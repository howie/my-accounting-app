"""Add BANK_RECORD import type.

Revision ID: 0011
Revises: 0010
Create Date: 2026-02-19
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add BANK_RECORD to ImportType enum."""
    op.execute("ALTER TYPE importtype ADD VALUE IF NOT EXISTS 'BANK_RECORD'")


def downgrade() -> None:
    """Cannot easily remove enum value in PostgreSQL."""
    pass
