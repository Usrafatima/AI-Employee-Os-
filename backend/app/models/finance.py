"""Finance module persistence models: quotations, invoices, payments, receipts.

Design notes
------------
* **Customers are not redefined here.** Quotations and invoices reference the
  CRM ``customers`` table (``app.models.crm.Customer``) directly.
* **Money uses NUMERIC, never FLOAT.** The CRM stores ``expected_value`` as a
  float, which is fine for an estimate but not for amounts that must reconcile
  to the cent. Every monetary column below is ``Numeric(14, 2)`` and is read
  back as :class:`decimal.Decimal`.
* **Totals are persisted, not derived at read time.** ``docs/database/data-model.md``
  requires that quotation and invoice snapshots be preserved after issuance, so
  a later change to a tax rate must not silently restate an issued document.
  Every write path recomputes them through ``finance_calculator`` so the stored
  values can never drift from the line items.
* **Financial records are archived, not deleted** (also per ``data-model.md``):
  documents move to a ``cancelled`` status instead of being removed.
* ``sequence_year`` / ``sequence_number`` back the human-readable document
  numbers. They are stored as integers so "next number" is a numeric MAX()
  rather than a lexicographic one, which would order ``...-1000`` before
  ``...-999``.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

if TYPE_CHECKING:  # pragma: no cover - import used for type checking only
    from app.models.crm import Customer


class QuotationStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    CONVERTED = "converted"
    CANCELLED = "cancelled"


class InvoiceStatus(str, Enum):
    DRAFT = "draft"
    SENT = "sent"
    PARTIALLY_PAID = "partially_paid"
    PAID = "paid"
    CANCELLED = "cancelled"


class DiscountType(str, Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class PaymentMethod(str, Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    CARD = "card"
    ONLINE = "online"


#: Statuses at which a document is locked against edits to its financial content.
QUOTATION_LOCKED_STATUSES = (QuotationStatus.CONVERTED.value, QuotationStatus.CANCELLED.value)
INVOICE_LOCKED_STATUSES = (InvoiceStatus.PAID.value, InvoiceStatus.CANCELLED.value)

_MONEY = Numeric(14, 2)
_QUANTITY = Numeric(12, 3)
_RATE = Numeric(6, 3)


class Quotation(Base):
    __tablename__ = "quotations"
    __table_args__ = (
        UniqueConstraint("quotation_number", name="uq_quotation_number"),
        UniqueConstraint("sequence_year", "sequence_number", name="uq_quotation_sequence"),
        Index("ix_quotation_customer_status", "customer_id", "status"),
        Index("ix_quotation_issue_date", "issue_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    quotation_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    sequence_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=QuotationStatus.DRAFT.value, index=True
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DiscountType.PERCENTAGE.value
    )
    discount_value: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    tax_rate: Mapped[Decimal] = mapped_column(_RATE, nullable=False, default=Decimal("0.000"))

    subtotal: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    items: Mapped[list["QuotationItem"]] = relationship(
        back_populates="quotation",
        cascade="all, delete-orphan",
        order_by="QuotationItem.position",
    )
    invoices: Mapped[list["Invoice"]] = relationship(back_populates="quotation")
    #: Read-only view of the CRM customer. `viewonly` because the Finance
    #: module reads customer data but never owns or mutates it, and so that no
    #: back_populates is required on the CRM model.
    customer: Mapped["Customer"] = relationship("Customer", lazy="joined", viewonly=True)


class QuotationItem(Base):
    __tablename__ = "quotation_items"
    __table_args__ = (Index("ix_quotation_item_quotation", "quotation_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    quotation_id: Mapped[int] = mapped_column(
        ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(_QUANTITY, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(_MONEY, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(_MONEY, nullable=False)

    quotation: Mapped[Quotation] = relationship(back_populates="items")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("invoice_number", name="uq_invoice_number"),
        UniqueConstraint("sequence_year", "sequence_number", name="uq_invoice_sequence"),
        Index("ix_invoice_customer_status", "customer_id", "status"),
        Index("ix_invoice_issue_date", "issue_date"),
        Index("ix_invoice_due_date", "due_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    sequence_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    # Set when the invoice was generated from a quotation. Invoices may also be
    # created directly, so this stays optional.
    quotation_id: Mapped[int | None] = mapped_column(
        ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True, index=True
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=InvoiceStatus.DRAFT.value, index=True
    )
    issue_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    discount_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default=DiscountType.PERCENTAGE.value
    )
    discount_value: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    tax_rate: Mapped[Decimal] = mapped_column(_RATE, nullable=False, default=Decimal("0.000"))

    subtotal: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    discount_amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    tax_amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    grand_total: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))
    #: Sum of recorded payments. Maintained by FinanceService whenever a payment
    #: is added or removed, so listing invoices never needs an aggregate query.
    amount_paid: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    terms: Mapped[str | None] = mapped_column(Text, nullable=True)

    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="InvoiceItem.position",
    )
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="invoice",
        cascade="all, delete-orphan",
        order_by="Payment.payment_date",
    )
    quotation: Mapped[Quotation | None] = relationship(back_populates="invoices")
    #: Read-only view of the CRM customer (see Quotation.customer).
    customer: Mapped["Customer"] = relationship("Customer", lazy="joined", viewonly=True)

    @property
    def balance_due(self) -> Decimal:
        return Decimal(self.grand_total or 0) - Decimal(self.amount_paid or 0)


class InvoiceItem(Base):
    __tablename__ = "invoice_items"
    __table_args__ = (Index("ix_invoice_item_invoice", "invoice_id", "position"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(_QUANTITY, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(_MONEY, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(_MONEY, nullable=False)

    invoice: Mapped[Invoice] = relationship(back_populates="items")


class Payment(Base):
    """A confirmed payment against an invoice.

    Recording a payment always produces a :class:`Receipt` in the same
    transaction, so no payment can exist without a traceable receipt.
    """

    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payment_invoice_date", "invoice_id", "payment_date"),
        Index("ix_payment_method", "method"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(_MONEY, nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    reference: Mapped[str | None] = mapped_column(String(120), nullable=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False, default=date.today, index=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    recorded_by: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    invoice: Mapped[Invoice] = relationship(back_populates="payments")
    receipt: Mapped["Receipt | None"] = relationship(
        back_populates="payment", cascade="all, delete-orphan", uselist=False
    )


class Receipt(Base):
    """Proof of a single payment. Generated automatically when a payment is recorded."""

    __tablename__ = "receipts"
    __table_args__ = (
        UniqueConstraint("receipt_number", name="uq_receipt_number"),
        UniqueConstraint("sequence_year", "sequence_number", name="uq_receipt_sequence"),
        UniqueConstraint("payment_id", name="uq_receipt_payment"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_number: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    sequence_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)

    payment_id: Mapped[int] = mapped_column(
        ForeignKey("payments.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    #: Balance remaining on the invoice immediately after this payment. Stored
    #: as a snapshot so a reprinted receipt always matches the original.
    balance_after: Mapped[Decimal] = mapped_column(_MONEY, nullable=False, default=Decimal("0.00"))

    issued_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )

    payment: Mapped[Payment] = relationship(back_populates="receipt")
