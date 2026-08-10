"""Invoice endpoints.

Invoices can be created directly or generated from a quotation (see
``POST /quotations/{id}/invoice``). Payment status is never set by hand — it is
derived from recorded payments in ``FinanceService.record_payment``.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser, get_current_user, require_admin
from app.database.session import get_db
from app.schemas.finance import (
    InvoiceCreate,
    InvoiceResponse,
    InvoiceStatusUpdate,
    InvoiceUpdate,
    PaymentResponse,
    SendDocumentRequest,
    SendDocumentResponse,
)
from app.services.finance_delivery_service import FinanceDeliveryService
from app.services.finance_pdf_service import build_invoice_pdf
from app.services.finance_service import FinanceService

router = APIRouter()


@router.get("/health")
def get_invoices_status():
    return {"module": "Invoices", "status": "active"}


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    payload: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.create_invoice(db, payload.model_dump(), current_user.actor)


@router.get("", response_model=dict)
def list_invoices(
    q: Optional[str] = Query(default=None, description="Search by invoice number"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    customer_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.list_invoices(
        db, q=q, status_filter=status_filter, customer_id=customer_id, page=page, page_size=page_size
    )


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.get_invoice(db, invoice_id)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
def update_invoice(
    invoice_id: int,
    payload: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.update_invoice(
        db, invoice_id, payload.model_dump(exclude_unset=True), current_user.actor
    )


@router.patch("/{invoice_id}/status", response_model=InvoiceResponse)
def set_invoice_status(
    invoice_id: int,
    payload: InvoiceStatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.set_invoice_status(db, invoice_id, payload.status, current_user.actor)


@router.delete("/{invoice_id}", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    """Archive an invoice. Financial records are cancelled, never deleted."""
    return FinanceService.cancel_invoice(db, invoice_id, current_user.actor)


@router.get("/{invoice_id}/payments", response_model=dict)
def list_invoice_payments(
    invoice_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    FinanceService.get_invoice(db, invoice_id)
    return FinanceService.list_payments(db, invoice_id=invoice_id, page=page, page_size=page_size)


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    invoice = FinanceService.get_invoice(db, invoice_id)
    return Response(
        content=build_invoice_pdf(invoice),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{invoice.invoice_number}.pdf"'},
    )


@router.post("/{invoice_id}/send", response_model=SendDocumentResponse)
def send_invoice(
    invoice_id: int,
    payload: SendDocumentRequest | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Email the invoice to the customer with its PDF attached."""
    return FinanceDeliveryService.send_invoice(
        db, invoice_id, payload.model_dump(exclude_unset=True) if payload else {}, current_user.actor
    )
