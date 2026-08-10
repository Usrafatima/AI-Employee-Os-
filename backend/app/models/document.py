import enum
import uuid
from datetime import datetime

from sqlalchemy import Column, String, Text, DateTime, Enum, ForeignKey
from app.core.types import GUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class DocumentType(str, enum.Enum):
    contract = "contract"
    invoice = "invoice"
    policy = "policy"
    report = "report"
    other = "other"


class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    processed = "processed"
    failed = "failed"


class Document(Base):
    __tablename__ = "documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), nullable=False, index=True)
    uploaded_by = Column(GUID(), nullable=True)

    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, jpg, png, docx...
    document_type = Column(Enum(DocumentType), default=DocumentType.other, nullable=False)
    status = Column(Enum(DocumentStatus), default=DocumentStatus.uploaded, nullable=False)

    extracted_text = Column(Text, nullable=True)      # OCR / text extraction result
    ai_summary = Column(Text, nullable=True)           # short AI-generated summary
    key_entities = Column(Text, nullable=True)         # JSON string: dates, amounts, parties etc.

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    qa_history = relationship("DocumentQA", back_populates="document", cascade="all, delete-orphan")


class DocumentQA(Base):
    """Stores AI Q&A interactions against a document, for the knowledge base + audit trail."""
    __tablename__ = "document_qa"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(GUID(), ForeignKey("documents.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    asked_by = Column(GUID(), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="qa_history")
