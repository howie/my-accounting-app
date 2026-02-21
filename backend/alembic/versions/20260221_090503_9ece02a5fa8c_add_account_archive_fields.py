"""add_account_archive_fields

Revision ID: 9ece02a5fa8c
Revises: 17b1dbe5b300
Create Date: 2026-02-21 09:05:03.553975+00:00
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9ece02a5fa8c"
down_revision: str | None = "17b1dbe5b300"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.add_column("accounts", sa.Column("archived_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "archived_at")
    op.drop_column("accounts", "is_archived")
