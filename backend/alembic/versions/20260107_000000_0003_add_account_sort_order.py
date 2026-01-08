"""Add sort_order to accounts for custom ordering

Revision ID: 0003
Revises: 0002
Create Date: 2026-01-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003'
down_revision: Union[str, None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add sort_order column with default 0
    op.add_column('accounts', sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))

    # Initialize sort_order based on current name ordering within each parent
    # Uses gap strategy (multiples of 1000) to allow insertions without full reorder
    op.execute("""
        WITH ordered AS (
            SELECT id, ROW_NUMBER() OVER (
                PARTITION BY ledger_id, parent_id
                ORDER BY name
            ) * 1000 AS new_order
            FROM accounts
        )
        UPDATE accounts SET sort_order = ordered.new_order
        FROM ordered WHERE accounts.id = ordered.id
    """)

    # Create composite index for efficient ordering queries
    op.create_index('ix_accounts_ledger_parent_sort', 'accounts', ['ledger_id', 'parent_id', 'sort_order'])


def downgrade() -> None:
    op.drop_index('ix_accounts_ledger_parent_sort', table_name='accounts')
    op.drop_column('accounts', 'sort_order')
