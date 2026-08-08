from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.dependencies import get_current_user
from app.core.permissions import require_role

from app.models.user import User
from app.schemas.approval import (
    ApprovalCreate,
    ApprovalResponse,
)
from app.services.approval_service import ApprovalService

router = APIRouter()


@router.post(
    "/",
    response_model=ApprovalResponse,
)
def create_approval(
    data: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApprovalService(db)

    return service.create_request(
        data,
        current_user.id,
    )


@router.get(
    "/",
    response_model=list[ApprovalResponse],
)
def get_all_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin")
    ),
):
    service = ApprovalService(db)

    return service.get_all()


@router.put(
    "/{approval_id}/approve",
    response_model=ApprovalResponse,
)
def approve_request(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin")
    ),
):
    service = ApprovalService(db)

    approval = service.approve(
        approval_id,
        current_user.id,
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found",
        )

    return approval


@router.put(
    "/{approval_id}/reject",
    response_model=ApprovalResponse,
)
def reject_request(
    approval_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role("admin")
    ),
):
    service = ApprovalService(db)

    approval = service.reject(
        approval_id,
        current_user.id,
    )

    if approval is None:
        raise HTTPException(
            status_code=404,
            detail="Approval request not found",
        )

    return approval