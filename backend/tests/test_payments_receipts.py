"""API tests for payment tracking and automatic receipt generation."""

from __future__ import annotations

import pytest


def pay(client, headers, invoice_id, amount, method="bank_transfer", **extra):
    payload = {"invoice_id": invoice_id, "amount": amount, "method": method, **extra}
    return client.post("/api/v1/payments", headers=headers, json=payload)


class TestRecordPayment:
    def test_full_payment_settles_the_invoice(self, client, user_headers, created_invoice):
        response = pay(client, user_headers, created_invoice["id"], 100)
        assert response.status_code == 201, response.text

        invoice = client.get(f"/api/v1/invoices/{created_invoice['id']}", headers=user_headers).json()
        assert invoice["status"] == "paid"
        assert invoice["amount_paid"] == 100.0
        assert invoice["balance_due"] == 0.0

    def test_partial_payment_sets_partially_paid(self, client, user_headers, created_invoice):
        pay(client, user_headers, created_invoice["id"], "30.50")
        invoice = client.get(f"/api/v1/invoices/{created_invoice['id']}", headers=user_headers).json()
        assert invoice["status"] == "partially_paid"
        assert invoice["amount_paid"] == 30.5
        assert invoice["balance_due"] == 69.5

    def test_instalments_accumulate_and_settle(self, client, user_headers, created_invoice):
        pay(client, user_headers, created_invoice["id"], "33.33")
        pay(client, user_headers, created_invoice["id"], "33.33")
        pay(client, user_headers, created_invoice["id"], "33.34")

        invoice = client.get(f"/api/v1/invoices/{created_invoice['id']}", headers=user_headers).json()
        assert invoice["amount_paid"] == 100.0
        assert invoice["balance_due"] == 0.0
        assert invoice["status"] == "paid"

    def test_records_the_acting_user(self, client, user_headers, created_invoice):
        body = pay(client, user_headers, created_invoice["id"], 10).json()
        assert body["recorded_by"] == "user:1"

    @pytest.mark.parametrize("method", ["cash", "bank_transfer", "card", "online"])
    def test_supported_payment_methods(self, client, user_headers, created_invoice, method):
        assert pay(client, user_headers, created_invoice["id"], 5, method=method).status_code == 201

    def test_rejects_unsupported_method(self, client, user_headers, created_invoice):
        assert pay(client, user_headers, created_invoice["id"], 5, method="crypto").status_code == 422


class TestPaymentValidation:
    def test_rejects_overpayment(self, client, user_headers, created_invoice):
        response = pay(client, user_headers, created_invoice["id"], "100.01")
        assert response.status_code == 422
        assert "exceeds the outstanding balance" in response.json()["detail"]

    def test_rejects_overpayment_across_instalments(self, client, user_headers, created_invoice):
        pay(client, user_headers, created_invoice["id"], 60)
        response = pay(client, user_headers, created_invoice["id"], 50)
        assert response.status_code == 422

    @pytest.mark.parametrize("amount", [0, -10])
    def test_rejects_non_positive_amount(self, client, user_headers, created_invoice, amount):
        assert pay(client, user_headers, created_invoice["id"], amount).status_code == 422

    def test_rejects_payment_on_a_settled_invoice(self, client, user_headers, created_invoice):
        pay(client, user_headers, created_invoice["id"], 100)
        response = pay(client, user_headers, created_invoice["id"], 1)
        assert response.status_code == 409
        assert "settled in full" in response.json()["detail"]

    def test_rejects_payment_on_a_cancelled_invoice(self, client, user_headers, admin_headers, created_invoice):
        client.delete(f"/api/v1/invoices/{created_invoice['id']}", headers=admin_headers)
        assert pay(client, user_headers, created_invoice["id"], 10).status_code == 409

    def test_rejects_unknown_invoice(self, client, user_headers):
        assert pay(client, user_headers, 91234, 10).status_code == 404


class TestAutomaticReceipts:
    def test_receipt_is_issued_with_the_payment(self, client, user_headers, created_invoice):
        body = pay(client, user_headers, created_invoice["id"], 100).json()
        assert body["receipt"] is not None
        assert body["receipt"]["receipt_number"].startswith("RCT-")
        assert body["receipt"]["balance_after"] == 0.0

    def test_receipt_snapshots_the_remaining_balance(self, client, user_headers, created_invoice):
        first = pay(client, user_headers, created_invoice["id"], 40).json()
        second = pay(client, user_headers, created_invoice["id"], 60).json()
        assert first["receipt"]["balance_after"] == 60.0
        assert second["receipt"]["balance_after"] == 0.0

    def test_receipt_numbers_are_sequential(self, client, user_headers, created_invoice):
        first = pay(client, user_headers, created_invoice["id"], 10).json()
        second = pay(client, user_headers, created_invoice["id"], 10).json()
        year = first["payment_date"][:4]
        assert first["receipt"]["receipt_number"] == f"RCT-{year}-001"
        assert second["receipt"]["receipt_number"] == f"RCT-{year}-002"

    def test_receipt_traces_back_to_payment_invoice_and_customer(self, client, user_headers, created_invoice):
        payment = pay(client, user_headers, created_invoice["id"], 100).json()
        receipt_id = payment["receipt"]["id"]

        detail = client.get(f"/api/v1/receipts/{receipt_id}", headers=user_headers).json()
        assert detail["payment_id"] == payment["id"]
        assert detail["invoice_id"] == created_invoice["id"]
        assert detail["invoice_number"] == created_invoice["invoice_number"]
        assert detail["customer"]["full_name"] == "Ada Lovelace"

    def test_receipt_reachable_from_the_payment(self, client, user_headers, created_invoice):
        payment = pay(client, user_headers, created_invoice["id"], 100).json()
        response = client.get(f"/api/v1/payments/{payment['id']}/receipt", headers=user_headers)
        assert response.status_code == 200
        assert response.json()["id"] == payment["receipt"]["id"]

    def test_no_receipt_exists_when_the_payment_was_rejected(self, client, user_headers, created_invoice):
        pay(client, user_headers, created_invoice["id"], 500)  # rejected: overpayment
        assert client.get("/api/v1/receipts", headers=user_headers).json()["total"] == 0


class TestPaymentHistory:
    def test_lists_payments_for_an_invoice(self, client, user_headers, created_invoice):
        pay(client, user_headers, created_invoice["id"], 25)
        pay(client, user_headers, created_invoice["id"], 25)
        body = client.get(f"/api/v1/invoices/{created_invoice['id']}/payments", headers=user_headers).json()
        assert body["total"] == 2

    def test_filters_by_method(self, client, user_headers, created_invoice):
        pay(client, user_headers, created_invoice["id"], 25, method="cash")
        pay(client, user_headers, created_invoice["id"], 25, method="card")
        body = client.get("/api/v1/payments?method=cash", headers=user_headers).json()
        assert body["total"] == 1

    def test_payment_appears_on_the_crm_timeline(self, client, user_headers, created_invoice, customer):
        pay(client, user_headers, created_invoice["id"], 100)
        timeline = client.get(f"/api/v1/crm/customers/{customer.id}/timeline").json()
        assert any(entry["activity_type"] == "Payment Recorded" for entry in timeline)
