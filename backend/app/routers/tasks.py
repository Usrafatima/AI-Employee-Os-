import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.task import Task, TaskComment, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut, TaskCommentCreate, TaskCommentOut
from app.services import reminder_service

router = APIRouter(tags=["Task Manager"])


@router.post("", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("", response_model=List[TaskOut])
def list_tasks(
    company_id: uuid.UUID,
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    assigned_to: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Task).filter(Task.company_id == company_id)
    if status:
        query = query.filter(Task.status == status)
    if priority:
        query = query.filter(Task.priority == priority)
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    return query.order_by(Task.due_date.is_(None), Task.due_date.asc(), Task.created_at.desc()).all()


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(task_id: uuid.UUID, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")

    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(task, field, value)

    if updates.get("status") == TaskStatus.done:
        task.progress_percent = 100

    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: uuid.UUID, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    db.delete(task)
    db.commit()


@router.post("/{task_id}/comments", response_model=TaskCommentOut, status_code=201)
def add_comment(task_id: uuid.UUID, payload: TaskCommentCreate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(404, "Task not found")
    comment = TaskComment(task_id=task_id, **payload.model_dump())
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.get("/{task_id}/comments", response_model=List[TaskCommentOut])
def list_comments(task_id: uuid.UUID, db: Session = Depends(get_db)):
    return db.query(TaskComment).filter(TaskComment.task_id == task_id).order_by(TaskComment.created_at.asc()).all()


@router.get("/overdue/list", response_model=List[TaskOut])
def get_overdue_tasks(company_id: uuid.UUID, db: Session = Depends(get_db)):
    """Used by the AI reminder scheduler to find tasks needing a nudge."""
    from datetime import datetime
    return (
        db.query(Task)
        .filter(
            Task.company_id == company_id,
            Task.due_date < datetime.utcnow(),
            Task.status != TaskStatus.done,
        )
        .all()
    )


@router.post("/overdue/send-reminders")
def send_ai_reminders(company_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Triggers AI-drafted reminder messages for all overdue tasks.
    Intended to be called by a scheduler (cron/Celery beat); exposed here so it
    can also be triggered manually or from the Communication Hub / Executive Assistant.
    """
    return {"reminders": reminder_service.run_overdue_reminders(db, company_id)}