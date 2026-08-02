"""create crm tables

Revision ID: f8a9b3c8d4e1
Revises: 24098b49f088
Create Date: 2026-08-02 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f8a9b3c8d4e1"
down_revision = "24098b49f088"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("company_name", sa.String(length=150), nullable=True),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("industry", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("email", name="uq_customer_email"),
    )
    op.create_index(op.f("ix_customers_email"), "customers", ["email"], unique=True)
    op.create_index(op.f("ix_customers_full_name"), "customers", ["full_name"], unique=False)
    op.create_index(op.f("ix_customers_company_name"), "customers", ["company_name"], unique=False)
    op.create_index(op.f("ix_customers_status"), "customers", ["status"], unique=False)
    op.create_index(op.f("ix_customers_id"), "customers", ["id"], unique=False)

    op.create_table(
        "leads",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("assigned_to", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="new"),
        sa.Column("expected_value", sa.Float(), nullable=True),
        sa.Column("probability", sa.Integer(), nullable=True),
        sa.Column("next_followup_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_leads_id"), "leads", ["id"], unique=False)
    op.create_index(op.f("ix_leads_customer_id"), "leads", ["customer_id"], unique=False)
    op.create_index(op.f("ix_leads_title"), "leads", ["title"], unique=False)
    op.create_index(op.f("ix_leads_source"), "leads", ["source"], unique=False)
    op.create_index(op.f("ix_leads_assigned_to"), "leads", ["assigned_to"], unique=False)
    op.create_index(op.f("ix_leads_status"), "leads", ["status"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sender", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("ai_response", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_conversations_id"), "conversations", ["id"], unique=False)
    op.create_index(op.f("ix_conversations_customer_id"), "conversations", ["customer_id"], unique=False)
    op.create_index(op.f("ix_conversations_sender"), "conversations", ["sender"], unique=False)
    op.create_index(op.f("ix_conversations_created_at"), "conversations", ["created_at"], unique=False)

    op.create_table(
        "activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("activity_type", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_activity_logs_id"), "activity_logs", ["id"], unique=False)
    op.create_index(op.f("ix_activity_logs_customer_id"), "activity_logs", ["customer_id"], unique=False)
    op.create_index(op.f("ix_activity_logs_activity_type"), "activity_logs", ["activity_type"], unique=False)
    op.create_index(op.f("ix_activity_logs_created_at"), "activity_logs", ["created_at"], unique=False)

    op.create_table(
        "crm_updates",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("last_activity", sa.String(length=200), nullable=True),
        sa.Column("last_contact_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_followup_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_updated_by", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_crm_updates_id"), "crm_updates", ["id"], unique=False)
    op.create_index(op.f("ix_crm_updates_customer_id"), "crm_updates", ["customer_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_crm_updates_customer_id"), table_name="crm_updates")
    op.drop_index(op.f("ix_crm_updates_id"), table_name="crm_updates")
    op.drop_table("crm_updates")

    op.drop_index(op.f("ix_activity_logs_created_at"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_activity_type"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_customer_id"), table_name="activity_logs")
    op.drop_index(op.f("ix_activity_logs_id"), table_name="activity_logs")
    op.drop_table("activity_logs")

    op.drop_index(op.f("ix_conversations_created_at"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_sender"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_customer_id"), table_name="conversations")
    op.drop_index(op.f("ix_conversations_id"), table_name="conversations")
    op.drop_table("conversations")

    op.drop_index(op.f("ix_leads_status"), table_name="leads")
    op.drop_index(op.f("ix_leads_assigned_to"), table_name="leads")
    op.drop_index(op.f("ix_leads_source"), table_name="leads")
    op.drop_index(op.f("ix_leads_title"), table_name="leads")
    op.drop_index(op.f("ix_leads_customer_id"), table_name="leads")
    op.drop_index(op.f("ix_leads_id"), table_name="leads")
    op.drop_table("leads")

    op.drop_index(op.f("ix_customers_status"), table_name="customers")
    op.drop_index(op.f("ix_customers_company_name"), table_name="customers")
    op.drop_index(op.f("ix_customers_full_name"), table_name="customers")
    op.drop_index(op.f("ix_customers_email"), table_name="customers")
    op.drop_index(op.f("ix_customers_id"), table_name="customers")
    op.drop_table("customers")
