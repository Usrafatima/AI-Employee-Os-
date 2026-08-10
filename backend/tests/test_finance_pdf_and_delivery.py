"""PDF generation and Communication Hub delivery.

The PDFs are asserted structurally (valid file, expected pages, text present)
rather than byte-for-byte, so cosmetic template changes do not break the suite
while a genuinely broken document still fails.
"""

from __future__ import annotations

import re

import pytest

from app.services import mailer_service


def pdf_page_count(content: bytes) -> int:
    return len(re.findall(rb"/Type\s*/Page[^s]", content))


def pdf_contains(content: bytes, needle: str) -> bool:
    """Search the uncompressed portions of a PDF for a literal string.

    ReportLab compresses content streams, so this checks document metadata and
    any uncompressed objects — enough to confirm the right document was built.
    """
    return needle.encode("latin-1", errors="ignore") in content


@pytest.fixture()
def sent_emails(monkeypatch):
    """Capture outbound mail instead of sending it."""
    captured: list[dict] = []

    def fake_send(to_email, subject, body, attachments=None):
        captured.append(
            {"to": to_email, "subject": subject, "body": body, "attachments": list(attachments or [])}
        )

    monkeypatch.setattr(mailer_service, "send_email", fake_send)
    # communication_service imported the symbol directly, so patch it there too.
    from app.services import communication_service

    monkeypatch.setattr(communication_service, "send_email", fake_send)
    return captured


class TestQuotationPdf:
    def test_returns_a_valid_pdf(self, client, user_headers, quotation_payload):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        response = client.get(f"/api/v1/quotations/{created['id']}/pdf", headers=user_headers)

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert response.content.startswith(b"%PDF-")
        assert response.content.rstrip().endswith(b"%%EOF")
        assert pdf_page_count(response.content) >= 1

    def test_filename_uses_the_document_number(self, client, user_headers, quotation_payload):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        response = client.get(f"/api/v1/quotations/{created['id']}/pdf", headers=user_headers)
        assert created["quotation_number"] in response.headers["content-disposition"]

    def test_metadata_identifies_the_document(self, client, user_headers, quotation_payload):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        content = client.get(f"/api/v1/quotations/{created['id']}/pdf", headers=user_headers).content
        assert pdf_contains(content, created["quotation_number"])
        assert pdf_contains(content, "Test Company Ltd")

    def test_requires_authentication(self, client, user_headers, quotation_payload):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        assert client.get(f"/api/v1/quotations/{created['id']}/pdf").status_code == 401

    def test_unknown_quotation_returns_404(self, client, user_headers):
        assert client.get("/api/v1/quotations/5150/pdf", headers=user_headers).status_code == 404

    def test_long_documents_paginate(self, client, user_headers, customer):
        """60 line items must flow onto extra pages rather than overflow one."""
        payload = {
            "customer_id": customer.id,
            "items": [
                {"description": f"Line item number {i} with a reasonably long description",
                 "quantity": i + 1, "unit_price": "12.34"}
                for i in range(60)
            ],
            "tax_rate": 15,
        }
        created = client.post("/api/v1/quotations", headers=user_headers, json=payload).json()
        content = client.get(f"/api/v1/quotations/{created['id']}/pdf", headers=user_headers).content
        assert pdf_page_count(content) >= 2


class TestInvoiceAndReceiptPdf:
    def test_invoice_pdf(self, client, user_headers, created_invoice):
        response = client.get(f"/api/v1/invoices/{created_invoice['id']}/pdf", headers=user_headers)
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF-")
        assert pdf_contains(response.content, created_invoice["invoice_number"])

    def test_invoice_pdf_after_partial_payment(self, client, user_headers, created_invoice):
        client.post(
            "/api/v1/payments",
            headers=user_headers,
            json={"invoice_id": created_invoice["id"], "amount": 40, "method": "cash"},
        )
        response = client.get(f"/api/v1/invoices/{created_invoice['id']}/pdf", headers=user_headers)
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF-")

    def test_receipt_pdf(self, client, user_headers, created_invoice):
        payment = client.post(
            "/api/v1/payments",
            headers=user_headers,
            json={"invoice_id": created_invoice["id"], "amount": 100, "method": "card"},
        ).json()
        receipt_id = payment["receipt"]["id"]

        response = client.get(f"/api/v1/receipts/{receipt_id}/pdf", headers=user_headers)
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF-")
        assert pdf_contains(response.content, payment["receipt"]["receipt_number"])


class TestEmailDelivery:
    def test_sending_a_quotation_attaches_its_pdf(self, client, user_headers, quotation_payload, sent_emails):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        response = client.post(f"/api/v1/quotations/{created['id']}/send", headers=user_headers, json={})

        assert response.status_code == 200, response.text
        assert response.json()["sent"] is True
        assert response.json()["to_email"] == "ada@example.com"

        assert len(sent_emails) == 1
        attachments = sent_emails[0]["attachments"]
        assert len(attachments) == 1
        filename, content, mime = attachments[0]
        assert filename == f"{created['quotation_number']}.pdf"
        assert mime == "application/pdf"
        assert content.startswith(b"%PDF-")

    def test_sending_advances_a_draft_to_sent(self, client, user_headers, quotation_payload, sent_emails):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        client.post(f"/api/v1/quotations/{created['id']}/send", headers=user_headers, json={})
        refreshed = client.get(f"/api/v1/quotations/{created['id']}", headers=user_headers).json()
        assert refreshed["status"] == "sent"

    def test_resending_does_not_reset_an_accepted_quotation(self, client, user_headers, quotation_payload, sent_emails):
        created = client.post("/api/v1/quotations", headers=user_headers, json=quotation_payload).json()
        client.patch(
            f"/api/v1/quotations/{created['id']}/status", headers=user_headers, json={"status": "accepted"}
        )
        client.post(f"/api/v1/quotations/{created['id']}/send", headers=user_headers, json={})
        refreshed = client.get(f"/api/v1/quotations/{created['id']}", headers=user_headers).json()
        assert refreshed["status"] == "accepted"

    def test_sending_an_invoice_attaches_its_pdf(self, client, user_headers, created_invoice, sent_emails):
        response = client.post(f"/api/v1/invoices/{created_invoice['id']}/send", headers=user_headers, json={})
        assert response.status_code == 200
        assert sent_emails[0]["attachments"][0][0] == f"{created_invoice['invoice_number']}.pdf"

    def test_sending_a_receipt(self, client, user_headers, created_invoice, sent_emails):
        payment = client.post(
            "/api/v1/payments",
            headers=user_headers,
            json={"invoice_id": created_invoice["id"], "amount": 100, "method": "online"},
        ).json()
        response = client.post(
            f"/api/v1/receipts/{payment['receipt']['id']}/send", headers=user_headers, json={}
        )
        assert response.status_code == 200
        assert "settled in full" in sent_emails[0]["body"]

    def test_recipient_can_be_overridden(self, client, user_headers, created_invoice, sent_emails):
        client.post(
            f"/api/v1/invoices/{created_invoice['id']}/send",
            headers=user_headers,
            json={"to_email": "accounts@customer.example", "subject": "Your invoice"},
        )
        assert sent_emails[0]["to"] == "accounts@customer.example"
        assert sent_emails[0]["subject"] == "Your invoice"

    def test_send_is_recorded_in_the_communication_email_log(self, client, user_headers, created_invoice, sent_emails):
        client.post(f"/api/v1/invoices/{created_invoice['id']}/send", headers=user_headers, json={})
        response = client.get("/api/v1/communication/email/history")
        assert response.status_code == 200, response.text
        history = response.json()
        assert any(created_invoice["invoice_number"] in (entry["subject"] or "") for entry in history)
        assert all(entry["status"] == "sent" for entry in history)

    def test_cancelled_invoice_cannot_be_sent(self, client, user_headers, admin_headers, created_invoice, sent_emails):
        client.delete(f"/api/v1/invoices/{created_invoice['id']}", headers=admin_headers)
        response = client.post(f"/api/v1/invoices/{created_invoice['id']}/send", headers=user_headers, json={})
        assert response.status_code == 409
        assert sent_emails == []


class TestPdfLayoutRegressions:
    """Guards for layout defects found during visual QA."""

    def test_rate_labels_drop_trailing_zeros(self):
        """A stored rate of 17.000 must print as 'Tax (17%)', not 'Tax (17.000%)'."""
        from decimal import Decimal

        from app.services.finance_pdf_service import _fmt_rate

        assert _fmt_rate(Decimal("17.000")) == "17"
        assert _fmt_rate(Decimal("17.500")) == "17.5"
        assert _fmt_rate(Decimal("0.000")) == "0"
        assert _fmt_rate(Decimal("2.250")) == "2.25"
        assert _fmt_rate(None) == "0"

    def test_receipt_banner_lines_do_not_overlap(self, client, user_headers, created_invoice):
        """The amount banner uses two paragraphs; their leading must clear the font size.

        A single paragraph with <br/> applied one leading to both lines, which
        made the 22pt amount collide with its label.
        """
        from app.services.finance_pdf_service import _styles

        styles = _styles()
        assert styles["banner_amount"].leading > styles["banner_amount"].fontSize
        assert styles["banner_label"].leading > styles["banner_label"].fontSize

        payment = client.post(
            "/api/v1/payments",
            headers=user_headers,
            json={"invoice_id": created_invoice["id"], "amount": 100, "method": "cash"},
        ).json()
        response = client.get(
            f"/api/v1/receipts/{payment['receipt']['id']}/pdf", headers=user_headers
        )
        assert response.status_code == 200
        assert response.content.startswith(b"%PDF-")

    def test_status_chip_is_sized_to_its_text(self):
        """Without an explicit width the chip expands to fill its parent cell."""
        from app.services.finance_pdf_service import CONTENT_WIDTH, _status_chip, _styles

        styles = _styles()
        narrow = _status_chip("draft", styles)._argW[0]
        wide = _status_chip("partially_paid", styles)._argW[0]
        assert narrow < wide < CONTENT_WIDTH / 2


class TestMailerAttachments:
    def test_dry_run_logs_instead_of_sending(self, caplog):
        """With no SMTP configured the mailer must not attempt a connection."""
        import logging

        with caplog.at_level(logging.INFO):
            mailer_service.send_email(
                "someone@example.com", "Subject", "Body", attachments=[("a.pdf", b"%PDF-", "application/pdf")]
            )
        assert "MAILER DRY RUN" in caplog.text
        assert "a.pdf" in caplog.text
