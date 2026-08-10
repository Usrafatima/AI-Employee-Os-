import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey, Integer
from app.core.types import GUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class MeetingStatus(str, enum.Enum):
    scheduled = "scheduled"
    recorded = "recorded"
    transcribing = "transcribing"
    summarized = "summarized"
    failed = "failed"


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    scheduled_at = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    status = Column(Enum(MeetingStatus), default=MeetingStatus.scheduled, nullable=False)

    audio_file_path = Column(String(500), nullable=True)
    transcript = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)          # bullet-point AI summary
    action_items = Column(Text, nullable=True)         # JSON string list of extracted action items
    deadlines_extracted = Column(Text, nullable=True)  # JSON string list of deadlines found

    created_by = Column(GUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    speakers = relationship("MeetingSpeaker", back_populates="meeting", cascade="all, delete-orphan")


class MeetingSpeaker(Base):
    """Speaker identification segments within a meeting transcript."""
    __tablename__ = "meeting_speakers"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    meeting_id = Column(GUID(), ForeignKey("meetings.id"), nullable=False)
    speaker_label = Column(String(100), nullable=False)  # e.g. "Speaker 1", or resolved name
    start_time_seconds = Column(Integer, nullable=True)
    end_time_seconds = Column(Integer, nullable=True)
    text = Column(Text, nullable=False)

    meeting = relationship("Meeting", back_populates="speakers")
