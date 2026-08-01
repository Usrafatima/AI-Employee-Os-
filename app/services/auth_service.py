from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.auth import UserSignup
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

from app.services.Token_service import TokenService
from app.services.session_service import SessionService

from app.models.session import UserSession
from app.models.session import UserSession
# Add inside AuthService class

def logout(self, refresh_token: str):

    session = (
        self.db.query(UserSession)
        .filter(UserSession.refresh_token == refresh_token)
        .first()
    )

    if session is None:
        return False

    self.db.delete(session)
    self.db.commit()

    return True
class AuthService:

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str):
        return (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )

    def create_user(self, user: UserSignup):

        existing_user = self.get_user_by_email(user.email)

        if existing_user:
            raise ValueError("Email already registered.")

        db_user = User(
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            password_hash=hash_password(user.password),
        )

        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)

        return db_user

    def login(self, email: str, password: str):

        user = self.get_user_by_email(email)

        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Access Token
        access_token = create_access_token(user.id)

        # Refresh Token
        token_service = TokenService(self.db)
        refresh_token = token_service.create_refresh_token(user.id)

        # Save Session
        session_service = SessionService(self.db)
        session_service.create_session(
            user_id=user.id,
            refresh_token=refresh_token,
            device="Web Browser",
            ip_address="127.0.0.1",
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    from app.models.session import UserSession


class AuthService:

    # ... signup/login methods ...

    def logout(self, refresh_token: str):

        session = (
            self.db.query(UserSession)
            .filter(
                UserSession.refresh_token == refresh_token
            )
            .first()
        )

        if session is None:
            return False

        self.db.delete(session)
        self.db.commit()

        return True