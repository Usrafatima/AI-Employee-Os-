import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime
from app.core.types import GUID

from app.core.database import Base


class KnowledgeArticle(Base):
    """
    Unified knowledge base entry. Populated either manually, or automatically
    from processed Documents / Meeting summaries, so AI Q&A has one place to search.
    """
    __tablename__ = "knowledge_articles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), nullable=False, index=True)

    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(String(500), nullable=True)  # comma separated
    source_type = Column(String(50), default="manual", nullable=False)  # manual/document/meeting
    source_id = Column(GUID(), nullable=True)

    created_by = Column(GUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
