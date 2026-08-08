from datetime import datetime
from pydantic import BaseModel


class SessionResponse(BaseModel):
    id: int
    user_id: int
    device: str | None = None
    ip_address: str | None = None
    login_time: datetime
    expiry_time: datetime

    class Config:
        from_attributes = True