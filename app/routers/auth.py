from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.auth import UserSignup, UserLogin, Token
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService

router = APIRouter()
from app.schemas.auth import (
    UserSignup,
    UserLogin,
    Token,
    LogoutRequest,
)

@router.post("/signup", response_model=UserResponse)
def signup(
    user: UserSignup,
    db: Session = Depends(get_db)
):
    service = AuthService(db)

    try:
        return service.create_user(user)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):
    service = AuthService(db)

    token = service.login(
        user.email,
        user.password
    )

    if token is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    return token
@router.post("/logout")
def logout(
    request: LogoutRequest,
    db: Session = Depends(get_db),
):
    service = AuthService(db)

    success = service.logout(
        request.refresh_token
    )

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    return {
        "message": "Logout successful"
    }