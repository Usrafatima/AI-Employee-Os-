"""
AI reminders for overdue/near-due tasks (Task Manager -> 'AI reminders' feature).
In production this runs on a schedule (e.g. Celery beat / cron). Here it's exposed
as a callable + an API endpoint so it can be triggered manually or wired to a scheduler.
"""
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus


def draft_reminder_message(task: Task) -> str:
    return (
        f"Reminder: task \"{task.title}\" (priority: {task.priority.value}) "
        f"was due on {task.due_date.strftime('%Y-%m-%d') if task.due_date else 'N/A'} "
        f"and is still marked '{task.status.value}'. Please update its status or progress."
    )


def run_overdue_reminders(db: Session, company_id) -> list[dict]:
    from datetime import datetime

    overdue_tasks = (
        db.query(Task)
        .filter(
            Task.company_id == company_id,
            Task.due_date < datetime.utcnow(),
            Task.status != TaskStatus.done,
        )
        .all()
    )

    results = []
    for task in overdue_tasks:
        message = draft_reminder_message(task)
        task.ai_reminder_sent += 1
        results.append({"task_id": str(task.id), "message": message})

    db.commit()
    return results
