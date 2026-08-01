from datetime import datetime, timedelta
import uuid

from sqlalchemy.orm import Session

from app.models.Refresh_token import RefreshToken


class TokenService:

    def __init__(self, db: Session):
        self.db = db


    def create_refresh_token(
        self,
        user_id: int
    ):

        token = str(uuid.uuid4())


        refresh_token = RefreshToken(
            token=token,
            user_id=user_id,
            expires_at=datetime.utcnow() + timedelta(days=7)
        )


        self.db.add(refresh_token)
        self.db.commit()
        self.db.refresh(refresh_token)


        return token