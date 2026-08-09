"""Request/response schemas for the Finance module.

Monetary fields are :class:`~decimal.Decimal` in Python and are serialized as
JSON numbers (not strings) so the existing frontend currency formatters keep
working unchanged. ``when_used="json"`` keeps ``model_dump()`` returning exact
Decimals for internal callers such as the AI tool registry.

Client-supplied totals are never trusted: the service layer recomputes every
amount from the line items through ``finance_calculator`` before persisting.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, PlainSerializer

QuotationStatus = Literal["draft", "sent", "accepted", "rejected", "converted", "cancelled"]
InvoiceStatus = Literal["draft", "sent", "partially_paid", "paid", "cancelled"]
DiscountType = Literal["percentage", "fixed"]
PaymentMethod = Literal["cash", "bank_transfer", "card", "online"]

#: A Decimal that serializes to a JSON number while staying exact in Python.
Money = Annotated[
    Decimal,
    PlainSerializer(lambda value: float(value), return_type=float, when_used="json"),
]


# --------------------------------------------------------------------------
# Line items
# --------------------------------------------------------------------------


class DocumentItemCreate(BaseModel):
    description: str = Field(..., min_length=1, max_length=255)
    quantity: Decimal = Field(..., gt=0, le=1_000_000)
    unit_price: Decimal = Field(..., ge=0, le=100_000_000)


class DocumentItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    position: int
    description: str
    quantity: Money
    unit_price: Money
    line_total: Money


# --------------------------------------------------------------------------
# Shared customer view (read from the CRM; Finance never owns customer data)
# --------------------------------------------------------------------------


class CustomerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    company_name: str | None = None
    email: str
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    country: str | None = None


# --------------------------------------------------------------------------
# Quotations
# --------------------------------------------------------------------------


class DocumentBase(BaseModel):
    discount_type: DiscountType = "percentage"
    discount_value: Decimal = Field(default=Decimal("0"), ge=0)
    tax_rate: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    notes: str | None = None
    terms: str | None = None


class QuotationCreate(DocumentBase):
    customer_id: int = Field(..., gt=0)
    items: list[DocumentItemCreate] = Field(..., min_length=1, max_length=200)
    issue_date: date | None = None
    valid_until: date | None = None


class QuotationUpdate(BaseModel):
    customer_id: int | None = Field(default=None, gt=0)
    items: list[DocumentItemCreate] | None = Field(default=None, min_length=1, max_length=200)
    issue_date: date | None = None
    valid_until: date | None = None
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(default=None, ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    terms: str | None = None


class QuotationStatusUpdate(BaseModel):
    status: QuotationStatus


class QuotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quotation_number: str
    customer_id: int
    customer: CustomerSummary | None = None
    status: QuotationStatus
    issue_date: date
    valid_until: date | None = None
    currency: str

    discount_type: DiscountType
    discount_value: Money
    tax_rate: Money

    subtotal: Money
    discount_amount: Money
    tax_amount: Money
    grand_total: Money

    notes: str | None = None
    terms: str | None = None
    items: list[DocumentItemResponse] = []

    sent_at: datetime | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Invoices
# --------------------------------------------------------------------------


class InvoiceCreate(DocumentBase):
    customer_id: int = Field(..., gt=0)
    items: list[DocumentItemCreate] = Field(..., min_length=1, max_length=200)
    issue_date: date | None = None
    due_date: date | None = None
    quotation_id: int | None = Field(default=None, gt=0)


class InvoiceFromQuotation(BaseModel):
    """Convert an existing quotation into an invoice.

    Line items, discount and tax are copied from the quotation so the two
    documents cannot disagree.
    """

    issue_date: date | None = None
    due_date: date | None = None


class InvoiceUpdate(BaseModel):
    customer_id: int | None = Field(default=None, gt=0)
    items: list[DocumentItemCreate] | None = Field(default=None, min_length=1, max_length=200)
    issue_date: date | None = None
    due_date: date | None = None
    discount_type: DiscountType | None = None
    discount_value: Decimal | None = Field(default=None, ge=0)
    tax_rate: Decimal | None = Field(default=None, ge=0, le=100)
    notes: str | None = None
    terms: str | None = None


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_number: str
    customer_id: int
    customer: CustomerSummary | None = None
    quotation_id: int | None = None
    status: InvoiceStatus
    issue_date: date
    due_date: date | None = None
    currency: str

    discount_type: DiscountType
    discount_value: Money
    tax_rate: Money

    subtotal: Money
    discount_amount: Money
    tax_amount: Money
    grand_total: Money
    amount_paid: Money
    balance_due: Money

    notes: str | None = None
    terms: str | None = None
    items: list[DocumentItemResponse] = []

    sent_at: datetime | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime


# --------------------------------------------------------------------------
# Payments and receipts
# --------------------------------------------------------------------------


class PaymentCreate(BaseModel):
    invoice_id: int = Field(..., gt=0)
    amount: Decimal = Field(..., gt=0)
    method: PaymentMethod
    reference: str | None = Field(default=None, max_length=120)
    payment_date: date | None = None
    notes: str | None = None


class ReceiptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    receipt_number: str
    payment_id: int
    balance_after: Money
    issued_at: datetime
    created_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    invoice_id: int
    amount: Money
    method: PaymentMethod
    reference: str | None = None
    payment_date: date
    notes: str | None = None
    recorded_by: str | None = None
    created_at: datetime
    receipt: ReceiptResponse | None = None


class ReceiptDetailResponse(ReceiptResponse):
    """A receipt together with the context needed to render or print it."""

    payment: PaymentResponse | None = None
    invoice_number: str | None = None
    invoice_id: int | None = None
    customer: CustomerSummary | None = None


# --------------------------------------------------------------------------
# Delivery and reporting
# --------------------------------------------------------------------------


class SendDocumentRequest(BaseModel):
    """Email a document to the customer with its PDF attached."""

    to_email: EmailStr | None = Field(
        default=None, description="Overrides the CRM customer email when supplied."
    )
    subject: str | None = Field(default=None, max_length=255)
    message: str | None = Field(default=None, max_length=5000)


class SendDocumentResponse(BaseModel):
    sent: bool
    to_email: str
    subject: str
    document_number: str
    email_log_id: int | None = None


class FinanceSummaryResponse(BaseModel):
    """Aggregates the Dashboard module can surface as finance KPIs."""

    currency: str
    total_quotations: int
    quotations_by_status: dict[str, int]
    total_quoted_value: Money

    total_invoices: int
    invoices_by_status: dict[str, int]
    total_invoiced_value: Money
    total_collected: Money
    total_outstanding: Money

    paid_invoices: int
    unpaid_invoices: int
    partially_paid_invoices: int


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[dict]
