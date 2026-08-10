"""add refresh token table

Revision ID: 57cccf4d4954
Revises:
Create Date: 2026-07-31 19:45:35.586786
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "57cccf4d4954"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "token",
            sa.String(),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("refresh_tokens")