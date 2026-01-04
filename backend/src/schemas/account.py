"""Account-related schemas for request/response validation.

Based on contracts/account_service.md
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field
from sqlmodel import SQLModel

from src.models.account import AccountType


class AccountCreate(SQLModel):
    """Schema for creating a new account."""

    name: str = Field(min_length=1, max_length=100)
    type: AccountType


class AccountRead(SQLModel):
    """Schema for reading an account (full details)."""

    id: uuid.UUID
    ledger_id: uuid.UUID
    name: str
    type: AccountType
    balance: Decimal
    is_system: bool
    created_at: datetime
    updated_at: datetime


class AccountListItem(SQLModel):
    """Schema for account list items (summary)."""

    id: uuid.UUID
    name: str
    type: AccountType
    balance: Decimal
    is_system: bool


class AccountUpdate(SQLModel):
    """Schema for updating an account."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
