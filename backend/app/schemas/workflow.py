from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WorkflowStatus = Literal["active", "inactive", "draft"]
WorkflowTriggerType = Literal["manual", "scheduled", "event"]
WorkflowRunStatus = Literal["pending", "running", "success", "failed"]
NotificationType = Literal["info", "warning", "success", "error"]


# ---------------------------------------------------------------------------
# Workflow
# ---------------------------------------------------------------------------

class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    description: str | None = Field(default=None)
    trigger_type: WorkflowTriggerType = "manual"
    trigger_config: str | None = Field(default=None, description="JSON-encoded trigger details (cron expression, event name, etc.)")
    action_config: str | None = Field(default=None, description="JSON-encoded list of actions/steps to run")
    status: WorkflowStatus = "draft"


class WorkflowCreate(WorkflowBase):
    pass


class WorkflowUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    trigger_type: WorkflowTriggerType | None = None
    trigger_config: str | None = None
    action_config: str | None = None
    status: WorkflowStatus | None = None


class WorkflowResponse(WorkflowBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool = False
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# WorkflowRun
# ---------------------------------------------------------------------------

class WorkflowRunCreate(BaseModel):
    triggered_by: str | None = Field(default=None, max_length=120)


class WorkflowRunUpdate(BaseModel):
    status: WorkflowRunStatus | None = None
    result_summary: str | None = None
    error_message: str | None = None


class WorkflowRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    status: WorkflowRunStatus
    triggered_by: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result_summary: str | None = None
    error_message: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------

class AuditLogCreate(BaseModel):
    actor: str = Field(..., max_length=120)
    action: str = Field(..., max_length=100)
    resource_type: str = Field(..., max_length=50)
    resource_id: str | None = Field(default=None, max_length=50)
    description: str | None = None
    extra_data: str | None = Field(default=None, description="JSON-encoded extra context")


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor: str
    action: str
    resource_type: str
    resource_id: str | None = None
    description: str | None = None
    extra_data: str | None = None
    created_at: datetime


# ---------------------------------------------------------------------------
# SystemNotification
# (named SystemNotification*, not Notification*, to match the model rename —
# communication.py already has its own Notification/comm_notifications)
# ---------------------------------------------------------------------------

class SystemNotificationCreate(BaseModel):
    recipient: str = Field(..., max_length=120)
    title: str = Field(..., max_length=200)
    message: str
    notification_type: NotificationType = "info"
    related_resource_type: str | None = Field(default=None, max_length=50)
    related_resource_id: str | None = Field(default=None, max_length=50)


class SystemNotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recipient: str
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    related_resource_type: str | None = None
    related_resource_id: str | None = None
    created_at: datetime