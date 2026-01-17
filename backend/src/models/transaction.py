"""Transaction model for the accounting system.

Based on data-model.md
"""

import uuid
from datetime import UTC, datetime
from datetime import date as date_type
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Index
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.advanced import InstallmentPlan, RecurringTransaction, Tag
    from src.models.ledger import Ledger


class TransactionType(str, Enum):
    """Enum for transaction types."""

    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"


class TransactionTagLink(SQLModel, table=True):
    """Many-to-many link between Transactions and Tags."""

    __tablename__ = "transaction_tags"

    transaction_id: uuid.UUID = Field(foreign_key="transactions.id", primary_key=True)
    tag_id: uuid.UUID = Field(foreign_key="tags.id", primary_key=True)


class Transaction(SQLModel, table=True):
    """A single financial event recorded using double-entry bookkeeping.

    An event affecting exactly two accounts with equal amounts.
    The amount is always positive; direction is determined by from/to accounts.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        # Composite index for efficient ledger transaction listing sorted by date
        Index("idx_transactions_ledger_date", "ledger_id", "date"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", index=True)
    date: date_type = Field(index=True)
    description: str = Field(max_length=255)
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    from_account_id: uuid.UUID = Field(foreign_key="accounts.id", index=True)
    to_account_id: uuid.UUID = Field(foreign_key="accounts.id", index=True)
    transaction_type: TransactionType = Field(sa_column=Column(SAEnum(TransactionType)))
    notes: str | None = Field(default=None, max_length=500)
    amount_expression: str | None = Field(default=None, max_length=100)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # New fields for Advanced Transactions
    recurring_transaction_id: uuid.UUID | None = Field(
        default=None, foreign_key="recurring_transactions.id", nullable=True
    )
    installment_plan_id: uuid.UUID | None = Field(
        default=None, foreign_key="installment_plans.id", nullable=True
    )
    installment_number: int | None = Field(default=None, nullable=True)

    # Relationships
    ledger: "Ledger" = Relationship(back_populates="transactions")
    from_account: "Account" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Transaction.from_account_id]"}
    )
    to_account: "Account" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Transaction.to_account_id]"}
    )

    # Advanced Relationships
    tags: list["Tag"] = Relationship(back_populates="transactions", link_model=TransactionTagLink)
    recurring_transaction: Optional["RecurringTransaction"] = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[Transaction.recurring_transaction_id]"}
    )
    installment_plan: Optional["InstallmentPlan"] = Relationship(back_populates="transactions")
