"""Create audit_logs table for tracking entity changes

Revision ID: 0004
Revises: 0003
Create Date: 2026-01-07

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


# revision identifiers, used by Alembic.
revision: str = '0004'
down_revision: Union[str, None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use IF NOT EXISTS to make migration idempotent
    conn = op.get_bind()
    result = conn.execute(sa.text("SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs'"))
    if result.fetchone() is not None:
        # Table already exists, skip creation
        return

    op.create_table(
        'audit_logs',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.Text(), nullable=False),  # CREATE, UPDATE, DELETE, REASSIGN
        sa.Column('old_value', JSONB, nullable=True),
        sa.Column('new_value', JSONB, nullable=True),
        sa.Column('extra_data', JSONB, nullable=True),  # Additional context (e.g., reassignment details)
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('ledger_id', UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['ledger_id'], ['ledgers.id'], ondelete='CASCADE'),
    )

    # Index for querying logs for a specific entity
    op.create_index('ix_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])

    # Index for querying recent logs by ledger
    op.create_index('ix_audit_logs_ledger_timestamp', 'audit_logs', ['ledger_id', sa.text('timestamp DESC')])

    # Index for querying logs by action type
    op.create_index('ix_audit_logs_ledger_action', 'audit_logs', ['ledger_id', 'action'])


def downgrade() -> None:
    op.drop_index('ix_audit_logs_ledger_action', table_name='audit_logs')
    op.drop_index('ix_audit_logs_ledger_timestamp', table_name='audit_logs')
    op.drop_index('ix_audit_logs_entity', table_name='audit_logs')
    op.drop_table('audit_logs')
