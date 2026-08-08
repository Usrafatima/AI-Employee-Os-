from datetime import datetime

from pydantic import BaseModel


class ApprovalCreate(BaseModel):
    request_type: str
    reference_id: int
    message: str


class ApprovalResponse(BaseModel):
    id: int
    request_type: str
    reference_id: int
    message: str
    status: str
    requested_by: int
    approved_by: int | None
    created_at: datetime
    approved_at: datetime | None

    class Config:
        from_attributes = True