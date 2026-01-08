"""Add account hierarchy (parent_id and depth)

Revision ID: 0002
Revises: 0001
Create Date: 2026-01-04

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add parent_id column (nullable, self-referential FK)
    op.add_column("accounts", sa.Column("parent_id", sa.UUID(), nullable=True))

    # Add depth column (1=root, 2=child, 3=grandchild)
    op.add_column("accounts", sa.Column("depth", sa.Integer(), nullable=False, server_default="1"))

    # Create index on parent_id for efficient tree queries
    op.create_index("ix_accounts_parent_id", "accounts", ["parent_id"])

    # Create composite index for ledger + parent queries
    op.create_index("ix_accounts_ledger_parent", "accounts", ["ledger_id", "parent_id"])

    # Add foreign key constraint (self-referential)
    op.create_foreign_key(
        "fk_accounts_parent_id", "accounts", "accounts", ["parent_id"], ["id"], ondelete="CASCADE"
    )


def downgrade() -> None:
    op.drop_constraint("fk_accounts_parent_id", "accounts", type_="foreignkey")
    op.drop_index("ix_accounts_ledger_parent", table_name="accounts")
    op.drop_index("ix_accounts_parent_id", table_name="accounts")
    op.drop_column("accounts", "depth")
    op.drop_column("accounts", "parent_id")
