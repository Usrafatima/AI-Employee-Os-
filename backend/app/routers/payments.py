"""Payment endpoints.

Recording a payment automatically issues its receipt, so there is no separate
"create receipt" call. Payments are immutable once recorded — correcting one is
an accounting adjustment, which is outside the scope of this module.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser, get_current_user
from app.database.session import get_db
from app.schemas.finance import PaymentCreate, PaymentResponse, ReceiptResponse
from app.services.finance_service import FinanceService

router = APIRouter()


@router.get("/health")
def get_payments_status():
    return {"module": "Payments", "status": "active"}


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
def record_payment(
    payload: PaymentCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Record a confirmed payment and automatically issue its receipt."""
    return FinanceService.record_payment(db, payload.model_dump(), current_user.actor)


@router.get("", response_model=dict)
def list_payments(
    invoice_id: Optional[int] = Query(default=None),
    method: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.list_payments(
        db, invoice_id=invoice_id, method=method, page=page, page_size=page_size
    )


@router.get("/{payment_id}", response_model=PaymentResponse)
def get_payment(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.get_payment(db, payment_id)


@router.get("/{payment_id}/receipt", response_model=ReceiptResponse)
def get_payment_receipt(
    payment_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """The receipt issued for this payment."""
    FinanceService.get_payment(db, payment_id)
    return FinanceService.get_receipt_for_payment(db, payment_id)
