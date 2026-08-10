"""Emailing finance documents to customers.

The Finance module does not implement any transport of its own. It renders the
PDF and hands the message to the Communication Hub
(:meth:`CommunicationService.send_direct_email`), which owns SMTP, the email
log and the customer conversation thread.

Sending is user-initiated: an operator (or the AI assistant acting on an
instruction) calls the send endpoint, and the document goes out immediately
with its PDF attached.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.finance import InvoiceStatus, QuotationStatus
from app.services.communication_service import CommunicationService
from app.services.finance_pdf_service import (
    build_invoice_pdf,
    build_quotation_pdf,
    build_receipt_pdf,
)
from app.services.finance_service import FinanceService

PDF_MIME = "application/pdf"


def _company() -> str:
    return settings.COMPANY_NAME or "AI Employee OS"


def _amount(value: Any) -> str:
    return f"{settings.CURRENCY_SYMBOL}{value:,.2f}"


def _resolve_recipient(customer: Any, override: str | None) -> str:
    recipient = (override or getattr(customer, "email", None) or "").strip()
    if not recipient:
        raise HTTPException(
            status_code=422,
            detail="No email address is available for this customer.",
        )
    return recipient


class FinanceDeliveryService:
    @staticmethod
    def send_quotation(
        db: Session, quotation_id: int, payload: dict[str, Any] | None = None, actor: str = "system"
    ) -> dict[str, Any]:
        payload = payload or {}
        quotation = FinanceService.get_quotation(db, quotation_id)

        if quotation.status == QuotationStatus.CANCELLED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A cancelled quotation cannot be sent.",
            )

        customer = quotation.customer
        recipient = _resolve_recipient(customer, payload.get("to_email"))
        subject = payload.get("subject") or f"Quotation {quotation.quotation_number} from {_company()}"
        body = payload.get("message") or (
            f"Dear {customer.full_name},\n\n"
            f"Please find attached quotation {quotation.quotation_number} for "
            f"{_amount(quotation.grand_total)}.\n"
            + (
                f"This quotation is valid until {quotation.valid_until:%d %b %Y}.\n"
                if quotation.valid_until
                else ""
            )
            + f"\nKind regards,\n{_company()}"
        )

        pdf = build_quotation_pdf(quotation)
        email_log = CommunicationService.send_direct_email(
            db,
            to_email=recipient,
            subject=subject,
            body=body,
            customer_id=quotation.customer_id,
            attachments=[(f"{quotation.quotation_number}.pdf", pdf, PDF_MIME)],
        )

        # Only advance a draft: a quotation the customer already accepted or
        # rejected must not be reset to "sent" by re-sending the PDF.
        if quotation.status == QuotationStatus.DRAFT.value:
            FinanceService.set_quotation_status(db, quotation.id, QuotationStatus.SENT.value, actor)

        return {
            "sent": True,
            "to_email": recipient,
            "subject": subject,
            "document_number": quotation.quotation_number,
            "email_log_id": email_log.id,
        }

    @staticmethod
    def send_invoice(
        db: Session, invoice_id: int, payload: dict[str, Any] | None = None, actor: str = "system"
    ) -> dict[str, Any]:
        payload = payload or {}
        invoice = FinanceService.get_invoice(db, invoice_id)

        if invoice.status == InvoiceStatus.CANCELLED.value:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A cancelled invoice cannot be sent.",
            )

        customer = invoice.customer
        recipient = _resolve_recipient(customer, payload.get("to_email"))
        subject = payload.get("subject") or f"Invoice {invoice.invoice_number} from {_company()}"
        body = payload.get("message") or (
            f"Dear {customer.full_name},\n\n"
            f"Please find attached invoice {invoice.invoice_number} for "
            f"{_amount(invoice.grand_total)}.\n"
            + (f"Payment is due by {invoice.due_date:%d %b %Y}.\n" if invoice.due_date else "")
            + (
                f"Outstanding balance: {_amount(invoice.balance_due)}.\n"
                if invoice.amount_paid
                else ""
            )
            + f"\nKind regards,\n{_company()}"
        )

        pdf = build_invoice_pdf(invoice)
        email_log = CommunicationService.send_direct_email(
            db,
            to_email=recipient,
            subject=subject,
            body=body,
            customer_id=invoice.customer_id,
            attachments=[(f"{invoice.invoice_number}.pdf", pdf, PDF_MIME)],
        )

        if invoice.status == InvoiceStatus.DRAFT.value:
            FinanceService.set_invoice_status(db, invoice.id, InvoiceStatus.SENT.value, actor)

        return {
            "sent": True,
            "to_email": recipient,
            "subject": subject,
            "document_number": invoice.invoice_number,
            "email_log_id": email_log.id,
        }

    @staticmethod
    def send_receipt(
        db: Session, receipt_id: int, payload: dict[str, Any] | None = None, actor: str = "system"
    ) -> dict[str, Any]:
        payload = payload or {}
        receipt = FinanceService.get_receipt(db, receipt_id)
        payment = FinanceService.get_payment(db, receipt.payment_id)
        invoice = FinanceService.get_invoice(db, payment.invoice_id)

        customer = invoice.customer
        recipient = _resolve_recipient(customer, payload.get("to_email"))
        subject = payload.get("subject") or f"Receipt {receipt.receipt_number} from {_company()}"
        body = payload.get("message") or (
            f"Dear {customer.full_name},\n\n"
            f"Thank you for your payment of {_amount(payment.amount)} against invoice "
            f"{invoice.invoice_number}.\n"
            f"Please find your receipt {receipt.receipt_number} attached.\n"
            + (
                "This invoice is now settled in full.\n"
                if receipt.balance_after <= 0
                else f"Remaining balance: {_amount(receipt.balance_after)}.\n"
            )
            + f"\nKind regards,\n{_company()}"
        )

        pdf = build_receipt_pdf(receipt, payment, invoice)
        email_log = CommunicationService.send_direct_email(
            db,
            to_email=recipient,
            subject=subject,
            body=body,
            customer_id=invoice.customer_id,
            attachments=[(f"{receipt.receipt_number}.pdf", pdf, PDF_MIME)],
        )

        return {
            "sent": True,
            "to_email": recipient,
            "subject": subject,
            "document_number": receipt.receipt_number,
            "email_log_id": email_log.id,
        }
