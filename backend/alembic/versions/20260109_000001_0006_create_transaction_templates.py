"""Create transaction_templates table.

Revision ID: 0006
Revises: 0005
Create Date: 2026-01-09

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create transaction_templates table."""
    op.create_table(
        "transaction_templates",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ledger_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("transaction_type", sa.String(20), nullable=False),
        sa.Column("from_account_id", sa.UUID(), nullable=False),
        sa.Column("to_account_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("description", sa.String(200), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["ledger_id"],
            ["ledgers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["from_account_id"],
            ["accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["to_account_id"],
            ["accounts.id"],
            ondelete="RESTRICT",
        ),
        sa.UniqueConstraint("ledger_id", "name", name="uq_template_ledger_name"),
        sa.CheckConstraint(
            "from_account_id != to_account_id",
            name="chk_template_different_accounts",
        ),
        sa.CheckConstraint(
            "amount >= 0.01 AND amount <= 999999999.99",
            name="chk_template_amount_range",
        ),
        sa.CheckConstraint(
            "transaction_type IN ('EXPENSE', 'INCOME', 'TRANSFER')",
            name="chk_template_type",
        ),
    )

    # Create index for efficient ordered listing by ledger
    op.create_index(
        "idx_template_ledger_sort",
        "transaction_templates",
        ["ledger_id", "sort_order"],
    )


def downgrade() -> None:
    """Drop transaction_templates table."""
    op.drop_index("idx_template_ledger_sort", table_name="transaction_templates")
    op.drop_table("transaction_templates")
