from datetime import datetime
from pydantic import BaseModel, EmailStr


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    phone: str | None
    role: str
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class UserUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None