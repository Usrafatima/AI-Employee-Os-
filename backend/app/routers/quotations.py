"""Quotation endpoints.

Routers carry HTTP semantics only; all business rules live in
``FinanceService``. Every endpoint requires an authenticated caller, and
archival (cancel) is restricted to administrators.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import CurrentUser, get_current_user, require_admin
from app.database.session import get_db
from app.schemas.finance import (
    InvoiceFromQuotation,
    InvoiceResponse,
    QuotationCreate,
    QuotationResponse,
    QuotationStatusUpdate,
    QuotationUpdate,
    SendDocumentRequest,
    SendDocumentResponse,
)
from app.services.finance_delivery_service import FinanceDeliveryService
from app.services.finance_pdf_service import build_quotation_pdf
from app.services.finance_service import FinanceService

router = APIRouter()


@router.get("/health")
def get_quotations_status():
    return {"module": "Quotations", "status": "active"}


@router.post("", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
def create_quotation(
    payload: QuotationCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.create_quotation(db, payload.model_dump(), current_user.actor)


@router.get("", response_model=dict)
def list_quotations(
    q: Optional[str] = Query(default=None, description="Search by quotation number"),
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status"),
    customer_id: Optional[int] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.list_quotations(
        db, q=q, status_filter=status_filter, customer_id=customer_id, page=page, page_size=page_size
    )


@router.get("/{quotation_id}", response_model=QuotationResponse)
def get_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.get_quotation(db, quotation_id)


@router.patch("/{quotation_id}", response_model=QuotationResponse)
def update_quotation(
    quotation_id: int,
    payload: QuotationUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.update_quotation(
        db, quotation_id, payload.model_dump(exclude_unset=True), current_user.actor
    )


@router.patch("/{quotation_id}/status", response_model=QuotationResponse)
def set_quotation_status(
    quotation_id: int,
    payload: QuotationStatusUpdate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.set_quotation_status(db, quotation_id, payload.status, current_user.actor)


@router.delete("/{quotation_id}", response_model=QuotationResponse)
def cancel_quotation(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(require_admin),
):
    """Archive a quotation. Financial records are cancelled, never deleted."""
    return FinanceService.cancel_quotation(db, quotation_id, current_user.actor)


@router.post(
    "/{quotation_id}/invoice", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED
)
def convert_quotation_to_invoice(
    quotation_id: int,
    payload: InvoiceFromQuotation | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    return FinanceService.create_invoice_from_quotation(
        db, quotation_id, payload.model_dump(exclude_unset=True) if payload else {}, current_user.actor
    )


@router.get("/{quotation_id}/pdf")
def download_quotation_pdf(
    quotation_id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    quotation = FinanceService.get_quotation(db, quotation_id)
    return Response(
        content=build_quotation_pdf(quotation),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{quotation.quotation_number}.pdf"'},
    )


@router.post("/{quotation_id}/send", response_model=SendDocumentResponse)
def send_quotation(
    quotation_id: int,
    payload: SendDocumentRequest | None = None,
    db: Session = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_user),
):
    """Email the quotation to the customer with its PDF attached."""
    return FinanceDeliveryService.send_quotation(
        db, quotation_id, payload.model_dump(exclude_unset=True) if payload else {}, current_user.actor
    )
