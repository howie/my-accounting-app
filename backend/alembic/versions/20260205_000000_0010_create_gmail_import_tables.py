"""Create Gmail import tables.

Revision ID: 0010
Revises: 0009
Create Date: 2026-02-05

Tables created:
- gmail_connections: OAuth2 connection state and credentials
- user_bank_settings: Per-user bank configuration
- statement_scan_jobs: Scan execution tracking
- discovered_statements: Found statements tracking

Column added:
- import_sessions.email_message_id: Gmail message ID for audit trail
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create gmail_connections table
    op.create_table(
        "gmail_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("ledger_id", sa.Uuid(), nullable=False),
        sa.Column("email_address", sa.String(length=255), nullable=False),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=False),
        sa.Column("token_expiry", sa.DateTime(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("CONNECTED", "EXPIRED", "DISCONNECTED", name="gmailconnectionstatus"),
            nullable=False,
        ),
        sa.Column("scan_start_date", sa.Date(), nullable=False),
        sa.Column(
            "schedule_frequency",
            sa.Enum("DAILY", "WEEKLY", name="schedulefrequency"),
            nullable=True,
        ),
        sa.Column("schedule_hour", sa.Integer(), nullable=True),
        sa.Column("schedule_day_of_week", sa.Integer(), nullable=True),
        sa.Column("last_scan_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["ledger_id"], ["ledgers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_gmail_connections_ledger_id"), "gmail_connections", ["ledger_id"], unique=True
    )

    # Create user_bank_settings table
    op.create_table(
        "user_bank_settings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("bank_code", sa.String(length=20), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False),
        sa.Column("encrypted_pdf_password", sa.Text(), nullable=True),
        sa.Column("credit_card_account_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["credit_card_account_id"], ["accounts.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "bank_code", name="uq_user_bank"),
    )
    op.create_index(
        op.f("ix_user_bank_settings_user_id"), "user_bank_settings", ["user_id"], unique=False
    )

    # Create statement_scan_jobs table
    op.create_table(
        "statement_scan_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("gmail_connection_id", sa.Uuid(), nullable=False),
        sa.Column(
            "trigger_type",
            sa.Enum("MANUAL", "SCHEDULED", name="scantriggertype"),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "SCANNING", "COMPLETED", "FAILED", name="scanjobstatus"),
            nullable=False,
        ),
        sa.Column("banks_scanned", sa.String(), nullable=False),
        sa.Column("statements_found", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["gmail_connection_id"], ["gmail_connections.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_statement_scan_jobs_gmail_connection_id"),
        "statement_scan_jobs",
        ["gmail_connection_id"],
        unique=False,
    )

    # Create discovered_statements table
    op.create_table(
        "discovered_statements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scan_job_id", sa.Uuid(), nullable=False),
        sa.Column("bank_code", sa.String(length=20), nullable=False),
        sa.Column("bank_name", sa.String(length=100), nullable=False),
        sa.Column("billing_period_start", sa.Date(), nullable=True),
        sa.Column("billing_period_end", sa.Date(), nullable=True),
        sa.Column("email_message_id", sa.String(length=255), nullable=False),
        sa.Column("email_subject", sa.String(length=500), nullable=False),
        sa.Column("email_date", sa.DateTime(), nullable=False),
        sa.Column("pdf_attachment_id", sa.String(length=255), nullable=False),
        sa.Column("pdf_filename", sa.String(length=255), nullable=False),
        sa.Column(
            "parse_status",
            sa.Enum("PENDING", "PARSED", "PARSE_FAILED", "LLM_PARSED", name="statementparsestatus"),
            nullable=False,
        ),
        sa.Column("parse_confidence", sa.Float(), nullable=True),
        sa.Column("transaction_count", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column(
            "import_status",
            sa.Enum("NOT_IMPORTED", "IMPORTED", "SKIPPED", name="statementimportstatus"),
            nullable=False,
        ),
        sa.Column("import_session_id", sa.Uuid(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["import_session_id"], ["import_sessions.id"]),
        sa.ForeignKeyConstraint(["scan_job_id"], ["statement_scan_jobs.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "bank_code",
            "billing_period_start",
            "billing_period_end",
            name="uq_statement_period",
        ),
    )
    op.create_index(
        op.f("ix_discovered_statements_scan_job_id"),
        "discovered_statements",
        ["scan_job_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_discovered_statements_email_message_id"),
        "discovered_statements",
        ["email_message_id"],
        unique=False,
    )

    # Add email_message_id to import_sessions
    op.add_column(
        "import_sessions",
        sa.Column("email_message_id", sa.String(length=255), nullable=True),
    )

    # Add GMAIL_CC to ImportType enum
    op.execute("ALTER TYPE importtype ADD VALUE IF NOT EXISTS 'GMAIL_CC'")


def downgrade() -> None:
    # Remove email_message_id from import_sessions
    op.drop_column("import_sessions", "email_message_id")

    # Drop discovered_statements table
    op.drop_index(
        op.f("ix_discovered_statements_email_message_id"), table_name="discovered_statements"
    )
    op.drop_index(op.f("ix_discovered_statements_scan_job_id"), table_name="discovered_statements")
    op.drop_table("discovered_statements")

    # Drop statement_scan_jobs table
    op.drop_index(
        op.f("ix_statement_scan_jobs_gmail_connection_id"), table_name="statement_scan_jobs"
    )
    op.drop_table("statement_scan_jobs")

    # Drop user_bank_settings table
    op.drop_index(op.f("ix_user_bank_settings_user_id"), table_name="user_bank_settings")
    op.drop_table("user_bank_settings")

    # Drop gmail_connections table
    op.drop_index(op.f("ix_gmail_connections_ledger_id"), table_name="gmail_connections")
    op.drop_table("gmail_connections")

    # Drop enums
    op.execute("DROP TYPE IF EXISTS statementimportstatus")
    op.execute("DROP TYPE IF EXISTS statementparsestatus")
    op.execute("DROP TYPE IF EXISTS scanjobstatus")
    op.execute("DROP TYPE IF EXISTS scantriggertype")
    op.execute("DROP TYPE IF EXISTS schedulefrequency")
    op.execute("DROP TYPE IF EXISTS gmailconnectionstatus")

    # Note: Cannot easily remove GMAIL_CC from importtype enum in PostgreSQL
    # Would need to recreate the enum type
