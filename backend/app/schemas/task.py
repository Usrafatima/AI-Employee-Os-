import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.task import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    company_id: uuid.UUID
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.medium
    assigned_to: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    source: str = "manual"
    source_reference_id: Optional[uuid.UUID] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[uuid.UUID] = None
    due_date: Optional[datetime] = None
    progress_percent: Optional[int] = Field(default=None, ge=0, le=100)


class TaskCommentCreate(BaseModel):
    author_id: Optional[uuid.UUID] = None
    content: str


class TaskCommentOut(BaseModel):
    id: uuid.UUID
    author_id: Optional[uuid.UUID]
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class TaskOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    assigned_to: Optional[uuid.UUID]
    created_by: Optional[uuid.UUID]
    due_date: Optional[datetime]
    progress_percent: int
    ai_reminder_sent: int
    source: str
    source_reference_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
