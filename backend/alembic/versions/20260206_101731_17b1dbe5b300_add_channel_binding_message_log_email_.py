"""add channel binding, message log, email auth, email import batch tables and transaction source fields

Revision ID: 17b1dbe5b300
Revises: 0009
Create Date: 2026-02-06 10:17:31.638493+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "17b1dbe5b300"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- Feature 012: New tables ---

    # email_authorizations
    op.create_table(
        "email_authorizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("email_address", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("provider", sa.Enum("GMAIL", name="emailprovider"), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("scopes", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_email_auth_active",
        "email_authorizations",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index("idx_email_auth_user", "email_authorizations", ["user_id"], unique=False)

    # channel_bindings
    op.create_table(
        "channel_bindings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column(
            "channel_type",
            sa.Enum("TELEGRAM", "LINE", "SLACK", name="channeltype"),
            nullable=False,
        ),
        sa.Column("external_user_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("display_name", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("default_ledger_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("unbound_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["default_ledger_id"], ["ledgers.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("channel_type", "external_user_id", name="uq_channel_binding_active"),
    )
    op.create_index(
        "idx_channel_binding_active",
        "channel_bindings",
        ["user_id"],
        unique=False,
        postgresql_where=sa.text("is_active = true"),
    )
    op.create_index("idx_channel_binding_user", "channel_bindings", ["user_id"], unique=False)

    # email_import_batches
    op.create_table(
        "email_import_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email_authorization_id", sa.Uuid(), nullable=False),
        sa.Column("ledger_id", sa.Uuid(), nullable=False),
        sa.Column("email_message_id", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("email_subject", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=False),
        sa.Column("email_sender", sqlmodel.sql.sqltypes.AutoString(length=255), nullable=False),
        sa.Column("email_date", sa.DateTime(), nullable=False),
        sa.Column(
            "statement_period_hash",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=False,
        ),
        sa.Column("parsed_transactions", sa.JSON(), nullable=True),
        sa.Column("parsed_count", sa.Integer(), nullable=False),
        sa.Column("imported_count", sa.Integer(), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PARSED",
                "PENDING_CONFIRMATION",
                "IMPORTING",
                "COMPLETED",
                "FAILED",
                name="emailimportstatus",
            ),
            nullable=False,
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("user_confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["email_authorization_id"], ["email_authorizations.id"]),
        sa.ForeignKeyConstraint(["ledger_id"], ["ledgers.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "email_message_id", "statement_period_hash", name="uq_email_import_dedup"
        ),
    )
    op.create_index(
        "idx_email_batch_auth",
        "email_import_batches",
        ["email_authorization_id"],
        unique=False,
    )
    op.create_index("idx_email_batch_ledger", "email_import_batches", ["ledger_id"], unique=False)

    # channel_message_logs
    op.create_table(
        "channel_message_logs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("channel_binding_id", sa.Uuid(), nullable=False),
        sa.Column("channel_type", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False),
        sa.Column(
            "message_type",
            sa.Enum("TEXT", "VOICE", "COMMAND", name="messagetype"),
            nullable=False,
        ),
        sa.Column("raw_content", sa.Text(), nullable=False),
        sa.Column("parsed_intent", sqlmodel.sql.sqltypes.AutoString(length=50), nullable=True),
        sa.Column("parsed_data", sa.JSON(), nullable=True),
        sa.Column(
            "processing_status",
            sa.Enum("RECEIVED", "PROCESSING", "COMPLETED", "FAILED", name="processingstatus"),
            nullable=False,
        ),
        sa.Column("error_message", sqlmodel.sql.sqltypes.AutoString(length=500), nullable=True),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("transaction_id", sa.Uuid(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["channel_binding_id"], ["channel_bindings.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_message_log_binding",
        "channel_message_logs",
        ["channel_binding_id"],
        unique=False,
    )
    op.create_index("idx_message_log_created", "channel_message_logs", ["created_at"], unique=False)
    op.create_index(
        op.f("ix_channel_message_logs_transaction_id"),
        "channel_message_logs",
        ["transaction_id"],
        unique=False,
    )

    # --- Feature 012: Transaction source tracking columns ---
    op.add_column(
        "transactions",
        sa.Column(
            "source_channel",
            sqlmodel.sql.sqltypes.AutoString(length=20),
            nullable=True,
        ),
    )
    op.add_column(
        "transactions",
        sa.Column("channel_message_id", sa.Uuid(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transactions", "channel_message_id")
    op.drop_column("transactions", "source_channel")

    op.drop_index(op.f("ix_channel_message_logs_transaction_id"), table_name="channel_message_logs")
    op.drop_index("idx_message_log_created", table_name="channel_message_logs")
    op.drop_index("idx_message_log_binding", table_name="channel_message_logs")
    op.drop_table("channel_message_logs")

    op.drop_index("idx_email_batch_ledger", table_name="email_import_batches")
    op.drop_index("idx_email_batch_auth", table_name="email_import_batches")
    op.drop_table("email_import_batches")

    op.drop_index("idx_channel_binding_user", table_name="channel_bindings")
    op.drop_index(
        "idx_channel_binding_active",
        table_name="channel_bindings",
        postgresql_where=sa.text("is_active = true"),
    )
    op.drop_table("channel_bindings")

    op.drop_index("idx_email_auth_user", table_name="email_authorizations")
    op.drop_index(
        "idx_email_auth_active",
        table_name="email_authorizations",
        postgresql_where=sa.text("is_active = true"),
    )
    op.drop_table("email_authorizations")
