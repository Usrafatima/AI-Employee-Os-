import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class KnowledgeArticleCreate(BaseModel):
    company_id: uuid.UUID
    title: str
    content: str
    tags: Optional[str] = None
    created_by: Optional[uuid.UUID] = None


class KnowledgeArticleOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    title: str
    content: str
    tags: Optional[str]
    source_type: str
    source_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeSearchRequest(BaseModel):
    query: str
    company_id: uuid.UUID
