from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.workflow import (
    AuditLogCreate,
    AuditLogResponse,
    SystemNotificationCreate,
    SystemNotificationResponse,
    WorkflowCreate,
    WorkflowResponse,
    WorkflowRunCreate,
    WorkflowRunResponse,
    WorkflowUpdate,
)
from app.services.workflow_service import WorkflowService

router = APIRouter()


@router.get("/")
def health_check() -> dict[str, str]:
    return {"status": "ok", "module": "workflow-automation"}


# ---------------------------------------------------------------------------
# Workflow CRUD
# ---------------------------------------------------------------------------

@router.post("/", response_model=WorkflowResponse, status_code=201)
def create_workflow(
    payload: WorkflowCreate,
    actor: str = Query(default="system"),
    db: Session = Depends(get_db),
) -> WorkflowResponse:
    workflow = WorkflowService.create_workflow(db, payload.model_dump(), actor=actor)
    return workflow


@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)) -> WorkflowResponse:
    return WorkflowService.get_workflow(db, workflow_id)


@router.get("")
def list_workflows(
    q: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    trigger_type: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    result = WorkflowService.list_workflows(
        db,
        q=q,
        status_filter=status_filter,
        trigger_type=trigger_type,
        page=page,
        page_size=page_size,
    )
    result["items"] = [WorkflowResponse.model_validate(item) for item in result["items"]]
    return result


@router.patch("/{workflow_id}", response_model=WorkflowResponse)
def update_workflow(
    workflow_id: int,
    payload: WorkflowUpdate,
    actor: str = Query(default="system"),
    db: Session = Depends(get_db),
) -> WorkflowResponse:
    return WorkflowService.update_workflow(
        db, workflow_id, payload.model_dump(exclude_unset=True), actor=actor
    )


@router.delete("/{workflow_id}")
def delete_workflow(
    workflow_id: int,
    actor: str = Query(default="system"),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    return WorkflowService.delete_workflow(db, workflow_id, actor=actor)


# ---------------------------------------------------------------------------
# WorkflowRun (execution)
# ---------------------------------------------------------------------------

@router.post("/{workflow_id}/run", response_model=WorkflowRunResponse, status_code=201)
def run_workflow(
    workflow_id: int,
    payload: WorkflowRunCreate | None = None,
    db: Session = Depends(get_db),
) -> WorkflowRunResponse:
    triggered_by = payload.triggered_by if payload and payload.triggered_by else "system"
    return WorkflowService.run_workflow(db, workflow_id, triggered_by=triggered_by)


@router.get("/{workflow_id}/runs", response_model=list[WorkflowRunResponse])
def list_runs_for_workflow(
    workflow_id: int,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[WorkflowRunResponse]:
    return WorkflowService.list_runs(db, workflow_id=workflow_id, status_filter=status_filter)


@router.get("/runs/all", response_model=list[WorkflowRunResponse])
def list_all_runs(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[WorkflowRunResponse]:
    return WorkflowService.list_runs(db, workflow_id=None, status_filter=status_filter)


@router.get("/runs/{run_id}", response_model=WorkflowRunResponse)
def get_run(run_id: int, db: Session = Depends(get_db)) -> WorkflowRunResponse:
    return WorkflowService.get_run(db, run_id)


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

@router.get("/audit-logs/", response_model=dict)
def list_audit_logs(
    actor: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    result = WorkflowService.list_audit_logs(
        db,
        actor=actor,
        resource_type=resource_type,
        resource_id=resource_id,
        page=page,
        page_size=page_size,
    )
    result["items"] = [AuditLogResponse.model_validate(item) for item in result["items"]]
    return result


@router.post("/audit-logs/", response_model=AuditLogResponse, status_code=201)
def create_audit_log(payload: AuditLogCreate, db: Session = Depends(get_db)) -> AuditLogResponse:
    return WorkflowService.log_action(
        db,
        actor=payload.actor,
        action=payload.action,
        resource_type=payload.resource_type,
        resource_id=payload.resource_id,
        description=payload.description,
        extra_data=payload.extra_data,
    )


# ---------------------------------------------------------------------------
# System Notifications
# ---------------------------------------------------------------------------

@router.get("/notifications/", response_model=dict)
def list_notifications(
    recipient: str | None = Query(default=None),
    is_read: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> dict:
    result = WorkflowService.list_notifications(
        db,
        recipient=recipient,
        is_read=is_read,
        page=page,
        page_size=page_size,
    )
    result["items"] = [SystemNotificationResponse.model_validate(item) for item in result["items"]]
    return result


@router.post("/notifications/", response_model=SystemNotificationResponse, status_code=201)
def create_notification(payload: SystemNotificationCreate, db: Session = Depends(get_db)) -> SystemNotificationResponse:
    return WorkflowService.notify(
        db,
        recipient=payload.recipient,
        title=payload.title,
        message=payload.message,
        notification_type=payload.notification_type,
        related_resource_type=payload.related_resource_type,
        related_resource_id=payload.related_resource_id,
    )