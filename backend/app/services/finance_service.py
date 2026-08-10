"""Business logic for the Finance module.

Follows the service conventions already used by ``CRMService``: static methods,
``HTTPException`` for transport-visible failures, and paginated collections
returned as ``{total, page, page_size, total_pages, items}``.

Two rules hold everywhere in this file:

1. **Amounts are recomputed server-side.** Whatever totals a client sends are
   ignored; every persisted amount comes from ``finance_calculator`` applied to
   the line items. The frontend may preview totals, but it can never set them.
2. **Customers come from the CRM.** ``CRMService.get_customer`` is the only way
   a customer is resolved, so soft-deleted and non-existent customers are
   rejected consistently with the rest of the product.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable, Sequence

from fastapi import HTTPException, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.models.crm import ActivityLog
from app.models.finance import (
    INVOICE_LOCKED_STATUSES,
    QUOTATION_LOCKED_STATUSES,
    DiscountType,
    Invoice,
    InvoiceItem,
    InvoiceStatus,
    Payment,
    PaymentMethod,
    Quotation,
    QuotationItem,
    QuotationStatus,
    Receipt,
)
from app.services.crm_service import CRMService
from app.services.finance_calculator import (
    CalculationError,
    compute_totals,
    money,
)

#: Starlette renamed HTTP_422_UNPROCESSABLE_ENTITY to ..._CONTENT and deprecated
#: the old name. Use the numeric code so the module works on both versions.
HTTP_422_UNPROCESSABLE = 422

QUOTATION_PREFIX = "QT"
INVOICE_PREFIX = "INV"
RECEIPT_PREFIX = "RCT"

#: How many times to retry number allocation when two requests race for the
#: same sequence value. The unique constraint is the real guard; this just
#: turns a rare collision into a retry instead of a 500.
_NUMBER_ALLOCATION_ATTEMPTS = 5


class FinanceService:
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fail(message: str, code: int = HTTP_422_UNPROCESSABLE) -> None:
        raise HTTPException(status_code=code, detail=message)

    @staticmethod
    def _next_number(db: Session, model: type, prefix: str) -> tuple[str, int, int]:
        """Allocate the next ``PREFIX-YYYY-NNN`` document number for this year."""
        year = date.today().year
        last = (
            db.query(func.max(model.sequence_number))
            .filter(model.sequence_year == year)
            .scalar()
        )
        sequence = int(last or 0) + 1
        return f"{prefix}-{year}-{sequence:03d}", year, sequence

    @staticmethod
    def _compute(items: Iterable[Any], discount_type: str, discount_value: Any, tax_rate: Any):
        """Run the calculator, translating rule violations into HTTP 422."""
        try:
            return compute_totals(
                items,
                discount_type=discount_type,
                discount_value=discount_value,
                tax_rate=tax_rate,
            )
        except CalculationError as exc:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE, detail=str(exc)
            ) from None

    @staticmethod
    def _log_activity(db: Session, customer_id: int, activity_type: str, description: str, actor: str) -> None:
        """Append to the shared CRM customer timeline.

        Added to the session without committing so it shares the caller's
        transaction — a failed finance write must not leave an orphan activity.
        """
        db.add(
            ActivityLog(
                customer_id=customer_id,
                activity_type=activity_type,
                description=description,
                created_by=actor,
            )
        )

    @staticmethod
    def _customer_summary(customer: Any) -> dict[str, Any] | None:
        if customer is None:
            return None
        return {
            "id": customer.id,
            "full_name": customer.full_name,
            "company_name": customer.company_name,
            "email": customer.email,
            "phone": customer.phone,
            "address": customer.address,
            "city": customer.city,
            "country": customer.country,
        }

    @staticmethod
    def _serialize_items(items: Sequence[Any]) -> list[dict[str, Any]]:
        return [
            {
                "id": item.id,
                "position": item.position,
                "description": item.description,
                "quantity": Decimal(item.quantity),
                "unit_price": Decimal(item.unit_price),
                "line_total": Decimal(item.line_total),
            }
            for item in items
        ]

    @staticmethod
    def serialize_quotation(quotation: Quotation, *, include_items: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": quotation.id,
            "quotation_number": quotation.quotation_number,
            "customer_id": quotation.customer_id,
            "customer": FinanceService._customer_summary(quotation.customer),
            "status": quotation.status,
            "issue_date": quotation.issue_date,
            "valid_until": quotation.valid_until,
            "currency": quotation.currency,
            "discount_type": quotation.discount_type,
            "discount_value": Decimal(quotation.discount_value),
            "tax_rate": Decimal(quotation.tax_rate),
            "subtotal": Decimal(quotation.subtotal),
            "discount_amount": Decimal(quotation.discount_amount),
            "tax_amount": Decimal(quotation.tax_amount),
            "grand_total": Decimal(quotation.grand_total),
            "notes": quotation.notes,
            "terms": quotation.terms,
            "sent_at": quotation.sent_at,
            "created_by": quotation.created_by,
            "created_at": quotation.created_at,
            "updated_at": quotation.updated_at,
            "items": [],
        }
        if include_items:
            data["items"] = FinanceService._serialize_items(quotation.items)
        return data

    @staticmethod
    def serialize_invoice(invoice: Invoice, *, include_items: bool = True) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "customer_id": invoice.customer_id,
            "customer": FinanceService._customer_summary(invoice.customer),
            "quotation_id": invoice.quotation_id,
            "status": invoice.status,
            "issue_date": invoice.issue_date,
            "due_date": invoice.due_date,
            "currency": invoice.currency,
            "discount_type": invoice.discount_type,
            "discount_value": Decimal(invoice.discount_value),
            "tax_rate": Decimal(invoice.tax_rate),
            "subtotal": Decimal(invoice.subtotal),
            "discount_amount": Decimal(invoice.discount_amount),
            "tax_amount": Decimal(invoice.tax_amount),
            "grand_total": Decimal(invoice.grand_total),
            "amount_paid": Decimal(invoice.amount_paid),
            "balance_due": invoice.balance_due,
            "notes": invoice.notes,
            "terms": invoice.terms,
            "sent_at": invoice.sent_at,
            "created_by": invoice.created_by,
            "created_at": invoice.created_at,
            "updated_at": invoice.updated_at,
            "items": [],
        }
        if include_items:
            data["items"] = FinanceService._serialize_items(invoice.items)
        return data

    @staticmethod
    def serialize_payment(payment: Payment) -> dict[str, Any]:
        receipt = payment.receipt
        return {
            "id": payment.id,
            "invoice_id": payment.invoice_id,
            "amount": Decimal(payment.amount),
            "method": payment.method,
            "reference": payment.reference,
            "payment_date": payment.payment_date,
            "notes": payment.notes,
            "recorded_by": payment.recorded_by,
            "created_at": payment.created_at,
            "receipt": FinanceService.serialize_receipt(receipt) if receipt else None,
        }

    @staticmethod
    def serialize_receipt(receipt: Receipt) -> dict[str, Any]:
        return {
            "id": receipt.id,
            "receipt_number": receipt.receipt_number,
            "payment_id": receipt.payment_id,
            "balance_after": Decimal(receipt.balance_after),
            "issued_at": receipt.issued_at,
            "created_at": receipt.created_at,
        }

    @staticmethod
    def _paginate(query, page: int, page_size: int, serializer) -> dict[str, Any]:
        total = query.count()
        rows = query.offset((page - 1) * page_size).limit(page_size).all()
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size if total else 0,
            "items": [serializer(row) for row in rows],
        }

    # ------------------------------------------------------------------
    # Quotations
    # ------------------------------------------------------------------

    @staticmethod
    def create_quotation(db: Session, payload: dict[str, Any], actor: str = "system") -> Quotation:
        customer = CRMService.get_customer(db, payload["customer_id"])
        items = payload.get("items") or []
        totals = FinanceService._compute(
            items,
            payload.get("discount_type") or DiscountType.PERCENTAGE.value,
            payload.get("discount_value") or 0,
            payload.get("tax_rate") or 0,
        )

        for attempt in range(_NUMBER_ALLOCATION_ATTEMPTS):
            number, year, sequence = FinanceService._next_number(db, Quotation, QUOTATION_PREFIX)
            quotation = Quotation(
                quotation_number=number,
                sequence_year=year,
                sequence_number=sequence,
                customer_id=customer.id,
                status=QuotationStatus.DRAFT.value,
                issue_date=payload.get("issue_date") or date.today(),
                valid_until=payload.get("valid_until"),
                currency=settings.CURRENCY_CODE,
                discount_type=payload.get("discount_type") or DiscountType.PERCENTAGE.value,
                discount_value=money(payload.get("discount_value") or 0),
                tax_rate=Decimal(str(payload.get("tax_rate") or 0)),
                subtotal=totals.subtotal,
                discount_amount=totals.discount_amount,
                tax_amount=totals.tax_amount,
                grand_total=totals.grand_total,
                notes=payload.get("notes"),
                terms=payload.get("terms") or (settings.DOCUMENT_TERMS or None),
                created_by=actor,
            )
            for position, (raw, line) in enumerate(zip(items, totals.lines)):
                description = raw["description"] if isinstance(raw, dict) else raw.description
                quotation.items.append(
                    QuotationItem(
                        position=position,
                        description=description,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        line_total=line.line_total,
                    )
                )

            db.add(quotation)
            FinanceService._log_activity(
                db,
                customer.id,
                "Quotation Created",
                f"Quotation {number} created for {settings.CURRENCY_SYMBOL}{totals.grand_total:,.2f}.",
                actor,
            )
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                if attempt == _NUMBER_ALLOCATION_ATTEMPTS - 1:
                    FinanceService._fail(
                        "Could not allocate a unique quotation number. Please retry.",
                        status.HTTP_409_CONFLICT,
                    )
                continue
            db.refresh(quotation)
            return quotation

        raise AssertionError("unreachable")  # pragma: no cover

    @staticmethod
    def list_quotations(
        db: Session,
        *,
        q: str | None = None,
        status_filter: str | None = None,
        customer_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        query = db.query(Quotation).options(selectinload(Quotation.items))
        if customer_id is not None:
            query = query.filter(Quotation.customer_id == customer_id)
        if status_filter:
            query = query.filter(Quotation.status == status_filter)
        if q:
            query = query.filter(Quotation.quotation_number.ilike(f"%{q}%"))
        query = query.order_by(Quotation.created_at.desc(), Quotation.id.desc())
        return FinanceService._paginate(
            query, page, page_size, lambda row: FinanceService.serialize_quotation(row, include_items=False)
        )

    @staticmethod
    def get_quotation(db: Session, quotation_id: int) -> Quotation:
        quotation = (
            db.query(Quotation)
            .options(selectinload(Quotation.items))
            .filter(Quotation.id == quotation_id)
            .first()
        )
        if quotation is None:
            FinanceService._fail("Quotation not found.", status.HTTP_404_NOT_FOUND)
        return quotation

    @staticmethod
    def update_quotation(db: Session, quotation_id: int, payload: dict[str, Any], actor: str = "system") -> Quotation:
        quotation = FinanceService.get_quotation(db, quotation_id)
        if quotation.status in QUOTATION_LOCKED_STATUSES:
            FinanceService._fail(
                f"A {quotation.status} quotation cannot be edited.", status.HTTP_409_CONFLICT
            )

        if payload.get("customer_id") and payload["customer_id"] != quotation.customer_id:
            quotation.customer_id = CRMService.get_customer(db, payload["customer_id"]).id

        for field in ("issue_date", "valid_until", "notes", "terms"):
            if field in payload:
                setattr(quotation, field, payload[field])

        discount_type = payload.get("discount_type", quotation.discount_type)
        discount_value = payload.get("discount_value", quotation.discount_value)
        tax_rate = payload.get("tax_rate", quotation.tax_rate)

        items = payload.get("items")
        source_items = items if items is not None else quotation.items
        totals = FinanceService._compute(source_items, discount_type, discount_value, tax_rate)

        if items is not None:
            quotation.items.clear()
            db.flush()
            for position, (raw, line) in enumerate(zip(items, totals.lines)):
                description = raw["description"] if isinstance(raw, dict) else raw.description
                quotation.items.append(
                    QuotationItem(
                        position=position,
                        description=description,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        line_total=line.line_total,
                    )
                )

        quotation.discount_type = discount_type
        quotation.discount_value = money(discount_value)
        quotation.tax_rate = Decimal(str(tax_rate))
        quotation.subtotal = totals.subtotal
        quotation.discount_amount = totals.discount_amount
        quotation.tax_amount = totals.tax_amount
        quotation.grand_total = totals.grand_total

        FinanceService._log_activity(
            db, quotation.customer_id, "Quotation Updated", f"Quotation {quotation.quotation_number} was updated.", actor
        )
        db.commit()
        db.refresh(quotation)
        return quotation

    @staticmethod
    def set_quotation_status(db: Session, quotation_id: int, new_status: str, actor: str = "system") -> Quotation:
        quotation = FinanceService.get_quotation(db, quotation_id)
        if quotation.status == QuotationStatus.CONVERTED.value:
            FinanceService._fail(
                "A converted quotation cannot change status.", status.HTTP_409_CONFLICT
            )
        if new_status == QuotationStatus.CONVERTED.value:
            FinanceService._fail(
                "Convert a quotation by creating an invoice from it.", status.HTTP_400_BAD_REQUEST
            )

        quotation.status = new_status
        if new_status == QuotationStatus.SENT.value and quotation.sent_at is None:
            quotation.sent_at = datetime.utcnow()

        FinanceService._log_activity(
            db,
            quotation.customer_id,
            "Quotation Status Changed",
            f"Quotation {quotation.quotation_number} marked {new_status}.",
            actor,
        )
        db.commit()
        db.refresh(quotation)
        return quotation

    @staticmethod
    def cancel_quotation(db: Session, quotation_id: int, actor: str = "system") -> Quotation:
        """Archive a quotation. Financial records are cancelled, never deleted."""
        quotation = FinanceService.get_quotation(db, quotation_id)
        if quotation.status == QuotationStatus.CONVERTED.value:
            FinanceService._fail(
                "This quotation has already been invoiced and cannot be cancelled.",
                status.HTTP_409_CONFLICT,
            )
        quotation.status = QuotationStatus.CANCELLED.value
        FinanceService._log_activity(
            db, quotation.customer_id, "Quotation Cancelled", f"Quotation {quotation.quotation_number} was cancelled.", actor
        )
        db.commit()
        db.refresh(quotation)
        return quotation

    # ------------------------------------------------------------------
    # Invoices
    # ------------------------------------------------------------------

    @staticmethod
    def _build_invoice(
        db: Session,
        *,
        customer_id: int,
        items: Sequence[Any],
        discount_type: str,
        discount_value: Any,
        tax_rate: Any,
        issue_date: date | None,
        due_date: date | None,
        notes: str | None,
        terms: str | None,
        quotation: Quotation | None,
        actor: str,
    ) -> Invoice:
        customer = CRMService.get_customer(db, customer_id)
        totals = FinanceService._compute(items, discount_type, discount_value, tax_rate)

        for attempt in range(_NUMBER_ALLOCATION_ATTEMPTS):
            number, year, sequence = FinanceService._next_number(db, Invoice, INVOICE_PREFIX)
            invoice = Invoice(
                invoice_number=number,
                sequence_year=year,
                sequence_number=sequence,
                customer_id=customer.id,
                quotation_id=quotation.id if quotation else None,
                status=InvoiceStatus.DRAFT.value,
                issue_date=issue_date or date.today(),
                due_date=due_date,
                currency=settings.CURRENCY_CODE,
                discount_type=discount_type,
                discount_value=money(discount_value or 0),
                tax_rate=Decimal(str(tax_rate or 0)),
                subtotal=totals.subtotal,
                discount_amount=totals.discount_amount,
                tax_amount=totals.tax_amount,
                grand_total=totals.grand_total,
                amount_paid=Decimal("0.00"),
                notes=notes,
                terms=terms or (settings.DOCUMENT_TERMS or None),
                created_by=actor,
            )
            for position, (raw, line) in enumerate(zip(items, totals.lines)):
                description = raw["description"] if isinstance(raw, dict) else raw.description
                invoice.items.append(
                    InvoiceItem(
                        position=position,
                        description=description,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        line_total=line.line_total,
                    )
                )

            db.add(invoice)
            if quotation is not None:
                quotation.status = QuotationStatus.CONVERTED.value

            FinanceService._log_activity(
                db,
                customer.id,
                "Invoice Created",
                f"Invoice {number} created for {settings.CURRENCY_SYMBOL}{totals.grand_total:,.2f}"
                + (f" from quotation {quotation.quotation_number}." if quotation else "."),
                actor,
            )
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                if attempt == _NUMBER_ALLOCATION_ATTEMPTS - 1:
                    FinanceService._fail(
                        "Could not allocate a unique invoice number. Please retry.",
                        status.HTTP_409_CONFLICT,
                    )
                continue
            db.refresh(invoice)
            return invoice

        raise AssertionError("unreachable")  # pragma: no cover

    @staticmethod
    def create_invoice(db: Session, payload: dict[str, Any], actor: str = "system") -> Invoice:
        quotation = None
        if payload.get("quotation_id"):
            quotation = FinanceService.get_quotation(db, payload["quotation_id"])
            if quotation.status == QuotationStatus.CONVERTED.value:
                FinanceService._fail(
                    f"Quotation {quotation.quotation_number} has already been invoiced.",
                    status.HTTP_409_CONFLICT,
                )
            if quotation.status == QuotationStatus.CANCELLED.value:
                FinanceService._fail(
                    f"Quotation {quotation.quotation_number} is cancelled.", status.HTTP_409_CONFLICT
                )

        return FinanceService._build_invoice(
            db,
            customer_id=payload["customer_id"],
            items=payload.get("items") or [],
            discount_type=payload.get("discount_type") or DiscountType.PERCENTAGE.value,
            discount_value=payload.get("discount_value") or 0,
            tax_rate=payload.get("tax_rate") or 0,
            issue_date=payload.get("issue_date"),
            due_date=payload.get("due_date"),
            notes=payload.get("notes"),
            terms=payload.get("terms"),
            quotation=quotation,
            actor=actor,
        )

    @staticmethod
    def create_invoice_from_quotation(
        db: Session, quotation_id: int, payload: dict[str, Any] | None = None, actor: str = "system"
    ) -> Invoice:
        """Generate an invoice that mirrors an existing quotation."""
        payload = payload or {}
        quotation = FinanceService.get_quotation(db, quotation_id)

        if quotation.status == QuotationStatus.CONVERTED.value:
            FinanceService._fail(
                f"Quotation {quotation.quotation_number} has already been invoiced.",
                status.HTTP_409_CONFLICT,
            )
        if quotation.status == QuotationStatus.CANCELLED.value:
            FinanceService._fail(
                f"Quotation {quotation.quotation_number} is cancelled and cannot be invoiced.",
                status.HTTP_409_CONFLICT,
            )
        if not quotation.items:
            FinanceService._fail("This quotation has no line items.")

        items = [
            {"description": item.description, "quantity": item.quantity, "unit_price": item.unit_price}
            for item in quotation.items
        ]
        return FinanceService._build_invoice(
            db,
            customer_id=quotation.customer_id,
            items=items,
            discount_type=quotation.discount_type,
            discount_value=quotation.discount_value,
            tax_rate=quotation.tax_rate,
            issue_date=payload.get("issue_date"),
            due_date=payload.get("due_date"),
            notes=quotation.notes,
            terms=quotation.terms,
            quotation=quotation,
            actor=actor,
        )

    @staticmethod
    def list_invoices(
        db: Session,
        *,
        q: str | None = None,
        status_filter: str | None = None,
        customer_id: int | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        query = db.query(Invoice).options(selectinload(Invoice.items))
        if customer_id is not None:
            query = query.filter(Invoice.customer_id == customer_id)
        if status_filter:
            query = query.filter(Invoice.status == status_filter)
        if q:
            query = query.filter(Invoice.invoice_number.ilike(f"%{q}%"))
        query = query.order_by(Invoice.created_at.desc(), Invoice.id.desc())
        return FinanceService._paginate(
            query, page, page_size, lambda row: FinanceService.serialize_invoice(row, include_items=False)
        )

    @staticmethod
    def get_invoice(db: Session, invoice_id: int) -> Invoice:
        invoice = (
            db.query(Invoice)
            .options(selectinload(Invoice.items), selectinload(Invoice.payments))
            .filter(Invoice.id == invoice_id)
            .first()
        )
        if invoice is None:
            FinanceService._fail("Invoice not found.", status.HTTP_404_NOT_FOUND)
        return invoice

    @staticmethod
    def update_invoice(db: Session, invoice_id: int, payload: dict[str, Any], actor: str = "system") -> Invoice:
        invoice = FinanceService.get_invoice(db, invoice_id)
        if invoice.status in INVOICE_LOCKED_STATUSES:
            FinanceService._fail(f"A {invoice.status} invoice cannot be edited.", status.HTTP_409_CONFLICT)
        if invoice.payments:
            FinanceService._fail(
                "This invoice has recorded payments and can no longer be edited.",
                status.HTTP_409_CONFLICT,
            )

        if payload.get("customer_id") and payload["customer_id"] != invoice.customer_id:
            invoice.customer_id = CRMService.get_customer(db, payload["customer_id"]).id

        for field in ("issue_date", "due_date", "notes", "terms"):
            if field in payload:
                setattr(invoice, field, payload[field])

        discount_type = payload.get("discount_type", invoice.discount_type)
        discount_value = payload.get("discount_value", invoice.discount_value)
        tax_rate = payload.get("tax_rate", invoice.tax_rate)

        items = payload.get("items")
        source_items = items if items is not None else invoice.items
        totals = FinanceService._compute(source_items, discount_type, discount_value, tax_rate)

        if items is not None:
            invoice.items.clear()
            db.flush()
            for position, (raw, line) in enumerate(zip(items, totals.lines)):
                description = raw["description"] if isinstance(raw, dict) else raw.description
                invoice.items.append(
                    InvoiceItem(
                        position=position,
                        description=description,
                        quantity=line.quantity,
                        unit_price=line.unit_price,
                        line_total=line.line_total,
                    )
                )

        invoice.discount_type = discount_type
        invoice.discount_value = money(discount_value)
        invoice.tax_rate = Decimal(str(tax_rate))
        invoice.subtotal = totals.subtotal
        invoice.discount_amount = totals.discount_amount
        invoice.tax_amount = totals.tax_amount
        invoice.grand_total = totals.grand_total

        FinanceService._log_activity(
            db, invoice.customer_id, "Invoice Updated", f"Invoice {invoice.invoice_number} was updated.", actor
        )
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def set_invoice_status(db: Session, invoice_id: int, new_status: str, actor: str = "system") -> Invoice:
        """Set a lifecycle status.

        Payment-derived statuses (``paid`` / ``partially_paid``) are owned by
        :meth:`record_payment` and cannot be set by hand — otherwise an invoice
        could read "paid" with no payment behind it.
        """
        invoice = FinanceService.get_invoice(db, invoice_id)
        if new_status in (InvoiceStatus.PAID.value, InvoiceStatus.PARTIALLY_PAID.value):
            FinanceService._fail(
                "Payment status is derived from recorded payments. Record a payment instead.",
                status.HTTP_400_BAD_REQUEST,
            )
        if invoice.status == InvoiceStatus.CANCELLED.value:
            FinanceService._fail("A cancelled invoice cannot change status.", status.HTTP_409_CONFLICT)
        if invoice.payments:
            FinanceService._fail(
                "This invoice has recorded payments; its status is managed by the payment history.",
                status.HTTP_409_CONFLICT,
            )

        invoice.status = new_status
        if new_status == InvoiceStatus.SENT.value and invoice.sent_at is None:
            invoice.sent_at = datetime.utcnow()

        FinanceService._log_activity(
            db, invoice.customer_id, "Invoice Status Changed", f"Invoice {invoice.invoice_number} marked {new_status}.", actor
        )
        db.commit()
        db.refresh(invoice)
        return invoice

    @staticmethod
    def cancel_invoice(db: Session, invoice_id: int, actor: str = "system") -> Invoice:
        invoice = FinanceService.get_invoice(db, invoice_id)
        if invoice.payments:
            FinanceService._fail(
                "This invoice has recorded payments and cannot be cancelled.", status.HTTP_409_CONFLICT
            )
        invoice.status = InvoiceStatus.CANCELLED.value
        FinanceService._log_activity(
            db, invoice.customer_id, "Invoice Cancelled", f"Invoice {invoice.invoice_number} was cancelled.", actor
        )
        db.commit()
        db.refresh(invoice)
        return invoice

    # ------------------------------------------------------------------
    # Payments and receipts
    # ------------------------------------------------------------------

    @staticmethod
    def record_payment(db: Session, payload: dict[str, Any], actor: str = "system") -> Payment:
        """Record a confirmed payment and issue its receipt in one transaction.

        The receipt is generated automatically, so a payment can never exist
        without a traceable receipt.
        """
        invoice = FinanceService.get_invoice(db, payload["invoice_id"])

        if invoice.status == InvoiceStatus.CANCELLED.value:
            FinanceService._fail("Payments cannot be recorded against a cancelled invoice.", status.HTTP_409_CONFLICT)

        try:
            amount = money(payload["amount"], field_name="amount")
        except CalculationError as exc:
            FinanceService._fail(str(exc))

        if amount <= 0:
            FinanceService._fail("Payment amount must be greater than zero.")

        balance = invoice.balance_due
        if balance <= 0:
            FinanceService._fail(
                f"Invoice {invoice.invoice_number} is already settled in full.", status.HTTP_409_CONFLICT
            )
        if amount > balance:
            FinanceService._fail(
                f"Payment of {settings.CURRENCY_SYMBOL}{amount:,.2f} exceeds the outstanding "
                f"balance of {settings.CURRENCY_SYMBOL}{balance:,.2f}."
            )

        method = payload.get("method")
        valid_methods = {item.value for item in PaymentMethod}
        if method not in valid_methods:
            FinanceService._fail(f"Payment method must be one of: {', '.join(sorted(valid_methods))}.")

        payment = Payment(
            invoice_id=invoice.id,
            amount=amount,
            method=method,
            reference=payload.get("reference"),
            payment_date=payload.get("payment_date") or date.today(),
            notes=payload.get("notes"),
            recorded_by=actor,
        )
        db.add(payment)

        invoice.amount_paid = money(Decimal(invoice.amount_paid) + amount)
        remaining = invoice.balance_due
        invoice.status = (
            InvoiceStatus.PAID.value if remaining <= 0 else InvoiceStatus.PARTIALLY_PAID.value
        )
        db.flush()

        for attempt in range(_NUMBER_ALLOCATION_ATTEMPTS):
            number, year, sequence = FinanceService._next_number(db, Receipt, RECEIPT_PREFIX)
            receipt = Receipt(
                receipt_number=number,
                sequence_year=year,
                sequence_number=sequence,
                payment_id=payment.id,
                balance_after=remaining,
            )
            db.add(receipt)
            FinanceService._log_activity(
                db,
                invoice.customer_id,
                "Payment Recorded",
                f"Payment of {settings.CURRENCY_SYMBOL}{amount:,.2f} recorded against "
                f"invoice {invoice.invoice_number}. Receipt {number} issued.",
                actor,
            )
            try:
                db.commit()
            except IntegrityError:
                db.rollback()
                if attempt == _NUMBER_ALLOCATION_ATTEMPTS - 1:
                    FinanceService._fail(
                        "Could not allocate a unique receipt number. Please retry.",
                        status.HTTP_409_CONFLICT,
                    )
                # Re-resolve state after rollback before retrying.
                invoice = FinanceService.get_invoice(db, payload["invoice_id"])
                continue
            db.refresh(payment)
            return payment

        raise AssertionError("unreachable")  # pragma: no cover

    @staticmethod
    def list_payments(
        db: Session,
        *,
        invoice_id: int | None = None,
        method: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        query = db.query(Payment).options(selectinload(Payment.receipt))
        if invoice_id is not None:
            query = query.filter(Payment.invoice_id == invoice_id)
        if method:
            query = query.filter(Payment.method == method)
        query = query.order_by(Payment.payment_date.desc(), Payment.id.desc())
        return FinanceService._paginate(query, page, page_size, FinanceService.serialize_payment)

    @staticmethod
    def get_payment(db: Session, payment_id: int) -> Payment:
        payment = (
            db.query(Payment)
            .options(selectinload(Payment.receipt))
            .filter(Payment.id == payment_id)
            .first()
        )
        if payment is None:
            FinanceService._fail("Payment not found.", status.HTTP_404_NOT_FOUND)
        return payment

    @staticmethod
    def list_receipts(db: Session, *, page: int = 1, page_size: int = 20) -> dict[str, Any]:
        query = db.query(Receipt).order_by(Receipt.issued_at.desc(), Receipt.id.desc())
        return FinanceService._paginate(query, page, page_size, FinanceService.serialize_receipt)

    @staticmethod
    def get_receipt(db: Session, receipt_id: int) -> Receipt:
        receipt = db.query(Receipt).filter(Receipt.id == receipt_id).first()
        if receipt is None:
            FinanceService._fail("Receipt not found.", status.HTTP_404_NOT_FOUND)
        return receipt

    @staticmethod
    def get_receipt_detail(db: Session, receipt_id: int) -> dict[str, Any]:
        """A receipt plus its payment, invoice and customer context."""
        receipt = FinanceService.get_receipt(db, receipt_id)
        payment = FinanceService.get_payment(db, receipt.payment_id)
        invoice = FinanceService.get_invoice(db, payment.invoice_id)

        data = FinanceService.serialize_receipt(receipt)
        data.update(
            {
                "payment": FinanceService.serialize_payment(payment),
                "invoice_id": invoice.id,
                "invoice_number": invoice.invoice_number,
                "customer": FinanceService._customer_summary(invoice.customer),
            }
        )
        return data

    @staticmethod
    def get_receipt_for_payment(db: Session, payment_id: int) -> Receipt:
        receipt = db.query(Receipt).filter(Receipt.payment_id == payment_id).first()
        if receipt is None:
            FinanceService._fail("No receipt exists for this payment.", status.HTTP_404_NOT_FOUND)
        return receipt

    # ------------------------------------------------------------------
    # Reporting — consumed by the Dashboard module and the AI assistant
    # ------------------------------------------------------------------

    @staticmethod
    def get_finance_summary(db: Session) -> dict[str, Any]:
        def _counts(model) -> dict[str, int]:
            rows = db.query(model.status, func.count(model.id)).group_by(model.status).all()
            return {str(row_status): int(count) for row_status, count in rows}

        quotation_counts = _counts(Quotation)
        invoice_counts = _counts(Invoice)

        active_quotations = [
            s for s in quotation_counts if s != QuotationStatus.CANCELLED.value
        ]
        total_quoted = (
            db.query(func.coalesce(func.sum(Quotation.grand_total), 0))
            .filter(Quotation.status.in_(active_quotations or [""]))
            .scalar()
        )

        billable = [s for s in invoice_counts if s != InvoiceStatus.CANCELLED.value]
        total_invoiced = (
            db.query(func.coalesce(func.sum(Invoice.grand_total), 0))
            .filter(Invoice.status.in_(billable or [""]))
            .scalar()
        )
        total_collected = (
            db.query(func.coalesce(func.sum(Invoice.amount_paid), 0))
            .filter(Invoice.status.in_(billable or [""]))
            .scalar()
        )

        total_invoiced = money(total_invoiced or 0)
        total_collected = money(total_collected or 0)

        paid = invoice_counts.get(InvoiceStatus.PAID.value, 0)
        partial = invoice_counts.get(InvoiceStatus.PARTIALLY_PAID.value, 0)
        unpaid = sum(
            count
            for row_status, count in invoice_counts.items()
            if row_status in (InvoiceStatus.DRAFT.value, InvoiceStatus.SENT.value)
        )

        return {
            "currency": settings.CURRENCY_CODE,
            "total_quotations": sum(quotation_counts.values()),
            "quotations_by_status": quotation_counts,
            "total_quoted_value": money(total_quoted or 0),
            "total_invoices": sum(invoice_counts.values()),
            "invoices_by_status": invoice_counts,
            "total_invoiced_value": total_invoiced,
            "total_collected": total_collected,
            "total_outstanding": money(total_invoiced - total_collected),
            "paid_invoices": paid,
            "unpaid_invoices": unpaid,
            "partially_paid_invoices": partial,
        }
