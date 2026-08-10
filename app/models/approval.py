from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class Approval(Base):
    __tablename__ = "approvals"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    request_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    reference_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
    )

    requested_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    approved_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )