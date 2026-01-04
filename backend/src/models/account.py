"""Account model for the accounting system.

Based on data-model.md
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

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
    """

    __tablename__ = "accounts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", index=True)
    name: str = Field(max_length=100)
    type: AccountType = Field(sa_column=Column(SAEnum(AccountType)))
    balance: Decimal = Field(default=Decimal("0"), max_digits=15, decimal_places=2)
    is_system: bool = Field(default=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    ledger: "Ledger" = Relationship(back_populates="accounts")  # type: ignore


# Avoid circular import
from src.models.ledger import Ledger  # noqa: E402, F401
