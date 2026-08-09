# Finance Module

Quotations, invoices, payments and receipts, with server-side PDF generation
and email delivery.

The module lives in `backend/app` alongside CRM, AI and Communication, and
reuses their models and services rather than duplicating them. It owns no
customer data: quotations and invoices reference the CRM `customers` table
directly.

---

## Business flow

```text
CRM Customer
     |
     v
Quotation  --(optional)-->  Invoice  -->  Payment  -->  Receipt (automatic)
```

An invoice can be raised **directly** from a customer, or **generated from a
quotation**, which copies the line items, discount and tax so the two documents
can never disagree. Recording a payment always issues a receipt in the same
transaction, so no payment exists without a traceable receipt.

---

## Data model

| Table | Purpose | Key relationships |
|---|---|---|
| `quotations` | Quotation header, totals, status | `customer_id` → `customers` |
| `quotation_items` | Line items (description, qty, unit price, line total) | `quotation_id` → `quotations` (cascade) |
| `invoices` | Invoice header, totals, `amount_paid` | `customer_id` → `customers`, optional `quotation_id` → `quotations` |
| `invoice_items` | Line items | `invoice_id` → `invoices` (cascade) |
| `payments` | A confirmed payment against an invoice | `invoice_id` → `invoices` (cascade) |
| `receipts` | Proof of one payment, with a balance snapshot | `payment_id` → `payments` (unique, cascade) |

Design decisions:

- **Money is `NUMERIC(14, 2)`, never `FLOAT`,** and is read back as
  `decimal.Decimal`. Quantities are `NUMERIC(12, 3)` so fractional units
  (hours, kilograms) are supported.
- **Totals are persisted, not derived at read time.** `docs/database/data-model.md`
  requires that issued documents keep their snapshot, so a later tax-rate change
  must not restate an old document. Every write path recomputes the totals via
  `finance_calculator`, so stored values cannot drift from the line items.
- **Financial records are archived, not deleted.** `DELETE` endpoints set the
  status to `cancelled`.
- **Document numbers** are backed by integer `sequence_year` / `sequence_number`
  columns so "next number" is a numeric `MAX()`. A lexicographic max would order
  `...-1000` before `...-999`. A unique constraint plus a bounded retry handles
  concurrent allocation.

### Statuses

| Document | Statuses |
|---|---|
| Quotation | `draft`, `sent`, `accepted`, `rejected`, `converted`, `cancelled` |
| Invoice | `draft`, `sent`, `partially_paid`, `paid`, `cancelled` |

`paid` and `partially_paid` are **derived from recorded payments** and cannot be
set by hand — otherwise an invoice could read "paid" with nothing behind it.

### Document numbering

`QT-2026-001`, `INV-2026-001`, `RCT-2026-001` — prefix, year, zero-padded
sequence that restarts each calendar year.

---

## Calculation rules

Defined in exactly one place: `backend/app/services/finance_calculator.py`.

```text
line_total   = quantity x unit_price
subtotal     = sum(line_totals)
discount     = percentage of subtotal, or a fixed amount (capped at subtotal)
taxable_base = subtotal - discount
tax          = taxable_base x tax_rate%
grand_total  = taxable_base + tax
```

- Tax is charged on the **discounted** amount.
- All money is `Decimal` quantized to 2 decimal places, **ROUND_HALF_UP**.
- Float inputs are converted via `str()` first, because `Decimal(0.1)` is not
  `0.1` while `Decimal("0.1")` is exact.
- A fixed discount larger than the subtotal is rejected rather than clamped
  silently, since it would otherwise produce a negative taxable base.

**The backend is authoritative.** Client-supplied totals are ignored; every
amount is recomputed from the line items before persisting. The frontend has a
mirrored preview in `frontend/src/lib/finance-preview.ts` that is clearly
labelled "Preview · confirmed by server on save" and is never sent back.

Validation rejects: non-positive quantities, negative prices, tax rates outside
0–100, negative discounts, percentage discounts above 100, fixed discounts above
the subtotal, empty documents, non-finite numbers, and payments that exceed the
outstanding balance.

---

## API

All endpoints are under `/api/v1` and require a bearer token
(see [Authentication](#authentication-and-roles)). `/health` endpoints are public.

### Quotations

| Method | Path | Notes |
|---|---|---|
| `POST` | `/quotations` | Create |
| `GET` | `/quotations` | List; filters `q`, `status`, `customer_id`, `page`, `page_size` |
| `GET` | `/quotations/{id}` | Detail with line items |
| `PATCH` | `/quotations/{id}` | Update; blocked once `converted`/`cancelled` |
| `PATCH` | `/quotations/{id}/status` | `sent`, `accepted`, `rejected` |
| `DELETE` | `/quotations/{id}` | Cancel (archive). **Admin only** |
| `POST` | `/quotations/{id}/invoice` | Convert to an invoice |
| `GET` | `/quotations/{id}/pdf` | PDF |
| `POST` | `/quotations/{id}/send` | Email with PDF attached |

### Invoices

| Method | Path | Notes |
|---|---|---|
| `POST` | `/invoices` | Create (optionally with `quotation_id`) |
| `GET` | `/invoices` | List; same filters as quotations |
| `GET` | `/invoices/{id}` | Detail |
| `PATCH` | `/invoices/{id}` | Update; blocked once paid, cancelled, or once a payment exists |
| `PATCH` | `/invoices/{id}/status` | `draft`, `sent`, `cancelled` only |
| `DELETE` | `/invoices/{id}` | Cancel (archive). **Admin only**; blocked if payments exist |
| `GET` | `/invoices/{id}/payments` | Payment history |
| `GET` | `/invoices/{id}/pdf` | PDF |
| `POST` | `/invoices/{id}/send` | Email with PDF attached |

### Payments and receipts

| Method | Path | Notes |
|---|---|---|
| `POST` | `/payments` | Record a payment; **issues a receipt automatically** |
| `GET` | `/payments` | List; filters `invoice_id`, `method` |
| `GET` | `/payments/{id}` | Detail, including its receipt |
| `GET` | `/payments/{id}/receipt` | The receipt for this payment |
| `GET` | `/receipts` | List |
| `GET` | `/receipts/{id}` | Receipt with payment, invoice and customer context |
| `GET` | `/receipts/{id}/pdf` | PDF |
| `POST` | `/receipts/{id}/send` | Email with PDF attached |

Supported payment methods: `cash`, `bank_transfer`, `card`, `online`.

### Overview

| Method | Path | Notes |
|---|---|---|
| `GET` | `/finance/summary` | Revenue, collected, outstanding, counts by status |
| `GET` | `/finance/settings` | Currency and company branding |

### Example — create a quotation

```http
POST /api/v1/quotations
Authorization: Bearer <token>

{
  "customer_id": 1,
  "items": [
    { "description": "Dell Latitude 5540 Laptop", "quantity": 25, "unit_price": 899.99 },
    { "description": "Docking Station", "quantity": 25, "unit_price": 45.50 }
  ],
  "discount_type": "percentage",
  "discount_value": 10,
  "tax_rate": 17,
  "valid_until": "2026-09-30"
}
```

```json
{
  "id": 1,
  "quotation_number": "QT-2026-001",
  "status": "draft",
  "subtotal": 23637.25,
  "discount_amount": 2363.73,
  "tax_amount": 3616.50,
  "grand_total": 24890.02,
  "customer": { "id": 1, "full_name": "John Carter", "email": "john.carter@apex.example" },
  "items": [ ... ]
}
```

Collections return the project's standard envelope:
`{ total, page, page_size, total_pages, items }`.

---

## Authentication and roles

Finance endpoints require an access token issued by the **Authentication
module** (the root `app/` application). This module does not create a second
authentication system — `backend/app/core/security.py` only *verifies* tokens,
using the same secret, algorithm and claims.

Two roles are recognised, per the supervisor's specification:

| Role | Permissions |
|---|---|
| `user` | Create, read, update, send documents; record payments |
| `admin` | Everything above, plus cancelling (archiving) quotations and invoices |

Any role that is not `admin` is treated as `user`, so a token issued before the
`role` claim existed degrades to the least-privileged role rather than
accidentally granting admin access.

`AUTH_REQUIRED=false` allows anonymous access for local demos before the login
screen exists. It mirrors the existing mailer dry-run convention. It never
grants the admin role, and a token that is present but invalid is always
rejected.

---

## PDF generation

`backend/app/services/finance_pdf_service.py`, built on **ReportLab** (pure
Python, so it needs no extra system packages in the existing slim image).

One standard template serves all three document types — the same header,
branding, customer block, item table and totals panel — so a branding change is
made in one place. Each document supplies only its own title, metadata and
summary rows.

Included: company name/logo/address/contact, customer details, document number
and dates, itemised table with repeating headers across pages, subtotal,
discount, tax, grand total, payment/balance information, notes and terms, and a
"Page X of Y" footer.

Branding comes from settings, so no company data is hardcoded. A missing or
unreadable logo is logged and skipped rather than failing the document.

---

## Integrations

| Module | How Finance uses it |
|---|---|
| **CRM** | The only source of customers. `CRMService.get_customer` resolves every customer, so soft-deleted and unknown customers are rejected consistently. Finance also appends `Quotation Created`, `Invoice Created`, `Payment Recorded` entries to the shared customer timeline (`activity_logs`), so finance events appear in the CRM UI automatically. |
| **Communication Hub** | Email delivery goes through `CommunicationService.send_direct_email`, which owns SMTP, the email log and the customer conversation thread. Finance added an optional `attachments` parameter to it and to `mailer_service.send_email` — additive, defaulting to none, so existing callers are unaffected. |
| **AI Executive Assistant** | Finance registers `create_quotation`, `create_invoice`, `record_payment` and `finance_summary` in the existing tool registry (`backend/app/ai/tools.py`). The handlers call the same `FinanceService` the REST API uses, so an AI-initiated action is validated, calculated and audited identically. Writes are marked `requires_approval`, matching the CRM tools. Documents created this way are attributed to `ai-assistant`. |
| **Dashboard** | `GET /finance/summary` exposes revenue, collected, outstanding and per-status counts. The Dashboard module currently serves mock data and was **not modified**; it can consume this endpoint when its owner is ready. |

---

## Environment variables

Added to `.env.example`:

```bash
AUTH_REQUIRED=true          # false only for local demos without a login screen

CURRENCY_CODE=USD
CURRENCY_SYMBOL=$

COMPANY_NAME="Your Company"
COMPANY_ADDRESS="..."
COMPANY_EMAIL=billing@example.com
COMPANY_PHONE="+1 555 0100"
COMPANY_WEBSITE=www.example.com
COMPANY_TAX_NUMBER=
COMPANY_LOGO_PATH=          # path to a PNG/JPG drawn on document PDFs
DOCUMENT_TERMS="Payment due within 30 days of the invoice date."
```

The system uses a single currency, per the supervisor's specification.

---

## Setup

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8005

# Frontend
cd frontend
npm install
npm run dev
```

Migration: `alembic upgrade c3d5e7a9b1f2` (revision `c3d5e7a9b1f2`, chained onto
the AI revision `a1b2c3d4e5f6`).

> **Known repository issue, not introduced by this module:** the Alembic history
> has two heads (`48ecbadec3ed` and `c3d5e7a9b1f2`), and revisions
> `57cccf4d4954` and `07b2ecaedcfd` both create the `refresh_tokens` table, so a
> full `alembic upgrade head` fails on a clean database. This predates the
> Finance module and needs the Authentication module's owner to resolve. Until
> then the app's `Base.metadata.create_all()` on startup creates the finance
> tables for development.

---

## Testing

```bash
cd backend
python -m pytest tests/ -q
```

179 tests covering: the calculation engine (rounding, precision, discounts,
tax order, edge cases), quotation and invoice lifecycles, quotation→invoice
conversion, payment tracking and partial payments, automatic receipt
generation, PDF structure and layout, email delivery with attachments,
authentication, RBAC, and the AI tool registry.

---

## Frontend

| Route | Purpose |
|---|---|
| `/finance` | Overview: KPIs, recent quotations and invoices |
| `/finance/quotations` | List with search, status filter, pagination |
| `/finance/quotations/new` | Create |
| `/finance/quotations/[id]` | Detail: PDF, send, accept/reject, convert to invoice |
| `/finance/invoices` | List with search, status filter, pagination |
| `/finance/invoices/new` | Create |
| `/finance/invoices/[id]` | Detail: PDF, send, record payment, payment history, receipt PDFs |

Built with the existing Tailwind dark slate/indigo design system and the
`apiClient` from `lib/api.ts`. `Finance & Invoices` in the sidebar now points at
`/finance` instead of `#`.

---

## Deliberately out of scope

Recurring invoices, payment gateways, QR payment links, due-date reminder jobs,
multi-currency, accounting-software integration and customer-customisable PDF
templates are **not** implemented. They appear in the project vision document
but were not part of the assigned module scope, and the supervisor confirmed a
single currency, one standard template and basic payment tracking.

## Known limitation: tenant isolation

`backend/app` has no company/tenant scoping anywhere — the CRM `customers` table
has no `company_id`, and no module in this application filters by company.
Finance therefore records `created_by` / `recorded_by` for audit but does **not**
implement company isolation on its own. Adding a `company_id` only to finance
tables would create the appearance of isolation while the referenced customers
remained globally visible, which is worse than not having it. This needs a
cross-module decision, ideally alongside the CRM adopting the `company_id` that
`docs/database/data-model.md` already specifies.
