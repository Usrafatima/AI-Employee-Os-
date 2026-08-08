from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from datetime import datetime

from app.database.session import Base


class RefreshToken(Base):

    __tablename__ = "refresh_tokens"


    id = Column(
        Integer,
        primary_key=True,
        index=True
    )


    token = Column(
        String,
        unique=True,
        nullable=False
    )


    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )


    expires_at = Column(
        DateTime,
        nullable=False
    )


    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )