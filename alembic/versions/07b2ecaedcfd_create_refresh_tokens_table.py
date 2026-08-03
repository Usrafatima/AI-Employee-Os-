"""create refresh tokens table

Revision ID: 07b2ecaedcfd
Revises: 70cb7fe12042
Create Date: 2026-08-01 14:30:01.800154
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "07b2ecaedcfd"
down_revision: Union[str, Sequence[str], None] = "70cb7fe12042"
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
            nullable=True,
        ),
    )

    op.create_index(
        "ix_refresh_tokens_id",
        "refresh_tokens",
        ["id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_refresh_tokens_id",
        table_name="refresh_tokens",
    )

    op.drop_table("refresh_tokens")