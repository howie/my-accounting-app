"""EmailImportBatch model for multi-channel integration.

Based on data-model.md for 012-ai-multi-channel feature.
Tracks each email bill import batch from parsing through confirmation to import.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, Index, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.email_authorization import EmailAuthorization


class EmailImportStatus(str, Enum):
    """Status of an email import batch."""

    PARSED = "PARSED"
    PENDING_CONFIRMATION = "PENDING_CONFIRMATION"
    IMPORTING = "IMPORTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class EmailImportBatch(SQLModel, table=True):
    """Tracks a single email bill import batch.

    Records source email metadata, parsed transactions (as JSON for preview),
    and tracks the import lifecycle through status transitions.
    """

    __tablename__ = "email_import_batches"
    __table_args__ = (
        UniqueConstraint(
            "email_message_id",
            "statement_period_hash",
            name="uq_email_import_dedup",
        ),
        Index("idx_email_batch_auth", "email_authorization_id"),
        Index("idx_email_batch_ledger", "ledger_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    email_authorization_id: uuid.UUID = Field(foreign_key="email_authorizations.id")
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id")
    email_message_id: str = Field(max_length=255)
    email_subject: str = Field(max_length=500)
    email_sender: str = Field(max_length=255)
    email_date: datetime
    statement_period_hash: str = Field(max_length=64)
    parsed_transactions: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    parsed_count: int = Field(default=0)
    imported_count: int = Field(default=0)
    failed_count: int = Field(default=0)
    status: EmailImportStatus = Field(
        default=EmailImportStatus.PARSED,
        sa_column=Column(SAEnum(EmailImportStatus), nullable=False, default="PARSED"),
    )
    error_message: str | None = Field(default=None, sa_column=Column(Text))
    user_confirmed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)

    # Relationships
    email_authorization: "EmailAuthorization" = Relationship(back_populates="import_batches")
