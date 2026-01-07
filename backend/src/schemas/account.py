"""Account-related schemas for request/response validation.

Based on contracts/account_service.md
Supports hierarchical account structure.
"""

from __future__ import annotations

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
    parent_id: uuid.UUID | None = Field(default=None)


class AccountRead(SQLModel):
    """Schema for reading an account (full details)."""

    id: uuid.UUID
    ledger_id: uuid.UUID
    name: str
    type: AccountType
    balance: Decimal
    is_system: bool
    parent_id: uuid.UUID | None
    depth: int
    sort_order: int = 0
    has_children: bool = False
    created_at: datetime
    updated_at: datetime


class AccountListItem(SQLModel):
    """Schema for account list items (summary)."""

    id: uuid.UUID
    name: str
    type: AccountType
    balance: Decimal
    is_system: bool
    parent_id: uuid.UUID | None
    depth: int
    sort_order: int = 0
    has_children: bool = False


class AccountTreeNode(SQLModel):
    """Schema for hierarchical account tree node."""

    id: uuid.UUID
    name: str
    type: AccountType
    balance: Decimal  # Aggregated balance including all descendants
    is_system: bool
    parent_id: uuid.UUID | None
    depth: int
    sort_order: int = 0
    children: list[AccountTreeNode] = Field(default_factory=list)


class AccountUpdate(SQLModel):
    """Schema for updating an account."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    parent_id: uuid.UUID | None = Field(default=None)


# Enable self-referential model
AccountTreeNode.model_rebuild()


class AccountReorderRequest(SQLModel):
    """Schema for reordering accounts within a parent."""

    parent_id: uuid.UUID | None = Field(default=None)
    account_ids: list[uuid.UUID] = Field(min_length=1)


class CanDeleteResponse(SQLModel):
    """Schema for checking if account can be deleted."""

    can_delete: bool
    has_children: bool
    has_transactions: bool
    transaction_count: int = 0
    child_count: int = 0


class ReassignRequest(SQLModel):
    """Schema for reassigning transactions before deletion."""

    replacement_account_id: uuid.UUID


class ReassignResponse(SQLModel):
    """Schema for reassignment result."""

    transactions_moved: int
    deleted_account_id: uuid.UUID
