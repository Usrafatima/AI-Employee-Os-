from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.workflow import (
    AuditLog,
    SystemNotification,
    Workflow,
    WorkflowRun,
    WorkflowRunStatus,
    WorkflowStatus,
)


class WorkflowService:
    # ------------------------------------------------------------------
    # Shared helpers (AuditLog / SystemNotification) — other modules can
    # call these two directly once this service is importable, e.g.
    # WorkflowService.log_action(db, actor="user:3", action="delete", ...)
    # ------------------------------------------------------------------

    @staticmethod
    def log_action(
        db: Session,
        *,
        actor: str,
        action: str,
        resource_type: str,
        resource_id: str | None = None,
        description: str | None = None,
        extra_data: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            actor=actor,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            description=description,
            extra_data=extra_data,
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def notify(
        db: Session,
        *,
        recipient: str,
        title: str,
        message: str,
        notification_type: str = "info",
        related_resource_type: str | None = None,
        related_resource_id: str | None = None,
    ) -> SystemNotification:
        notification = SystemNotification(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            related_resource_type=related_resource_type,
            related_resource_id=related_resource_id,
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    # ------------------------------------------------------------------
    # Workflow CRUD
    # ------------------------------------------------------------------

    @staticmethod
    def create_workflow(db: Session, payload: dict[str, Any], *, actor: str = "system") -> Workflow:
        workflow = Workflow(**payload, created_by=actor)
        db.add(workflow)
        db.commit()
        db.refresh(workflow)

        WorkflowService.log_action(
            db,
            actor=actor,
            action="create",
            resource_type="workflow",
            resource_id=str(workflow.id),
            description=f"Workflow '{workflow.name}' was created.",
        )
        return workflow

    @staticmethod
    def get_workflow(db: Session, workflow_id: int) -> Workflow:
        workflow = (
            db.query(Workflow)
            .filter(Workflow.id == workflow_id, Workflow.is_deleted.is_(False))
            .first()
        )
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found.")
        return workflow

    @staticmethod
    def list_workflows(
        db: Session,
        *,
        q: str | None = None,
        status_filter: str | None = None,
        trigger_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        query = db.query(Workflow).filter(Workflow.is_deleted.is_(False))

        if q:
            query = query.filter(or_(Workflow.name.ilike(f"%{q}%"), Workflow.description.ilike(f"%{q}%")))
        if status_filter:
            query = query.filter(Workflow.status == status_filter)
        if trigger_type:
            query = query.filter(Workflow.trigger_type == trigger_type)

        total = query.count()
        items = query.order_by(Workflow.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
            "items": items,
        }

    @staticmethod
    def update_workflow(db: Session, workflow_id: int, payload: dict[str, Any], *, actor: str = "system") -> Workflow:
        workflow = WorkflowService.get_workflow(db, workflow_id)
        previous_status = workflow.status

        for field, value in payload.items():
            if value is not None and hasattr(workflow, field):
                setattr(workflow, field, value)

        db.commit()
        db.refresh(workflow)

        WorkflowService.log_action(
            db,
            actor=actor,
            action="update",
            resource_type="workflow",
            resource_id=str(workflow.id),
            description=f"Workflow '{workflow.name}' was updated.",
        )

        if previous_status != workflow.status:
            WorkflowService.notify(
                db,
                recipient=actor,
                title="Workflow status changed",
                message=f"Workflow '{workflow.name}' changed from {previous_status} to {workflow.status}.",
                notification_type="info",
                related_resource_type="workflow",
                related_resource_id=str(workflow.id),
            )
        return workflow

    @staticmethod
    def delete_workflow(db: Session, workflow_id: int, *, actor: str = "system") -> dict[str, str]:
        workflow = WorkflowService.get_workflow(db, workflow_id)
        workflow.is_deleted = True
        db.commit()

        WorkflowService.log_action(
            db,
            actor=actor,
            action="delete",
            resource_type="workflow",
            resource_id=str(workflow.id),
            description=f"Workflow '{workflow.name}' was deleted.",
        )
        return {"message": "Workflow deleted successfully."}

    # ------------------------------------------------------------------
    # WorkflowRun (execution)
    # ------------------------------------------------------------------

    @staticmethod
    def run_workflow(db: Session, workflow_id: int, *, triggered_by: str = "system") -> WorkflowRun:
        workflow = WorkflowService.get_workflow(db, workflow_id)
        if workflow.status != WorkflowStatus.ACTIVE.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Workflow must be active to run (current status: {workflow.status}).",
            )

        run = WorkflowRun(
            workflow_id=workflow.id,
            status=WorkflowRunStatus.RUNNING.value,
            triggered_by=triggered_by,
            started_at=datetime.utcnow(),
        )
        db.add(run)
        db.commit()
        db.refresh(run)

        # NOTE: no execution engine wired up yet — this marks the run as
        # succeeded immediately so the rest of the module (history, audit,
        # notifications) is fully testable. Swap this block out once actual
        # step execution exists.
        run.status = WorkflowRunStatus.SUCCESS.value
        run.finished_at = datetime.utcnow()
        run.result_summary = f"Workflow '{workflow.name}' executed successfully."
        db.commit()
        db.refresh(run)

        WorkflowService.log_action(
            db,
            actor=triggered_by,
            action="run",
            resource_type="workflow_run",
            resource_id=str(run.id),
            description=f"Workflow '{workflow.name}' run #{run.id} finished with status {run.status}.",
        )
        WorkflowService.notify(
            db,
            recipient=triggered_by,
            title="Workflow run complete",
            message=f"Workflow '{workflow.name}' finished with status: {run.status}.",
            notification_type="success" if run.status == WorkflowRunStatus.SUCCESS.value else "error",
            related_resource_type="workflow_run",
            related_resource_id=str(run.id),
        )
        return run

    @staticmethod
    def get_run(db: Session, run_id: int) -> WorkflowRun:
        run = db.query(WorkflowRun).filter(WorkflowRun.id == run_id).first()
        if not run:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow run not found.")
        return run

    @staticmethod
    def list_runs(db: Session, *, workflow_id: int | None = None, status_filter: str | None = None) -> list[WorkflowRun]:
        query = db.query(WorkflowRun)
        if workflow_id is not None:
            query = query.filter(WorkflowRun.workflow_id == workflow_id)
        if status_filter:
            query = query.filter(WorkflowRun.status == status_filter)
        return query.order_by(WorkflowRun.created_at.desc()).all()

    # ------------------------------------------------------------------
    # Audit log & notification read endpoints
    # ------------------------------------------------------------------

    @staticmethod
    def list_audit_logs(
        db: Session,
        *,
        actor: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        query = db.query(AuditLog)
        if actor:
            query = query.filter(AuditLog.actor == actor)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if resource_id:
            query = query.filter(AuditLog.resource_id == resource_id)

        total = query.count()
        items = query.order_by(AuditLog.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
            "items": items,
        }

    @staticmethod
    def list_notifications(
        db: Session,
        *,
        recipient: str | None = None,
        is_read: bool | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict[str, Any]:
        query = db.query(SystemNotification)
        if recipient:
            query = query.filter(SystemNotification.recipient == recipient)
        if is_read is not None:
            query = query.filter(SystemNotification.is_read == is_read)

        total = query.count()
        items = query.order_by(SystemNotification.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
        }