import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Enum, Boolean, ForeignKey
from app.core.types import GUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class EventStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"


class EventSource(str, enum.Enum):
    manual = "manual"
    voice = "voice"
    text = "text"
    meeting_followup = "meeting_followup"  # created from Meeting Assistant


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(DateTime, nullable=False, index=True)
    end_time = Column(DateTime, nullable=True)
    location = Column(String(255), nullable=True)

    status = Column(Enum(EventStatus), default=EventStatus.scheduled, nullable=False)
    source = Column(Enum(EventSource), default=EventSource.manual, nullable=False)

    # Cross-module link: e.g. the meeting this event was scheduled for/from
    related_meeting_id = Column(GUID(), nullable=True)

    created_by = Column(GUID(), nullable=True)
    attendees = Column(Text, nullable=True)  # comma-separated user_ids or emails, kept simple

    reminder_24h_sent = Column(Boolean, default=False, nullable=False)
    reminder_12h_sent = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
