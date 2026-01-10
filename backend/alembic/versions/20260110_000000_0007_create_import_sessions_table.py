"""Create import_sessions table.

Revision ID: 0007
Revises: 0004
Create Date: 2026-01-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "import_sessions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("ledger_id", sa.UUID(), nullable=False),
        sa.Column(
            "import_type",
            sa.Enum("MYAB_CSV", "CREDIT_CARD", name="importtype"),
            nullable=False,
        ),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("source_file_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "PROCESSING", "COMPLETED", "FAILED", name="importstatus"),
            nullable=False,
        ),
        sa.Column("progress_current", sa.Integer(), nullable=False, default=0),
        sa.Column("progress_total", sa.Integer(), nullable=False, default=0),
        sa.Column("imported_count", sa.Integer(), nullable=False, default=0),
        sa.Column("skipped_count", sa.Integer(), nullable=False, default=0),
        sa.Column("error_count", sa.Integer(), nullable=False, default=0),
        sa.Column("created_accounts_count", sa.Integer(), nullable=False, default=0),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["ledger_id"], ["ledgers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_import_sessions_ledger_id", "import_sessions", ["ledger_id"], unique=False
    )
    op.create_index(
        "idx_import_sessions_status", "import_sessions", ["status"], unique=False
    )
    op.create_index(
        "idx_import_sessions_created_at", "import_sessions", ["created_at"], unique=False
    )


def downgrade() -> None:
    op.drop_index("idx_import_sessions_created_at", table_name="import_sessions")
    op.drop_index("idx_import_sessions_status", table_name="import_sessions")
    op.drop_index("idx_import_sessions_ledger_id", table_name="import_sessions")
    op.drop_table("import_sessions")
    # Drop enum types
    sa.Enum(name="importstatus").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="importtype").drop(op.get_bind(), checkfirst=True)
