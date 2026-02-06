"""Email import Pydantic schemas for request/response validation.

Based on contracts/email-import-api.yaml for 012-ai-multi-channel feature.
"""

import uuid
from datetime import date, datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel

from src.models.email_authorization import EmailProvider
from src.models.email_import_batch import EmailImportStatus


class EmailAuthorizationRead(SQLModel):
    """Response schema for an email authorization."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email_address: str
    provider: EmailProvider
    is_active: bool
    last_sync_at: datetime | None = None
    created_at: datetime


class EmailImportBatchRead(SQLModel):
    """Response schema for an email import batch."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email_subject: str
    email_sender: str
    email_date: datetime | None = None
    status: EmailImportStatus
    parsed_count: int
    imported_count: int
    failed_count: int = 0
    created_at: datetime
    user_confirmed_at: datetime | None = None


class ParsedTransaction(SQLModel):
    """A single transaction parsed from an email bill."""

    index: int | None = None
    date: date
    description: str
    merchant: str | None = None
    amount: float
    currency: str = "TWD"
    suggested_from_account: str | None = None
    suggested_to_account: str | None = None
    confidence: float | None = None
    needs_review: bool = False


class EmailImportBatchDetail(EmailImportBatchRead):
    """Detailed response for an email import batch including parsed transactions."""

    parsed_transactions: list[ParsedTransaction] = []


class TransactionOverride(SQLModel):
    """User override for a single parsed transaction."""

    index: int
    from_account: str | None = None
    to_account: str | None = None
    description: str | None = None
    skip: bool = False


class ConfirmImportRequest(SQLModel):
    """Request to confirm an email import batch."""

    transaction_overrides: list[TransactionOverride] = []


class TriggerScanRequest(SQLModel):
    """Request to trigger an email scan."""

    authorization_id: uuid.UUID
    ledger_id: uuid.UUID
