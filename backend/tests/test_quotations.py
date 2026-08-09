"""API tests for the quotation lifecycle."""

from __future__ import annotations

import pytest


def create_quotation(client, headers, payload):
    return client.post("/api/v1/quotations", headers=headers, json=payload)


class TestCreateQuotation:
    def test_creates_with_server_calculated_totals(self, client, user_headers, quotation_payload):
        response = create_quotation(client, user_headers, quotation_payload)
        assert response.status_code == 201, response.text
        body = response.json()

        assert body["subtotal"] == 60.17
        assert body["discount_amount"] == 6.02
        assert body["tax_amount"] == 10.83
        assert body["grand_total"] == 64.98
        assert body["status"] == "draft"
        assert len(body["items"]) == 2
        assert body["items"][0]["line_total"] == 59.97

    def test_assigns_sequential_numbers(self, client, user_headers, quotation_payload):
        first = create_quotation(client, user_headers, quotation_payload).json()
        second = create_quotation(client, user_headers, quotation_payload).json()

        year = first["issue_date"][:4]
        assert first["quotation_number"] == f"QT-{year}-001"
        assert second["quotation_number"] == f"QT-{year}-002"

    def test_embeds_crm_customer_details(self, client, user_headers, quotation_payload, customer):
        body = create_quotation(client, user_headers, quotation_payload).json()
        assert body["customer"]["id"] == customer.id
        assert body["customer"]["full_name"] == "Ada Lovelace"
        assert body["customer"]["email"] == "ada@example.com"

    def test_records_the_acting_user(self, client, user_headers, quotation_payload):
        body = create_quotation(client, user_headers, quotation_payload).json()
        assert body["created_by"] == "user:1"

    def test_appears_on_the_crm_customer_timeline(self, client, user_headers, quotation_payload, customer):
        create_quotation(client, user_headers, quotation_payload)
        timeline = client.get(f"/api/v1/crm/customers/{customer.id}/timeline").json()
        assert any(entry["activity_type"] == "Quotation Created" for entry in timeline)


class TestQuotationValidation:
    def test_rejects_unknown_customer(self, client, user_headers, quotation_payload):
        quotation_payload["customer_id"] = 99999
        response = create_quotation(client, user_headers, quotation_payload)
        assert response.status_code == 404

    def test_rejects_soft_deleted_customer(self, client, user_headers, quotation_payload, customer):
        client.delete(f"/api/v1/crm/customers/{customer.id}")
        response = create_quotation(client, user_headers, quotation_payload)
        assert response.status_code == 404

    def test_rejects_empty_item_list(self, client, user_headers, quotation_payload):
        quotation_payload["items"] = []
        assert create_quotation(client, user_headers, quotation_payload).status_code == 422

    @pytest.mark.parametrize("quantity", [0, -3])
    def test_rejects_invalid_quantity(self, client, user_headers, quotation_payload, quantity):
        quotation_payload["items"] = [{"description": "x", "quantity": quantity, "unit_price": 10}]
        assert create_quotation(client, user_headers, quotation_payload).status_code == 422

    def test_rejects_negative_price(self, client, user_headers, quotation_payload):
        quotation_payload["items"] = [{"description": "x", "quantity": 1, "unit_price": -10}]
        assert create_quotation(client, user_headers, quotation_payload).status_code == 422

    @pytest.mark.parametrize("tax_rate", [-1, 101])
    def test_rejects_invalid_tax_rate(self, client, user_headers, quotation_payload, tax_rate):
        quotation_payload["tax_rate"] = tax_rate
        assert create_quotation(client, user_headers, quotation_payload).status_code == 422

    def test_rejects_fixed_discount_above_subtotal(self, client, user_headers, quotation_payload):
        quotation_payload["discount_type"] = "fixed"
        quotation_payload["discount_value"] = 10000
        response = create_quotation(client, user_headers, quotation_payload)
        assert response.status_code == 422
        assert "subtotal" in response.json()["detail"]

    def test_ignores_client_supplied_totals(self, client, user_headers, quotation_payload):
        """A client cannot dictate the amounts; the server recalculates them."""
        quotation_payload["grand_total"] = 1
        quotation_payload["subtotal"] = 1
        body = create_quotation(client, user_headers, quotation_payload).json()
        assert body["grand_total"] == 64.98


class TestReadQuotations:
    def test_lists_with_pagination_envelope(self, client, user_headers, quotation_payload):
        create_quotation(client, user_headers, quotation_payload)
        body = client.get("/api/v1/quotations", headers=user_headers).json()
        assert body["total"] == 1
        assert body["page"] == 1
        assert body["total_pages"] == 1
        assert len(body["items"]) == 1

    def test_filters_by_status(self, client, user_headers, quotation_payload):
        create_quotation(client, user_headers, quotation_payload)
        assert client.get("/api/v1/quotations?status=draft", headers=user_headers).json()["total"] == 1
        assert client.get("/api/v1/quotations?status=accepted", headers=user_headers).json()["total"] == 0

    def test_get_returns_line_items(self, client, user_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        body = client.get(f"/api/v1/quotations/{created['id']}", headers=user_headers).json()
        assert len(body["items"]) == 2

    def test_unknown_id_returns_404(self, client, user_headers):
        assert client.get("/api/v1/quotations/4242", headers=user_headers).status_code == 404


class TestUpdateQuotation:
    def test_replacing_items_recalculates_totals(self, client, user_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        response = client.patch(
            f"/api/v1/quotations/{created['id']}",
            headers=user_headers,
            json={"items": [{"description": "Rewritten", "quantity": 1, "unit_price": 50}], "discount_value": 0, "tax_rate": 0},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["grand_total"] == 50.0
        assert len(body["items"]) == 1

    def test_changing_only_tax_reuses_stored_items(self, client, user_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        body = client.patch(
            f"/api/v1/quotations/{created['id']}", headers=user_headers, json={"tax_rate": 0}
        ).json()
        assert body["tax_amount"] == 0.0
        assert body["subtotal"] == 60.17
        assert body["grand_total"] == 54.15


class TestQuotationStatus:
    def test_marks_as_sent(self, client, user_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        body = client.patch(
            f"/api/v1/quotations/{created['id']}/status", headers=user_headers, json={"status": "sent"}
        ).json()
        assert body["status"] == "sent"
        assert body["sent_at"] is not None

    def test_cannot_set_converted_directly(self, client, user_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        response = client.patch(
            f"/api/v1/quotations/{created['id']}/status",
            headers=user_headers,
            json={"status": "converted"},
        )
        assert response.status_code == 400

    def test_rejects_unknown_status(self, client, user_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        response = client.patch(
            f"/api/v1/quotations/{created['id']}/status", headers=user_headers, json={"status": "banana"}
        )
        assert response.status_code == 422


class TestCancelQuotation:
    def test_admin_can_cancel(self, client, user_headers, admin_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        response = client.delete(f"/api/v1/quotations/{created['id']}", headers=admin_headers)
        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    def test_cancelled_quotation_is_archived_not_deleted(self, client, user_headers, admin_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        client.delete(f"/api/v1/quotations/{created['id']}", headers=admin_headers)
        assert client.get(f"/api/v1/quotations/{created['id']}", headers=user_headers).status_code == 200

    def test_cancelled_quotation_cannot_be_edited(self, client, user_headers, admin_headers, quotation_payload):
        created = create_quotation(client, user_headers, quotation_payload).json()
        client.delete(f"/api/v1/quotations/{created['id']}", headers=admin_headers)
        response = client.patch(
            f"/api/v1/quotations/{created['id']}", headers=user_headers, json={"tax_rate": 5}
        )
        assert response.status_code == 409
