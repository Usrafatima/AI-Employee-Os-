from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.password import ForgotPasswordRequest
from app.services.password_reset_service import PasswordResetService

router = APIRouter(
    prefix="/password",
    tags=["Password Reset"]
)


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    service = PasswordResetService(db)

    token = service.forgot_password(request.email)

    if not token:
        return {
            "message": "User not found"
        }

    return {
        "message": "Password reset token generated",
        "token": token
    }