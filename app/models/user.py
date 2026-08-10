from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from sqlalchemy import Boolean

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        default="employee",
    )

    company_id: Mapped[int | None] = mapped_column(
        ForeignKey("companies.id"),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    company = relationship("Company", back_populates="users")
    is_active: Mapped[bool] = mapped_column(
    Boolean,
    default=True,
)