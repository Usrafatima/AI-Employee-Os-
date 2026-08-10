from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class MessageDirection(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"


class MessageChannel(str, Enum):
    EMAIL = "email"
    WHATSAPP = "whatsapp"
    CHAT = "chat"


class MessageStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    SENT = "sent"
    REJECTED = "rejected"


class EmailStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class ReminderType(str, Enum):
    H24 = "24h"
    H12 = "12h"


class Message(Base):
    """A single message in a customer conversation (email / whatsapp / chat).

    AI-generated outgoing replies are created with status=pending_approval and
    must be approved by an admin (see CommunicationService.approve_message)
    before they are actually sent.
    """

    __tablename__ = "comm_messages"
    __table_args__ = (
        Index("ix_comm_message_customer_created", "customer_id", "created_at"),
        Index("ix_comm_message_status", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    ai_generated: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default=MessageStatus.SENT.value, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class EmailLog(Base):
    """Record of every email send attempt (approved replies, quotations, invoices, follow-ups)."""

    __tablename__ = "comm_email_log"
    __table_args__ = (
        Index("ix_comm_email_log_created", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("comm_messages.id", ondelete="SET NULL"), nullable=True, index=True)
    to_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=EmailStatus.PENDING.value, index=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)


class CalendarEvent(Base):
    """Scheduled meeting/event, creatable from structured fields or natural-language text
    (typed prompt, or a transcript from voice input)."""

    __tablename__ = "comm_calendar_events"
    __table_args__ = (
        Index("ix_comm_event_time", "event_time"),
        Index("ix_comm_event_customer", "customer_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id", ondelete="SET NULL"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    created_via: Mapped[str] = mapped_column(String(20), nullable=False, default="text")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class Notification(Base):
    """24h / 12h reminder generated for an upcoming calendar event."""

    __tablename__ = "comm_notifications"
    __table_args__ = (
        Index("ix_comm_notification_event_type", "event_id", "type", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("comm_calendar_events.id", ondelete="CASCADE"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    sent: Mapped[bool] = mapped_column(Integer, nullable=False, default=0)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
