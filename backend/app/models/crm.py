from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class CustomerStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class LeadSource(str, Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    EMAIL = "email"
    PHONE = "phone"
    PARTNER = "partner"
    OTHER = "other"


class Customer(Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("email", name="uq_customer_email"),
        Index("ix_customer_status", "status"),
        Index("ix_customer_company", "company_name"),
        Index("ix_customer_name", "full_name"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(150), nullable=False, index=True)
    company_name: Mapped[str | None] = mapped_column(String(150), nullable=True, index=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[CustomerStatus] = mapped_column(String(20), nullable=False, default=CustomerStatus.ACTIVE.value, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    leads: Mapped[list["Lead"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    activity_logs: Mapped[list["ActivityLog"]] = relationship(back_populates="customer", cascade="all, delete-orphan")
    crm_update: Mapped["CRMUpdate | None"] = relationship(back_populates="customer", cascade="all, delete-orphan", uselist=False)


class Lead(Base):
    __tablename__ = "leads"
    __table_args__ = (
        Index("ix_lead_customer_status", "customer_id", "status"),
        Index("ix_lead_assigned_to", "assigned_to"),
        Index("ix_lead_source", "source"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    assigned_to: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    status: Mapped[LeadStatus] = mapped_column(String(30), nullable=False, default=LeadStatus.NEW.value, index=True)
    expected_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    probability: Mapped[int | None] = mapped_column(Integer, nullable=True)
    next_followup_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="leads")


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversation_customer_created", "customer_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    sender: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    ai_response: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    customer: Mapped[Customer] = relationship(back_populates="conversations")


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    __table_args__ = (
        Index("ix_activity_customer_created", "customer_id", "created_at"),
        Index("ix_activity_type", "activity_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False, index=True)

    customer: Mapped[Customer] = relationship(back_populates="activity_logs")


class CRMUpdate(Base):
    __tablename__ = "crm_updates"
    __table_args__ = (
        UniqueConstraint("customer_id", name="uq_customer_crm_update"),
        Index("ix_crm_update_customer", "customer_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    last_activity: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_contact_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_followup_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_updated_by: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    customer: Mapped[Customer] = relationship(back_populates="crm_update")
