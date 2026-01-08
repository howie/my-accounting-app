"""Transaction-related schemas for request/response validation.

Based on contracts/transaction_service.md
"""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import Field, field_validator
from sqlmodel import SQLModel

from src.models.account import AccountType
from src.models.transaction import TransactionType


class TransactionCreate(SQLModel):
    """Schema for creating a new transaction."""

    date: date
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=Decimal("0"), max_digits=15, decimal_places=2)
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    transaction_type: TransactionType

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        """Ensure description is not whitespace only."""
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace only")
        return v.strip()


class TransactionUpdate(SQLModel):
    """Schema for updating a transaction."""

    date: date
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=Decimal("0"), max_digits=15, decimal_places=2)
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    transaction_type: TransactionType

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        """Ensure description is not whitespace only."""
        if not v.strip():
            raise ValueError("Description cannot be empty or whitespace only")
        return v.strip()


class AccountSummary(SQLModel):
    """Minimal account info for transaction display."""

    id: uuid.UUID
    name: str
    type: AccountType


class TransactionRead(SQLModel):
    """Schema for reading a transaction (full details)."""

    id: uuid.UUID
    ledger_id: uuid.UUID
    date: date
    description: str
    amount: Decimal
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    transaction_type: TransactionType
    created_at: datetime
    updated_at: datetime
    from_account: AccountSummary | None = None
    to_account: AccountSummary | None = None


class TransactionListItem(SQLModel):
    """Schema for transaction list items (summary with account names)."""

    id: uuid.UUID
    date: date
    description: str
    amount: Decimal
    transaction_type: TransactionType
    from_account: AccountSummary
    to_account: AccountSummary


class PaginatedTransactions(SQLModel):
    """Paginated list of transactions."""

    data: list[TransactionListItem]
    cursor: str | None = None
    has_more: bool = False
