from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.session import UserSession


class SessionService:

    def __init__(self, db: Session):
        self.db = db

    def create_session(
        self,
        user_id: int,
        refresh_token: str,
        device: str = None,
        ip_address: str = None,
    ):

        session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            device=device,
            ip_address=ip_address,
            expiry_time=datetime.utcnow() + timedelta(days=7),
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return session

    def get_user_sessions(
        self,
        user_id: int,
    ):

        return (
            self.db.query(UserSession)
            .filter(UserSession.user_id == user_id)
            .all()
        )

    def delete_session(
        self,
        session_id: int,
    ):

        session = (
            self.db.query(UserSession)
            .filter(UserSession.id == session_id)
            .first()
        )

        if not session:
            return None

        self.db.delete(session)
        self.db.commit()

        return {
            "message": "Session deleted successfully"
        }

    def delete_all_sessions(
        self,
        user_id: int,
    ):

        (
            self.db.query(UserSession)
            .filter(UserSession.user_id == user_id)
            .delete()
        )

        self.db.commit()

        return {
            "message": "All sessions deleted successfully"
        }