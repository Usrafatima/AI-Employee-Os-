"""Receipt endpoints.

Receipts are generated automatically when a payment is recorded, so this
router is read-only plus PDF/delivery actions. Every receipt traces back to a
payment and, through it, to an invoice and customer.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser, get_current_user
from app.database.session import get_db
from app.schemas.finance import (
    ReceiptDetailResponse,
    SendDocumentRequest,
    SendDocumentResponse,
)
from app.services.finance_delivery_service import FinanceDeliveryService
from app.services.finance_pdf_service import build_receipt_pdf
from app.services.finance_service import FinanceService

router = APIRouter()


@router.get("/health")
def get_receipts_status():
    return {"module": "Receipts", "status": "active"}


@router.get("", response_model=dict)
def list_receipts(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.list_receipts(db, page=page, page_size=page_size)


@router.get("/{receipt_id}", response_model=ReceiptDetailResponse)
def get_receipt(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.get_receipt_detail(db, receipt_id)


@router.get("/{receipt_id}/pdf")
def download_receipt_pdf(
    receipt_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    receipt = FinanceService.get_receipt(db, receipt_id)
    payment = FinanceService.get_payment(db, receipt.payment_id)
    invoice = FinanceService.get_invoice(db, payment.invoice_id)
    return Response(
        content=build_receipt_pdf(receipt, payment, invoice),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{receipt.receipt_number}.pdf"'},
    )


@router.post("/{receipt_id}/send", response_model=SendDocumentResponse)
def send_receipt(
    receipt_id: int,
    payload: SendDocumentRequest | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Email the receipt to the customer with its PDF attached."""
    return FinanceDeliveryService.send_receipt(
        db, receipt_id, payload.model_dump(exclude_unset=True) if payload else {}, current_user.actor
    )
