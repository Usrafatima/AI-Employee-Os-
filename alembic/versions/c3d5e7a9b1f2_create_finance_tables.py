"""create finance tables

Quotations, quotation items, invoices, invoice items, payments and receipts
for the Finance module.

Chained onto the AI tables revision, which follows the CRM revision, because
quotations and invoices carry foreign keys to ``customers``.

Revision ID: c3d5e7a9b1f2
Revises: a1b2c3d4e5f6
Create Date: 2026-08-09 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c3d5e7a9b1f2"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


MONEY = sa.Numeric(14, 2)
QUANTITY = sa.Numeric(12, 3)
RATE = sa.Numeric(6, 3)


def upgrade() -> None:
    op.create_table(
        "quotations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("quotation_number", sa.String(length=30), nullable=False),
        sa.Column("sequence_year", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("discount_type", sa.String(length=20), nullable=False, server_default="percentage"),
        sa.Column("discount_value", MONEY, nullable=False, server_default="0"),
        sa.Column("tax_rate", RATE, nullable=False, server_default="0"),
        sa.Column("subtotal", MONEY, nullable=False, server_default="0"),
        sa.Column("discount_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("tax_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("grand_total", MONEY, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("terms", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("quotation_number", name="uq_quotation_number"),
        sa.UniqueConstraint("sequence_year", "sequence_number", name="uq_quotation_sequence"),
    )
    op.create_index(op.f("ix_quotations_id"), "quotations", ["id"], unique=False)
    op.create_index(op.f("ix_quotations_quotation_number"), "quotations", ["quotation_number"], unique=True)
    op.create_index(op.f("ix_quotations_sequence_year"), "quotations", ["sequence_year"], unique=False)
    op.create_index(op.f("ix_quotations_customer_id"), "quotations", ["customer_id"], unique=False)
    op.create_index(op.f("ix_quotations_status"), "quotations", ["status"], unique=False)
    op.create_index(op.f("ix_quotations_created_by"), "quotations", ["created_by"], unique=False)
    op.create_index("ix_quotation_customer_status", "quotations", ["customer_id", "status"], unique=False)
    op.create_index("ix_quotation_issue_date", "quotations", ["issue_date"], unique=False)

    op.create_table(
        "quotation_items",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("quotation_id", sa.Integer(), sa.ForeignKey("quotations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", QUANTITY, nullable=False),
        sa.Column("unit_price", MONEY, nullable=False),
        sa.Column("line_total", MONEY, nullable=False),
    )
    op.create_index(op.f("ix_quotation_items_id"), "quotation_items", ["id"], unique=False)
    op.create_index(op.f("ix_quotation_items_quotation_id"), "quotation_items", ["quotation_id"], unique=False)
    op.create_index("ix_quotation_item_quotation", "quotation_items", ["quotation_id", "position"], unique=False)

    op.create_table(
        "invoices",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("invoice_number", sa.String(length=30), nullable=False),
        sa.Column("sequence_year", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("quotation_id", sa.Integer(), sa.ForeignKey("quotations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="draft"),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("currency", sa.String(length=3), nullable=False, server_default="USD"),
        sa.Column("discount_type", sa.String(length=20), nullable=False, server_default="percentage"),
        sa.Column("discount_value", MONEY, nullable=False, server_default="0"),
        sa.Column("tax_rate", RATE, nullable=False, server_default="0"),
        sa.Column("subtotal", MONEY, nullable=False, server_default="0"),
        sa.Column("discount_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("tax_amount", MONEY, nullable=False, server_default="0"),
        sa.Column("grand_total", MONEY, nullable=False, server_default="0"),
        sa.Column("amount_paid", MONEY, nullable=False, server_default="0"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("terms", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("invoice_number", name="uq_invoice_number"),
        sa.UniqueConstraint("sequence_year", "sequence_number", name="uq_invoice_sequence"),
    )
    op.create_index(op.f("ix_invoices_id"), "invoices", ["id"], unique=False)
    op.create_index(op.f("ix_invoices_invoice_number"), "invoices", ["invoice_number"], unique=True)
    op.create_index(op.f("ix_invoices_sequence_year"), "invoices", ["sequence_year"], unique=False)
    op.create_index(op.f("ix_invoices_customer_id"), "invoices", ["customer_id"], unique=False)
    op.create_index(op.f("ix_invoices_quotation_id"), "invoices", ["quotation_id"], unique=False)
    op.create_index(op.f("ix_invoices_status"), "invoices", ["status"], unique=False)
    op.create_index(op.f("ix_invoices_created_by"), "invoices", ["created_by"], unique=False)
    op.create_index("ix_invoice_customer_status", "invoices", ["customer_id", "status"], unique=False)
    op.create_index("ix_invoice_issue_date", "invoices", ["issue_date"], unique=False)
    op.create_index("ix_invoice_due_date", "invoices", ["due_date"], unique=False)

    op.create_table(
        "invoice_items",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("quantity", QUANTITY, nullable=False),
        sa.Column("unit_price", MONEY, nullable=False),
        sa.Column("line_total", MONEY, nullable=False),
    )
    op.create_index(op.f("ix_invoice_items_id"), "invoice_items", ["id"], unique=False)
    op.create_index(op.f("ix_invoice_items_invoice_id"), "invoice_items", ["invoice_id"], unique=False)
    op.create_index("ix_invoice_item_invoice", "invoice_items", ["invoice_id", "position"], unique=False)

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("invoice_id", sa.Integer(), sa.ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount", MONEY, nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False),
        sa.Column("reference", sa.String(length=120), nullable=True),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_payments_id"), "payments", ["id"], unique=False)
    op.create_index(op.f("ix_payments_invoice_id"), "payments", ["invoice_id"], unique=False)
    op.create_index(op.f("ix_payments_method"), "payments", ["method"], unique=False)
    op.create_index(op.f("ix_payments_payment_date"), "payments", ["payment_date"], unique=False)
    op.create_index(op.f("ix_payments_recorded_by"), "payments", ["recorded_by"], unique=False)
    op.create_index("ix_payment_invoice_date", "payments", ["invoice_id", "payment_date"], unique=False)
    op.create_index("ix_payment_method", "payments", ["method"], unique=False)

    op.create_table(
        "receipts",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("receipt_number", sa.String(length=30), nullable=False),
        sa.Column("sequence_year", sa.Integer(), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("balance_after", MONEY, nullable=False, server_default="0"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("receipt_number", name="uq_receipt_number"),
        sa.UniqueConstraint("sequence_year", "sequence_number", name="uq_receipt_sequence"),
        sa.UniqueConstraint("payment_id", name="uq_receipt_payment"),
    )
    op.create_index(op.f("ix_receipts_id"), "receipts", ["id"], unique=False)
    op.create_index(op.f("ix_receipts_receipt_number"), "receipts", ["receipt_number"], unique=True)
    op.create_index(op.f("ix_receipts_sequence_year"), "receipts", ["sequence_year"], unique=False)
    op.create_index(op.f("ix_receipts_payment_id"), "receipts", ["payment_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_receipts_payment_id"), table_name="receipts")
    op.drop_index(op.f("ix_receipts_sequence_year"), table_name="receipts")
    op.drop_index(op.f("ix_receipts_receipt_number"), table_name="receipts")
    op.drop_index(op.f("ix_receipts_id"), table_name="receipts")
    op.drop_table("receipts")

    op.drop_index("ix_payment_method", table_name="payments")
    op.drop_index("ix_payment_invoice_date", table_name="payments")
    op.drop_index(op.f("ix_payments_recorded_by"), table_name="payments")
    op.drop_index(op.f("ix_payments_payment_date"), table_name="payments")
    op.drop_index(op.f("ix_payments_method"), table_name="payments")
    op.drop_index(op.f("ix_payments_invoice_id"), table_name="payments")
    op.drop_index(op.f("ix_payments_id"), table_name="payments")
    op.drop_table("payments")

    op.drop_index("ix_invoice_item_invoice", table_name="invoice_items")
    op.drop_index(op.f("ix_invoice_items_invoice_id"), table_name="invoice_items")
    op.drop_index(op.f("ix_invoice_items_id"), table_name="invoice_items")
    op.drop_table("invoice_items")

    op.drop_index("ix_invoice_due_date", table_name="invoices")
    op.drop_index("ix_invoice_issue_date", table_name="invoices")
    op.drop_index("ix_invoice_customer_status", table_name="invoices")
    op.drop_index(op.f("ix_invoices_created_by"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_status"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_quotation_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_customer_id"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_sequence_year"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_invoice_number"), table_name="invoices")
    op.drop_index(op.f("ix_invoices_id"), table_name="invoices")
    op.drop_table("invoices")

    op.drop_index("ix_quotation_item_quotation", table_name="quotation_items")
    op.drop_index(op.f("ix_quotation_items_quotation_id"), table_name="quotation_items")
    op.drop_index(op.f("ix_quotation_items_id"), table_name="quotation_items")
    op.drop_table("quotation_items")

    op.drop_index("ix_quotation_issue_date", table_name="quotations")
    op.drop_index("ix_quotation_customer_status", table_name="quotations")
    op.drop_index(op.f("ix_quotations_created_by"), table_name="quotations")
    op.drop_index(op.f("ix_quotations_status"), table_name="quotations")
    op.drop_index(op.f("ix_quotations_customer_id"), table_name="quotations")
    op.drop_index(op.f("ix_quotations_sequence_year"), table_name="quotations")
    op.drop_index(op.f("ix_quotations_quotation_number"), table_name="quotations")
    op.drop_index(op.f("ix_quotations_id"), table_name="quotations")
    op.drop_table("quotations")
