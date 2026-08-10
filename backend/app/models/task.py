import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Integer
from app.core.types import GUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), nullable=False, index=True)  # comes from Auth module
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.todo, nullable=False)
    priority = Column(Enum(TaskPriority), default=TaskPriority.medium, nullable=False)
    assigned_to = Column(GUID(), nullable=True, index=True)  # user_id from Auth module
    created_by = Column(GUID(), nullable=True, index=True)
    due_date = Column(DateTime, nullable=True)
    progress_percent = Column(Integer, default=0, nullable=False)
    ai_reminder_sent = Column(Integer, default=0, nullable=False)  # count of AI reminders sent
    source = Column(String(50), default="manual", nullable=False)  # manual / meeting / ai_assistant
    source_reference_id = Column(GUID(), nullable=True)  # e.g. meeting_id if auto-created

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    comments = relationship("TaskComment", back_populates="task", cascade="all, delete-orphan")


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    task_id = Column(GUID(), ForeignKey("tasks.id"), nullable=False)
    author_id = Column(GUID(), nullable=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    task = relationship("Task", back_populates="comments")
