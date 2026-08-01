from fastapi import Depends, HTTPException, status

from app.core.dependencies import get_current_user
from app.models.user import User



def require_role(role: str):

    def checker(
        current_user: User = Depends(get_current_user)
    ):

        if current_user.role != role:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return current_user

    return checker