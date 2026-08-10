"""API tests for the invoice lifecycle, including quotation conversion."""

from __future__ import annotations

import pytest


@pytest.fixture()
def quotation(client, user_headers, quotation_payload):
    return client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()


class TestCreateInvoice:
    def test_creates_directly_without_a_quotation(self, client, user_headers, customer):
        """The supervisor confirmed invoices may be raised without a quotation."""
        response = client.post(
            "/api/v1/invoices",
            headers=user_headers,
            json={
                "customer_id": customer.id,
                "items": [{"description": "Support retainer", "quantity": 2, "unit_price": "250.00"}],
                "discount_value": 0,
                "tax_rate": 10,
            },
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["subtotal"] == 500.0
        assert body["tax_amount"] == 50.0
        assert body["grand_total"] == 550.0
        assert body["quotation_id"] is None
        assert body["amount_paid"] == 0.0
        assert body["balance_due"] == 550.0

    def test_numbering_uses_the_invoice_prefix(self, client, user_headers, created_invoice):
        year = created_invoice["issue_date"][:4]
        assert created_invoice["invoice_number"] == f"INV-{year}-001"

    def test_rejects_unknown_customer(self, client, user_headers):
        response = client.post(
            "/api/v1/invoices",
            headers=user_headers,
            json={"customer_id": 98765, "items": [{"description": "x", "quantity": 1, "unit_price": 1}]},
        )
        assert response.status_code == 404


class TestConvertQuotationToInvoice:
    def test_copies_items_and_totals(self, client, user_headers, quotation):
        response = client.post(f"/api/v1/quotations/{quotation['id']}/invoice", headers=user_headers)
        assert response.status_code == 201, response.text
        invoice = response.json()

        assert invoice["quotation_id"] == quotation["id"]
        assert invoice["subtotal"] == quotation["subtotal"]
        assert invoice["discount_amount"] == quotation["discount_amount"]
        assert invoice["tax_amount"] == quotation["tax_amount"]
        assert invoice["grand_total"] == quotation["grand_total"]
        assert len(invoice["items"]) == len(quotation["items"])

    def test_marks_the_quotation_converted(self, client, user_headers, quotation):
        client.post(f"/api/v1/quotations/{quotation['id']}/invoice", headers=user_headers)
        refreshed = client.get(f"/api/v1/quotations/{quotation['id']}", headers=user_headers).json()
        assert refreshed["status"] == "converted"

    def test_cannot_invoice_the_same_quotation_twice(self, client, user_headers, quotation):
        client.post(f"/api/v1/quotations/{quotation['id']}/invoice", headers=user_headers)
        response = client.post(f"/api/v1/quotations/{quotation['id']}/invoice", headers=user_headers)
        assert response.status_code == 409
        assert "already been invoiced" in response.json()["detail"]

    def test_cannot_invoice_a_cancelled_quotation(self, client, user_headers, admin_headers, quotation):
        client.delete(f"/api/v1/quotations/{quotation['id']}", headers=admin_headers)
        response = client.post(f"/api/v1/quotations/{quotation['id']}/invoice", headers=user_headers)
        assert response.status_code == 409

    def test_converted_quotation_cannot_be_edited(self, client, user_headers, quotation):
        client.post(f"/api/v1/quotations/{quotation['id']}/invoice", headers=user_headers)
        response = client.patch(
            f"/api/v1/quotations/{quotation['id']}", headers=user_headers, json={"tax_rate": 0}
        )
        assert response.status_code == 409


class TestUpdateInvoice:
    def test_recalculates_on_item_change(self, client, user_headers, created_invoice):
        body = client.patch(
            f"/api/v1/invoices/{created_invoice['id']}",
            headers=user_headers,
            json={"items": [{"description": "Revised", "quantity": 3, "unit_price": "10.00"}]},
        ).json()
        assert body["grand_total"] == 30.0

    def test_locked_once_a_payment_exists(self, client, user_headers, created_invoice):
        client.post(
            "/api/v1/payments",
            headers=user_headers,
            json={"invoice_id": created_invoice["id"], "amount": 10, "method": "cash"},
        )
        response = client.patch(
            f"/api/v1/invoices/{created_invoice['id']}", headers=user_headers, json={"tax_rate": 5}
        )
        assert response.status_code == 409
        assert "payments" in response.json()["detail"]


class TestInvoiceStatus:
    def test_marks_as_sent(self, client, user_headers, created_invoice):
        body = client.patch(
            f"/api/v1/invoices/{created_invoice['id']}/status",
            headers=user_headers,
            json={"status": "sent"},
        ).json()
        assert body["status"] == "sent"

    def test_cannot_mark_paid_by_hand(self, client, user_headers, created_invoice):
        """Payment status must be backed by a real payment record."""
        response = client.patch(
            f"/api/v1/invoices/{created_invoice['id']}/status",
            headers=user_headers,
            json={"status": "paid"},
        )
        assert response.status_code == 400
        assert "Record a payment" in response.json()["detail"]


class TestCancelInvoice:
    def test_admin_can_cancel_an_unpaid_invoice(self, client, admin_headers, created_invoice):
        response = client.delete(f"/api/v1/invoices/{created_invoice['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cannot_cancel_an_invoice_with_payments(self, client, user_headers, admin_headers, created_invoice):
        client.post(
            "/api/v1/payments",
            headers=user_headers,
            json={"invoice_id": created_invoice["id"], "amount": 25, "method": "card"},
        )
        response = client.delete(f"/api/v1/invoices/{created_invoice['id']}", headers=admin_headers)
        assert response.status_code == 409


class TestFinanceSummary:
    def test_reports_totals_and_outstanding(self, client, user_headers, created_invoice):
        client.post(
            "/api/v1/payments",
            headers=user_headers,
            json={"invoice_id": created_invoice["id"], "amount": 40, "method": "bank_transfer"},
        )
        summary = client.get("/api/v1/finance/summary", headers=user_headers).json()

        assert summary["total_invoices"] == 1
        assert summary["total_invoiced_value"] == 100.0
        assert summary["total_collected"] == 40.0
        assert summary["total_outstanding"] == 60.0
        assert summary["partially_paid_invoices"] == 1
        assert summary["currency"] == "USD"

    def test_excludes_cancelled_invoices_from_revenue(self, client, admin_headers, user_headers, created_invoice):
        client.delete(f"/api/v1/invoices/{created_invoice['id']}", headers=admin_headers)
        summary = client.get("/api/v1/finance/summary", headers=user_headers).json()
        assert summary["total_invoiced_value"] == 0.0
