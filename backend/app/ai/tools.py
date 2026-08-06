from __future__ import annotations

from typing import Any, Callable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.services.crm_service import CRMService


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
