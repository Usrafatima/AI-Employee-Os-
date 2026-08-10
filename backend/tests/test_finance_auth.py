"""Authentication and role-based access control on finance endpoints.

Tokens are minted with the same secret and algorithm the Authentication module
uses, so these tests exercise the real verification path rather than a stub.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import ALGORITHM

PROTECTED_READS = [
    "/api/v1/quotations",
    "/api/v1/invoices",
    "/api/v1/payments",
    "/api/v1/receipts",
    "/api/v1/finance/summary",
]


def token(claims: dict, *, secret: str | None = None) -> str:
    payload = {"exp": datetime.now(timezone.utc) + timedelta(minutes=30), **claims}
    return jwt.encode(payload, secret or settings.SECRET_KEY, algorithm=ALGORITHM)


class TestAuthenticationRequired:
    @pytest.mark.parametrize("path", PROTECTED_READS)
    def test_rejects_anonymous_requests(self, client, path):
        assert client.get(path).status_code == 401

    def test_rejects_anonymous_writes(self, client, customer):
        response = client.post(
            "/api/v1/quotations",
            json={"customer_id": customer.id, "items": [{"description": "x", "quantity": 1, "unit_price": 1}]},
        )
        assert response.status_code == 401

    def test_rejects_a_garbage_token(self, client):
        response = client.get("/api/v1/quotations", headers={"Authorization": "Bearer not-a-jwt"})
        assert response.status_code == 401

    def test_rejects_a_token_signed_with_the_wrong_secret(self, client):
        forged = token({"sub": "1", "role": "admin"}, secret="a-different-secret")
        response = client.get("/api/v1/quotations", headers={"Authorization": f"Bearer {forged}"})
        assert response.status_code == 401

    def test_rejects_an_expired_token(self, client):
        expired = jwt.encode(
            {"sub": "1", "role": "admin", "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )
        response = client.get("/api/v1/quotations", headers={"Authorization": f"Bearer {expired}"})
        assert response.status_code == 401

    def test_rejects_a_token_without_a_subject(self, client):
        response = client.get(
            "/api/v1/quotations", headers={"Authorization": f"Bearer {token({'role': 'admin'})}"}
        )
        assert response.status_code == 401

    def test_health_endpoints_stay_public(self, client):
        assert client.get("/api/v1/finance/health").status_code == 200
        assert client.get("/api/v1/quotations/health").status_code == 200


class TestRoleBasedAccess:
    def test_regular_user_cannot_cancel_a_quotation(self, client, user_headers, quotation_payload):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        response = client.delete(f"/api/v1/quotations/{created['id']}", headers=user_headers)
        assert response.status_code == 403
        assert "admin" in response.json()["detail"].lower()

    def test_regular_user_cannot_cancel_an_invoice(self, client, user_headers, created_invoice):
        response = client.delete(f"/api/v1/invoices/{created_invoice['id']}", headers=user_headers)
        assert response.status_code == 403

    def test_admin_can_cancel(self, client, user_headers, admin_headers, quotation_payload):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        assert client.delete(f"/api/v1/quotations/{created['id']}", headers=admin_headers).status_code == 200

    def test_regular_user_can_perform_normal_finance_work(self, client, user_headers, quotation_payload):
        assert client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).status_code == 201

    def test_token_without_a_role_claim_is_not_admin(self, client, customer, quotation_payload):
        """Tokens minted before roles were added must not gain admin rights."""
        headers = {"Authorization": f"Bearer {token({'sub': '7'})}"}
        created = client.post("/api/v1/quotations", headers=headers, json=quotation_payload).json()
        assert client.delete(f"/api/v1/quotations/{created['id']}", headers=headers).status_code == 403

    def test_unrecognised_role_is_not_admin(self, client, quotation_payload):
        headers = {"Authorization": f"Bearer {token({'sub': '8', 'role': 'superuser'})}"}
        created = client.post("/api/v1/quotations", headers=headers, json=quotation_payload).json()
        assert client.delete(f"/api/v1/quotations/{created['id']}", headers=headers).status_code == 403

    def test_role_matching_is_case_insensitive(self, client, quotation_payload):
        headers = {"Authorization": f"Bearer {token({'sub': '9', 'role': 'Admin'})}"}
        created = client.post("/api/v1/quotations", headers=headers, json=quotation_payload).json()
        assert client.delete(f"/api/v1/quotations/{created['id']}", headers=headers).status_code == 200


class TestPrototypeFallback:
    """AUTH_REQUIRED=false allows anonymous access for local demos.

    It must never grant admin rights, and must still reject a bad token.
    """

    @pytest.fixture(autouse=True)
    def _relax_auth(self, monkeypatch):
        monkeypatch.setattr(settings, "AUTH_REQUIRED", False)

    def test_anonymous_read_is_allowed(self, client):
        assert client.get("/api/v1/quotations").status_code == 200

    def test_anonymous_caller_is_never_admin(self, client, quotation_payload):
        created = client.post("/api/v1/quotations", json=quotation_payload).json()
        assert client.delete(f"/api/v1/quotations/{created['id']}").status_code == 403

    def test_an_invalid_token_is_still_rejected(self, client):
        response = client.get("/api/v1/quotations", headers={"Authorization": "Bearer bad-token"})
        assert response.status_code == 401
