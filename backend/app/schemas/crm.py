from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

CustomerStatus = Literal["active", "inactive"]
LeadStatus = Literal["new", "contacted", "qualified", "proposal_sent", "negotiation", "won", "lost"]
ConversationSender = Literal["customer", "agent", "ai"]


class CustomerBase(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=150)
    company_name: str | None = Field(default=None, max_length=150)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None)
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    notes: str | None = Field(default=None)
    status: CustomerStatus = "active"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        digits = "".join(ch for ch in value if ch.isdigit() or ch in "+()- ")
        if len(digits.strip()) < 7:
            raise ValueError("Phone number must be valid.")
        return value


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    company_name: str | None = Field(default=None, max_length=150)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=50)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    country: str | None = Field(default=None, max_length=100)
    industry: str | None = Field(default=None, max_length=100)
    notes: str | None = None
    status: CustomerStatus | None = None

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        digits = "".join(ch for ch in value if ch.isdigit() or ch in "+()- ")
        if len(digits.strip()) < 7:
            raise ValueError("Phone number must be valid.")
        return value


class CustomerResponse(CustomerBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_deleted: bool = False
    created_at: datetime
    updated_at: datetime


class LeadBase(BaseModel):
    customer_id: int
    title: str = Field(..., min_length=2, max_length=200)
    source: str = Field(..., min_length=2, max_length=50)
    assigned_to: str | None = Field(default=None, max_length=120)
    status: LeadStatus = "new"
    expected_value: float | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    next_followup_date: datetime | None = None
    notes: str | None = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    customer_id: int | None = None
    title: str | None = Field(default=None, min_length=2, max_length=200)
    source: str | None = Field(default=None, min_length=2, max_length=50)
    assigned_to: str | None = Field(default=None, max_length=120)
    status: LeadStatus | None = None
    expected_value: float | None = Field(default=None, ge=0)
    probability: int | None = Field(default=None, ge=0, le=100)
    next_followup_date: datetime | None = None
    notes: str | None = None


class LeadResponse(LeadBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    customer_id: int
    sender: ConversationSender = "customer"
    message: str = Field(..., min_length=1)
    ai_response: str | None = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    sender: str
    message: str
    ai_response: str | None = None
    created_at: datetime


class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    activity_type: str
    description: str
    created_by: str | None = None
    created_at: datetime


class CRMUpdateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_id: int
    last_activity: str | None = None
    last_contact_date: datetime | None = None
    next_followup_date: datetime | None = None
    last_updated_by: str | None = None
    created_at: datetime
    updated_at: datetime


class CustomerProfileResponse(BaseModel):
    customer: CustomerResponse
    leads: list[LeadResponse] = []
    conversations: list[ConversationResponse] = []
    activity_timeline: list[ActivityLogResponse] = []
    crm_update: CRMUpdateResponse | None = None


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[dict]


class SearchQuery(BaseModel):
    q: str | None = Field(default=None, max_length=200)
