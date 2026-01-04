"""Ledger-related schemas for request/response validation.

Based on contracts/ledger_service.md
"""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import Field
from sqlmodel import SQLModel


class LedgerCreate(SQLModel):
    """Schema for creating a new ledger."""

    name: str = Field(min_length=1, max_length=100)
    initial_balance: Decimal = Field(
        default=Decimal("0"), ge=0, max_digits=15, decimal_places=2
    )


class LedgerRead(SQLModel):
    """Schema for reading a ledger (full details)."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    initial_balance: Decimal
    created_at: datetime


class LedgerListItem(SQLModel):
    """Schema for ledger list items (summary)."""

    id: uuid.UUID
    name: str
    initial_balance: Decimal
    created_at: datetime


class LedgerUpdate(SQLModel):
    """Schema for updating a ledger."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
