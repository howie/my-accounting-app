"""ImportSession model for tracking import operations.

Based on data-model.md for 006-data-import feature.
Tracks each import operation's source, status, and results for audit trail.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.ledger import Ledger


class ImportStatus(str, Enum):
    """Enum for import session status."""

    PENDING = "PENDING"  # Preview created, awaiting user confirmation
    PROCESSING = "PROCESSING"  # Import in progress
    COMPLETED = "COMPLETED"  # Import completed successfully
    FAILED = "FAILED"  # Import failed


from src.schemas.data_import import ImportType


class ImportSession(SQLModel, table=True):
    """Tracks a single import operation.

    Used for audit trail and to prevent duplicate imports.
    Records source file, status, progress, and results.
    """

    __tablename__ = "import_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", index=True)

    # Import source information
    import_type: ImportType = Field(sa_column=Column(SAEnum(ImportType)))
    source_filename: str = Field(max_length=255)
    source_file_hash: str = Field(max_length=64)  # SHA-256 for duplicate detection
    bank_code: str | None = Field(default=None, max_length=20)  # Bank code for credit card imports

    # Status tracking
    status: ImportStatus = Field(
        default=ImportStatus.PENDING,
        sa_column=Column(SAEnum(ImportStatus)),
    )
    progress_current: int = Field(default=0)
    progress_total: int = Field(default=0)

    # Result statistics
    imported_count: int = Field(default=0)
    skipped_count: int = Field(default=0)
    error_count: int = Field(default=0)
    created_accounts_count: int = Field(default=0)

    # Error message (if failed)
    error_message: str | None = Field(default=None, max_length=1000)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)

    # Relationships
    ledger: "Ledger" = Relationship(back_populates="import_sessions")
