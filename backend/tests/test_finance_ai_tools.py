"""Finance actions exposed to the AI Executive Assistant.

The assistant does not reimplement any finance logic — it calls the same
``FinanceService`` the REST API uses, so validation, calculation and audit
behave identically whichever route a request arrives by.
"""

from __future__ import annotations

import pytest

from app.ai.orchestrator import classify_intent, detect_tool
from app.ai.tools import execute_tool, list_tools, tool_requires_approval

FINANCE_TOOLS = ["create_quotation", "create_invoice", "record_payment", "finance_summary"]


class TestToolRegistry:
    @pytest.mark.parametrize("name", FINANCE_TOOLS)
    def test_tool_is_registered(self, name):
        assert name in list_tools()

    @pytest.mark.parametrize("name", ["create_quotation", "create_invoice", "record_payment"])
    def test_write_actions_require_approval(self, name):
        assert tool_requires_approval(name) is True

    def test_read_only_summary_needs_no_approval(self):
        assert tool_requires_approval("finance_summary") is False

    def test_existing_crm_tools_are_untouched(self):
        """The Finance module extends the registry; it must not displace CRM."""
        tools = list_tools()
        for name in ("create_customer", "create_lead", "crm_summary"):
            assert name in tools


class TestIntentDetection:
    @pytest.mark.parametrize(
        "message",
        [
            "Create a quotation for customer 1 for 25 laptops",
            "Send a quote to customer 3",
            "make a quotation for 10 chairs",
        ],
    )
    def test_detects_quotation_requests(self, message):
        assert detect_tool(message) == "create_quotation"

    @pytest.mark.parametrize(
        "message",
        ["Create an invoice for customer 2", "generate a new invoice for 5 monitors"],
    )
    def test_detects_invoice_requests(self, message):
        assert detect_tool(message) == "create_invoice"

    def test_quotation_wins_over_the_generic_customer_rule(self):
        """'quotation for customer 5' must not be read as create_customer."""
        assert detect_tool("create a quotation for customer 5") == "create_quotation"

    def test_detects_payment_requests(self):
        assert detect_tool("record a payment against invoice 4") == "record_payment"

    def test_routes_money_summaries_to_finance(self):
        assert detect_tool("give me a revenue summary") == "finance_summary"

    def test_still_routes_plain_summaries_to_crm(self):
        assert detect_tool("give me a summary") == "crm_summary"

    def test_still_detects_crm_actions(self):
        assert detect_tool("add a new customer") == "create_customer"
        assert detect_tool("create a lead") == "create_lead"

    def test_classifies_finance_requests_as_business_actions(self):
        assert classify_intent("create an invoice for customer 2") == "business_action"


class TestToolExecution:
    def test_creates_a_quotation_from_flat_arguments(self, db_session, customer):
        result = execute_tool(
            db_session,
            "create_quotation",
            {"customer": str(customer.id), "product": "Laptop", "qty": "25", "price": "900"},
        )
        assert result["success"] is True
        assert result["result"]["quotation_number"].startswith("QT-")
        # 25 x 900 with no tax or discount configured
        assert result["result"]["grand_total"] == "22500.00"

    def test_creates_a_quotation_from_structured_items(self, db_session, customer):
        result = execute_tool(
            db_session,
            "create_quotation",
            {
                "customer_id": customer.id,
                "items": [
                    {"description": "Laptop", "quantity": 2, "unit_price": "899.99"},
                    {"description": "Dock", "quantity": 2, "unit_price": "149.50"},
                ],
                "tax_rate": "10",
            },
        )
        assert result["success"] is True
        # subtotal 2098.98, tax 209.90, total 2308.88
        assert result["result"]["grand_total"] == "2308.88"

    def test_creates_an_invoice(self, db_session, customer):
        result = execute_tool(
            db_session,
            "create_invoice",
            {"customer_id": customer.id, "description": "Consulting", "quantity": "3", "unit_price": "500"},
        )
        assert result["success"] is True
        assert result["result"]["invoice_number"].startswith("INV-")

    def test_records_a_payment_and_returns_the_receipt(self, db_session, customer):
        invoice = execute_tool(
            db_session,
            "create_invoice",
            {"customer_id": customer.id, "description": "Retainer", "quantity": "1", "unit_price": "400"},
        )["result"]

        result = execute_tool(
            db_session, "record_payment", {"invoice_id": invoice["id"], "amount": "400", "method": "cash"}
        )
        assert result["success"] is True
        assert result["result"]["receipt_number"].startswith("RCT-")

    def test_finance_summary_is_json_safe(self, db_session, customer):
        import json

        execute_tool(
            db_session,
            "create_invoice",
            {"customer_id": customer.id, "description": "Item", "quantity": "1", "unit_price": "100"},
        )
        result = execute_tool(db_session, "finance_summary", {})
        assert result["success"] is True
        json.dumps(result["result"])  # must not raise on Decimal values

    def test_business_rule_violations_surface_as_readable_failures(self, db_session, customer):
        """A rejected action returns success=False rather than raising."""
        result = execute_tool(
            db_session,
            "create_quotation",
            {"customer_id": customer.id, "description": "Broken", "quantity": "-5", "unit_price": "10"},
        )
        assert result["success"] is False
        assert "Quantity" in result["message"]

    def test_unknown_customer_is_reported_not_raised(self, db_session):
        result = execute_tool(
            db_session,
            "create_invoice",
            {"customer_id": 4321, "description": "x", "quantity": "1", "unit_price": "1"},
        )
        assert result["success"] is False
        assert "Customer not found" in result["message"]

    def test_ai_created_documents_are_attributed_to_the_assistant(self, db_session, customer):
        from app.models.finance import Quotation

        execute_tool(
            db_session,
            "create_quotation",
            {"customer_id": customer.id, "description": "Item", "quantity": "1", "unit_price": "10"},
        )
        quotation = db_session.query(Quotation).first()
        assert quotation.created_by == "ai-assistant"
