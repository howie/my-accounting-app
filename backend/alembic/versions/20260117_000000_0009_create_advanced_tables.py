"""create_advanced_tables

Revision ID: 0009
Revises: 0008
Create Date: 2026-01-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel

# revision identifiers, used by Alembic.
revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    # Create tags table
    op.create_table('tags',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=True)

    # Create recurring_transactions table
    op.create_table('recurring_transactions',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('transaction_type', sa.String(), nullable=False),
        sa.Column('source_account_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('dest_account_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('frequency', sa.Enum('DAILY', 'WEEKLY', 'MONTHLY', 'YEARLY', name='frequency'), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('last_generated_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['dest_account_id'], ['accounts.id'], )
    )
    op.create_index(op.f('ix_recurring_transactions_id'), 'recurring_transactions', ['id'], unique=False)

    # Create installment_plans table
    op.create_table('installment_plans',
        sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('total_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('installment_count', sa.Integer(), nullable=False),
        sa.Column('source_account_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('dest_account_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['source_account_id'], ['accounts.id'], ),
        sa.ForeignKeyConstraint(['dest_account_id'], ['accounts.id'], )
    )
    op.create_index(op.f('ix_installment_plans_id'), 'installment_plans', ['id'], unique=False)

    # Create transaction_tags association table
    op.create_table('transaction_tags',
        sa.Column('transaction_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column('tag_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.PrimaryKeyConstraint('transaction_id', 'tag_id'),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], )
    )

    # Update transactions table
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('recurring_transaction_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
        batch_op.add_column(sa.Column('installment_plan_id', sqlmodel.sql.sqltypes.GUID(), nullable=True))
        batch_op.add_column(sa.Column('installment_number', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_transactions_recurring', 'recurring_transactions', ['recurring_transaction_id'], ['id'])
        batch_op.create_foreign_key('fk_transactions_installment', 'installment_plans', ['installment_plan_id'], ['id'])


def downgrade():
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_transactions_installment', type_='foreignkey')
        batch_op.drop_constraint('fk_transactions_recurring', type_='foreignkey')
        batch_op.drop_column('installment_number')
        batch_op.drop_column('installment_plan_id')
        batch_op.drop_column('recurring_transaction_id')

    op.drop_table('transaction_tags')
    op.drop_index(op.f('ix_installment_plans_id'), table_name='installment_plans')
    op.drop_table('installment_plans')
    op.drop_index(op.f('ix_recurring_transactions_id'), table_name='recurring_transactions')
    op.drop_table('recurring_transactions')
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_index(op.f('ix_tags_id'), table_name='tags')
    op.drop_table('tags')
