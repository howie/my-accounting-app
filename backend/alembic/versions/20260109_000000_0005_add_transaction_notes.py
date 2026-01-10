"""Add notes and amount_expression fields to transactions table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-01-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add notes and amount_expression columns to transactions table."""
    op.add_column(
        "transactions",
        sa.Column("notes", sa.String(500), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("amount_expression", sa.String(100), nullable=True),
    )


def downgrade() -> None:
    """Remove notes and amount_expression columns from transactions table."""
    op.drop_column("transactions", "amount_expression")
    op.drop_column("transactions", "notes")
