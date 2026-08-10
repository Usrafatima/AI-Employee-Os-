import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.document import DocumentType, DocumentStatus


class DocumentOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    uploaded_by: Optional[uuid.UUID]
    file_name: str
    file_type: str
    document_type: DocumentType
    status: DocumentStatus
    extracted_text: Optional[str]
    ai_summary: Optional[str]
    key_entities: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentQARequest(BaseModel):
    question: str
    asked_by: Optional[uuid.UUID] = None


class DocumentQAOut(BaseModel):
    id: uuid.UUID
    document_id: uuid.UUID
    question: str
    answer: str
    created_at: datetime

    class Config:
        from_attributes = True
