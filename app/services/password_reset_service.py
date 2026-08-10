from datetime import datetime, timedelta
import secrets

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.core.security import hash_password



class PasswordResetService:


    def __init__(self, db: Session):
        self.db = db



    def forgot_password(
        self,
        email: str
    ):

        user = (
            self.db.query(User)
            .filter(User.email == email)
            .first()
        )


        if not user:
            return None



        token = secrets.token_urlsafe(32)



        reset_token = PasswordResetToken(

            token=token,

            user_id=user.id,

            expires_at=datetime.utcnow()
            +
            timedelta(hours=1)

        )


        self.db.add(reset_token)

        self.db.commit()

        self.db.refresh(reset_token)


        return token




    def reset_password(
        self,
        token: str,
        new_password: str
    ):


        reset_token = (
            self.db.query(
                PasswordResetToken
            )
            .filter(
                PasswordResetToken.token == token
            )
            .first()
        )


        if not reset_token:
            return False



        if reset_token.expires_at < datetime.utcnow():

            self.db.delete(reset_token)

            self.db.commit()

            return False




        user = (
            self.db.query(User)
            .filter(
                User.id == reset_token.user_id
            )
            .first()
        )


        if not user:
            return False



        user.password_hash = hash_password(
            new_password
        )


        self.db.delete(
            reset_token
        )


        self.db.commit()


        return True