"""Account model for the accounting system.

Based on data-model.md
Supports hierarchical account structure (up to 3 levels deep).
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel


class AccountType(str, Enum):
    """Enum for account types in double-entry bookkeeping."""

    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class Account(SQLModel, table=True):
    """A single category within the Chart of Accounts for a ledger.

    Accounts are classified as Asset, Liability, Income, or Expense.
    System accounts (Cash, Equity) are created automatically and cannot be deleted.

    Supports hierarchical structure:
    - depth=1: Root level (no parent)
    - depth=2: Child of root
    - depth=3: Grandchild (max depth)

    Only leaf accounts (accounts without children) can have transactions.
    Parent accounts display aggregated balances from all descendants.
    """

    __tablename__ = "accounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", index=True)
    name: str = Field(max_length=100)
    type: AccountType = Field(sa_column=Column(SAEnum(AccountType)))
    balance: Decimal = Field(default=Decimal("0"), max_digits=15, decimal_places=2)
    is_system: bool = Field(default=False)

    # Hierarchy fields
    parent_id: uuid.UUID | None = Field(default=None, foreign_key="accounts.id", index=True)
    depth: int = Field(default=1, ge=1, le=3)  # 1=root, 2=child, 3=grandchild
    sort_order: int = Field(default=0, ge=0)  # Custom ordering within parent

    is_archived: bool = Field(default=False)
    archived_at: datetime | None = Field(default=None)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    ledger: "Ledger" = Relationship(back_populates="accounts")

    # Self-referential relationships for hierarchy
    parent: Optional["Account"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={
            "remote_side": "Account.id",
            "foreign_keys": "[Account.parent_id]",
        },
    )
    children: list["Account"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={
            "foreign_keys": "[Account.parent_id]",
            "cascade": "all, delete-orphan",
        },
    )


# Import at module level to register Ledger for SQLAlchemy
from src.models.ledger import Ledger  # noqa: E402, F401
