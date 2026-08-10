import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.calendar_event import EventStatus, EventSource


class CalendarEventCreate(BaseModel):
    company_id: uuid.UUID
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    source: EventSource = EventSource.manual
    related_meeting_id: Optional[uuid.UUID] = None
    created_by: Optional[uuid.UUID] = None
    attendees: Optional[str] = None


class CalendarEventFromText(BaseModel):
    """Lets the AI Executive Assistant / voice pipeline hand off a raw instruction,
    e.g. 'Schedule a meeting with John Friday at 3 PM', and get back a structured event."""
    company_id: uuid.UUID
    instruction: str
    created_by: Optional[uuid.UUID] = None


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    location: Optional[str] = None
    status: Optional[EventStatus] = None
    attendees: Optional[str] = None


class CalendarEventOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    description: Optional[str]
    start_time: datetime
    end_time: Optional[datetime]
    location: Optional[str]
    status: EventStatus
    source: EventSource
    related_meeting_id: Optional[uuid.UUID]
    attendees: Optional[str]
    reminder_24h_sent: bool
    reminder_12h_sent: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
