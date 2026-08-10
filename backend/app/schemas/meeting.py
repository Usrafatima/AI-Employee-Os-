import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.meeting import MeetingStatus


class MeetingCreate(BaseModel):
    company_id: uuid.UUID
    title: str
    scheduled_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    created_by: Optional[uuid.UUID] = None


class MeetingOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    scheduled_at: Optional[datetime]
    duration_minutes: Optional[int]
    status: MeetingStatus
    transcript: Optional[str]
    ai_summary: Optional[str]
    action_items: Optional[str]
    deadlines_extracted: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
