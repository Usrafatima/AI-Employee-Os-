from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

MessageDirection = Literal["incoming", "outgoing"]
MessageChannel = Literal["email", "whatsapp", "chat"]
MessageStatus = Literal["draft", "pending_approval", "approved", "sent", "rejected"]
EmailStatus = Literal["pending", "sent", "failed"]
CreatedVia = Literal["text", "voice", "prompt"]
ReminderType = Literal["24h", "12h"]


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    direction: MessageDirection
    channel: MessageChannel
    content: str
    ai_generated: bool
    status: MessageStatus
    created_at: datetime


class IncomingMessageCreate(BaseModel):
    customer_id: int
    channel: MessageChannel
    content: str = Field(..., min_length=1)


class IncomingMessageResult(BaseModel):
    incoming: MessageResponse
    ai_draft: MessageResponse


class DraftUpdate(BaseModel):
    content: str = Field(..., min_length=1)


class EmailSendRequest(BaseModel):
    to_email: EmailStr
    subject: str | None = None
    body: str = Field(..., min_length=1)
    customer_id: int | None = None


class EmailLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: int | None = None
    to_email: str
    subject: str | None = None
    body: str
    status: EmailStatus
    error: str | None = None
    sent_at: datetime | None = None
    created_at: datetime


class WhatsAppSendRequest(BaseModel):
    customer_id: int
    content: str = Field(..., min_length=1)


class CalendarEventCreate(BaseModel):
    customer_id: int | None = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    event_time: datetime
    created_via: CreatedVia = "text"


class CalendarEventFromText(BaseModel):
    text: str = Field(..., min_length=1)
    customer_id: int | None = None
    created_via: CreatedVia = "text"


class CalendarEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int | None = None
    title: str
    description: str | None = None
    event_time: datetime
    created_via: CreatedVia
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    type: ReminderType
    sent: bool
    message: str | None = None
    created_at: datetime
