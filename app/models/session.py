from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.session import Base


class UserSession(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    refresh_token: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    device: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    login_time: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    expiry_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )