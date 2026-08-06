"""create ai tables

Revision ID: a1b2c3d4e5f6
Revises: f8a9b3c8d4e1
Create Date: 2026-08-05 00:00:00.000000

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "f8a9b3c8d4e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=150), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_ai_conversations_id"), "ai_conversations", ["id"], unique=False)
    op.create_index(op.f("ix_ai_conversations_created_at"), "ai_conversations", ["created_at"], unique=False)

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("ai_conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_ai_messages_id"), "ai_messages", ["id"], unique=False)
    op.create_index(op.f("ix_ai_messages_conversation_id"), "ai_messages", ["conversation_id"], unique=False)
    op.create_index(op.f("ix_ai_messages_role"), "ai_messages", ["role"], unique=False)
    op.create_index(op.f("ix_ai_messages_created_at"), "ai_messages", ["created_at"], unique=False)

    op.create_table(
        "ai_knowledge_entries",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_ai_knowledge_entries_id"), "ai_knowledge_entries", ["id"], unique=False)
    op.create_index(op.f("ix_ai_knowledge_entries_title"), "ai_knowledge_entries", ["title"], unique=False)
    op.create_index(op.f("ix_ai_knowledge_entries_category"), "ai_knowledge_entries", ["category"], unique=False)

    op.create_table(
        "ai_activity_logs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("request", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=100), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="completed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(op.f("ix_ai_activity_logs_id"), "ai_activity_logs", ["id"], unique=False)
    op.create_index(op.f("ix_ai_activity_logs_kind"), "ai_activity_logs", ["kind"], unique=False)
    op.create_index(op.f("ix_ai_activity_logs_intent"), "ai_activity_logs", ["intent"], unique=False)
    op.create_index(op.f("ix_ai_activity_logs_status"), "ai_activity_logs", ["status"], unique=False)
    op.create_index(op.f("ix_ai_activity_logs_created_at"), "ai_activity_logs", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_ai_activity_logs_created_at"), table_name="ai_activity_logs")
    op.drop_index(op.f("ix_ai_activity_logs_status"), table_name="ai_activity_logs")
    op.drop_index(op.f("ix_ai_activity_logs_intent"), table_name="ai_activity_logs")
    op.drop_index(op.f("ix_ai_activity_logs_kind"), table_name="ai_activity_logs")
    op.drop_index(op.f("ix_ai_activity_logs_id"), table_name="ai_activity_logs")
    op.drop_table("ai_activity_logs")

    op.drop_index(op.f("ix_ai_knowledge_entries_category"), table_name="ai_knowledge_entries")
    op.drop_index(op.f("ix_ai_knowledge_entries_title"), table_name="ai_knowledge_entries")
    op.drop_index(op.f("ix_ai_knowledge_entries_id"), table_name="ai_knowledge_entries")
    op.drop_table("ai_knowledge_entries")

    op.drop_index(op.f("ix_ai_messages_created_at"), table_name="ai_messages")
    op.drop_index(op.f("ix_ai_messages_role"), table_name="ai_messages")
    op.drop_index(op.f("ix_ai_messages_conversation_id"), table_name="ai_messages")
    op.drop_index(op.f("ix_ai_messages_id"), table_name="ai_messages")
    op.drop_table("ai_messages")

    op.drop_index(op.f("ix_ai_conversations_created_at"), table_name="ai_conversations")
    op.drop_index(op.f("ix_ai_conversations_id"), table_name="ai_conversations")
    op.drop_table("ai_conversations")
