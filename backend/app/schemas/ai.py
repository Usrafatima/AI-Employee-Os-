from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: int | None = None


class ProposedAction(BaseModel):
    action: str
    arguments: dict[str, Any] = {}
    requires_approval: bool = True


class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    plan: list[str] = []
    proposed_action: ProposedAction | None = None
    created_at: datetime


class ActionConfirmRequest(BaseModel):
    conversation_id: int
    action: str = Field(..., min_length=1)
    arguments: dict[str, Any] = {}


class ActionConfirmResponse(BaseModel):
    success: bool
    tool: str
    message: str
    result: dict[str, Any] | None = None


class ConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=150)


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str | None = None
    created_at: datetime
    updated_at: datetime


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    created_at: datetime


class KnowledgeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    category: str | None = Field(default=None, max_length=100)


class KnowledgeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: str | None = None
    created_at: datetime
    updated_at: datetime


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    request: str
    response: str
    intent: str | None = None
    status: str
    created_at: datetime
