"""Ledger model for the accounting system.

Based on data-model.md
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.transaction import Transaction


class Ledger(SQLModel, table=True):
    """A container for a complete set of financial records (an account book).

    Represents a specific tracking context (e.g., personal finances for 2024).
    Each ledger has an independent chart of accounts and transaction list.
    """

    __tablename__ = "ledgers"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    initial_balance: Decimal = Field(default=Decimal("0"), max_digits=15, decimal_places=2)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    accounts: list["Account"] = Relationship(
        back_populates="ledger",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    transactions: list["Transaction"] = Relationship(
        back_populates="ledger",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
