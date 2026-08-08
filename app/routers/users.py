from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.permissions import require_role

from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate

from app.services.user_service import UserService
from app.database.session import get_db


router = APIRouter()


# Current logged-in user profile
@router.get(
    "/me",
    response_model=UserResponse,
)
def get_me(
    current_user: User = Depends(get_current_user),
):
    return current_user



# Update own profile
@router.put(
    "/me",
    response_model=UserResponse,
)
def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):

    service = UserService(db)

    return service.update_user(
        current_user,
        user_update
    )



# Admin: Get all users
@router.get(
    "/",
    response_model=list[UserResponse],
)
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin")
    ),
):

    service = UserService(db)

    return service.get_all_users()



# Admin/User specific user fetch
@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    if (
        current_user.role != "admin"
        and current_user.id != user_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    service = UserService(db)

    user = service.get_user_by_id(user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user





# Admin delete user
@router.delete(
    "/{user_id}",
)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin")
    ),
):

    service = UserService(db)

    deleted = service.delete_user(user_id)


    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


    return {
        "message": "User deleted successfully"
    }