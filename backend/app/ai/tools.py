from __future__ import annotations

from typing import Any, Callable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.crm_service import CRMService
from app.services.finance_service import FinanceService


def _create_customer(db: Session, arguments: dict[str, Any]) -> dict[str, Any]:
    customer = CRMService.create_customer(db, arguments)
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "company_name": customer.company_name,
        "email": customer.email,
    }


def _create_lead(db: Session, arguments: dict[str, Any]) -> dict[str, Any]:
    lead = CRMService.create_lead(db, arguments)
    return {
        "id": lead.id,
        "customer_id": lead.customer_id,
        "title": lead.title,
        "status": lead.status,
    }


def _crm_summary(db: Session, arguments: dict[str, Any]) -> dict[str, Any]:
    return CRMService.get_customer_sales_summary(db)


# --- Finance -----------------------------------------------------------------
# These wrap the same FinanceService the REST API uses, so an action performed
# by the assistant is validated, calculated and audited identically to one
# performed through the UI. Amounts are passed through as strings so they reach
# the Decimal-based calculator without a float round-trip.


def _items_from_arguments(arguments: dict[str, Any]) -> list[dict[str, Any]]:
    """Accept either a structured ``items`` list or one flat line item.

    The flat form ("25 laptops at 900 each") is what the current keyword
    extraction produces; the structured form is ready for a model that can
    emit JSON arguments directly.
    """
    items = arguments.get("items")
    if isinstance(items, list) and items:
        return items
    if arguments.get("description") is None:
        return []
    return [
        {
            "description": arguments["description"],
            "quantity": arguments.get("quantity", 1),
            "unit_price": arguments.get("unit_price", 0),
        }
    ]


def _document_payload(arguments: dict[str, Any]) -> dict[str, Any]:
    return {
        "customer_id": arguments.get("customer_id"),
        "items": _items_from_arguments(arguments),
        "discount_type": arguments.get("discount_type") or "percentage",
        "discount_value": arguments.get("discount_value") or 0,
        "tax_rate": arguments.get("tax_rate") or 0,
        "notes": arguments.get("notes"),
    }


def _create_quotation(db: Session, arguments: dict[str, Any]) -> dict[str, Any]:
    quotation = FinanceService.create_quotation(db, _document_payload(arguments), actor="ai-assistant")
    return {
        "id": quotation.id,
        "quotation_number": quotation.quotation_number,
        "customer_id": quotation.customer_id,
        "status": quotation.status,
        "grand_total": str(quotation.grand_total),
    }


def _create_invoice(db: Session, arguments: dict[str, Any]) -> dict[str, Any]:
    payload = _document_payload(arguments)
    payload["quotation_id"] = arguments.get("quotation_id")
    invoice = FinanceService.create_invoice(db, payload, actor="ai-assistant")
    return {
        "id": invoice.id,
        "invoice_number": invoice.invoice_number,
        "customer_id": invoice.customer_id,
        "status": invoice.status,
        "grand_total": str(invoice.grand_total),
    }


def _record_payment(db: Session, arguments: dict[str, Any]) -> dict[str, Any]:
    payment = FinanceService.record_payment(
        db,
        {
            "invoice_id": arguments.get("invoice_id"),
            "amount": arguments.get("amount"),
            "method": arguments.get("method") or "bank_transfer",
            "reference": arguments.get("reference"),
            "notes": arguments.get("notes"),
        },
        actor="ai-assistant",
    )
    return {
        "id": payment.id,
        "invoice_id": payment.invoice_id,
        "amount": str(payment.amount),
        "method": payment.method,
        "receipt_number": payment.receipt.receipt_number if payment.receipt else None,
    }


def _finance_summary(db: Session, arguments: dict[str, Any]) -> dict[str, Any]:
    summary = FinanceService.get_finance_summary(db)
    # Decimals are stringified so the result stays JSON-serialisable wherever
    # the orchestrator passes it next.
    return {
        key: (str(value) if hasattr(value, "quantize") else value) for key, value in summary.items()
    }


# Tool registry — every business task the assistant can execute.
# `fields` = allowed argument keys passed to the handler.
# `field_map` = rename natural-language keys (extracted by the AI) to the service's field names.
# `coerce` = cast extracted string values to the right Python type.
TOOLS: dict[str, dict[str, Any]] = {
    "create_customer": {
        "description": "Create a new CRM customer. Requires full_name and email.",
        "requires_approval": True,
        "handler": _create_customer,
        "fields": [
            "full_name", "company_name", "email", "phone", "address",
            "city", "country", "industry", "notes", "status",
        ],
        "field_map": {
            "name": "full_name",
            "fullname": "full_name",
            "customer name": "full_name",
            "company": "company_name",
            "companyname": "company_name",
            "companyName": "company_name",
        },
        "coerce": {},
    },
    "create_lead": {
        "description": "Create a new CRM lead for an existing customer. Requires customer_id, title and source.",
        "requires_approval": True,
        "handler": _create_lead,
        "fields": [
            "customer_id", "title", "source", "assigned_to", "status",
            "expected_value", "probability", "next_followup_date", "notes",
        ],
        "field_map": {
            "customer": "customer_id",
            "customerid": "customer_id",
            "customerId": "customer_id",
            "lead": "title",
            "lead name": "title",
            "leadname": "title",
        },
        "coerce": {"customer_id": int},
    },
    "crm_summary": {
        "description": "Read-only summary of customers and leads (safe to run without approval).",
        "requires_approval": False,
        "handler": _crm_summary,
        "fields": [],
        "field_map": {},
        "coerce": {},
    },
    "create_quotation": {
        "description": (
            "Create a quotation for an existing CRM customer. Requires customer_id and "
            "either an items list or a description with quantity and unit_price."
        ),
        "requires_approval": True,
        "handler": _create_quotation,
        "fields": [
            "customer_id", "items", "description", "quantity", "unit_price",
            "discount_type", "discount_value", "tax_rate", "notes",
        ],
        "field_map": {
            "customer": "customer_id",
            "customerid": "customer_id",
            "customerId": "customer_id",
            "product": "description",
            "item": "description",
            "service": "description",
            "qty": "quantity",
            "price": "unit_price",
            "rate": "unit_price",
            "unitprice": "unit_price",
            "unitPrice": "unit_price",
            "tax": "tax_rate",
            "discount": "discount_value",
        },
        "coerce": {"customer_id": int},
    },
    "create_invoice": {
        "description": (
            "Create an invoice for an existing CRM customer, optionally from a quotation. "
            "Requires customer_id and either an items list or a description with quantity "
            "and unit_price."
        ),
        "requires_approval": True,
        "handler": _create_invoice,
        "fields": [
            "customer_id", "quotation_id", "items", "description", "quantity",
            "unit_price", "discount_type", "discount_value", "tax_rate", "notes",
        ],
        "field_map": {
            "customer": "customer_id",
            "customerid": "customer_id",
            "customerId": "customer_id",
            "quotation": "quotation_id",
            "quotationid": "quotation_id",
            "product": "description",
            "item": "description",
            "service": "description",
            "qty": "quantity",
            "price": "unit_price",
            "rate": "unit_price",
            "unitprice": "unit_price",
            "tax": "tax_rate",
            "discount": "discount_value",
        },
        "coerce": {"customer_id": int, "quotation_id": int},
    },
    "record_payment": {
        "description": (
            "Record a payment against an invoice and automatically issue its receipt. "
            "Requires invoice_id and amount."
        ),
        "requires_approval": True,
        "handler": _record_payment,
        "fields": ["invoice_id", "amount", "method", "reference", "notes"],
        "field_map": {
            "invoice": "invoice_id",
            "invoiceid": "invoice_id",
            "invoiceId": "invoice_id",
            "paid": "amount",
            "payment": "amount",
            "payment_method": "method",
        },
        "coerce": {"invoice_id": int},
    },
    "finance_summary": {
        "description": (
            "Read-only finance overview: revenue, collected, outstanding balance and "
            "document counts by status (safe to run without approval)."
        ),
        "requires_approval": False,
        "handler": _finance_summary,
        "fields": [],
        "field_map": {},
        "coerce": {},
    },
}


def _normalize_arguments(spec: dict[str, Any], arguments: dict[str, Any]) -> dict[str, Any]:
    field_map = spec.get("field_map", {})
    allowed = set(spec.get("fields", []))
    coerce = spec.get("coerce", {})
    normalized: dict[str, Any] = {}
    for key, value in (arguments or {}).items():
        mapped = field_map.get(key, key)
        if mapped not in allowed:
            continue
        if value is None or value == "":
            continue
        if mapped in coerce:
            try:
                value = coerce[mapped](value)
            except (TypeError, ValueError):
                continue
        normalized[mapped] = value
    return normalized


def list_tools() -> dict[str, dict[str, Any]]:
    return {
        name: {
            "name": name,
            "description": spec["description"],
            "requires_approval": spec["requires_approval"],
        }
        for name, spec in TOOLS.items()
    }


def tool_requires_approval(tool_name: str) -> bool:
    spec = TOOLS.get(tool_name)
    return bool(spec and spec.get("requires_approval"))


def execute_tool(db: Session, tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Execute a registered tool and return a readable result."""
    spec = TOOLS.get(tool_name)
    if spec is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Business task '{tool_name}' is not supported.",
        )
    handler: Callable[[Session, dict[str, Any]], Any] = spec["handler"]
    args = _normalize_arguments(spec, arguments)
    try:
        result = handler(db, args)
    except HTTPException as exc:
        return {"success": False, "tool": tool_name, "message": str(exc.detail), "result": None}
    return {"success": True, "tool": tool_name, "message": f"Business task '{tool_name}' completed.", "result": result}
