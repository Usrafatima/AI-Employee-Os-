from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.password import (
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.services.password_reset_service import PasswordResetService


router = APIRouter(
    prefix="/password",
    tags=["Password Reset"],
)


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    service = PasswordResetService(db)

    token = service.forgot_password(
        request.email
    )

    if not token:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return {
        "message": "Password reset token generated",
        "token": token
    }



@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    service = PasswordResetService(db)

    result = service.reset_password(
        request.token,
        request.new_password
    )

    if not result:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired token"
        )


    return {
        "message": "Password reset successful"
    }