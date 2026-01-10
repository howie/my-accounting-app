"""TransactionTemplate model for reusable transaction presets.

Based on data-model.md from 004-transaction-entry feature.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

from src.models.transaction import TransactionType

if TYPE_CHECKING:
    from src.models.account import Account
    from src.models.ledger import Ledger


class TransactionTemplate(SQLModel, table=True):
    """A reusable transaction preset for quick entry.

    Stores default values for commonly used transactions (e.g., monthly rent,
    recurring subscriptions) that users can apply with a single click.
    """

    __tablename__ = "transaction_templates"
    __table_args__ = (
        # Composite index for efficient ordered listing by ledger
        Index("idx_template_ledger_sort", "ledger_id", "sort_order"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", index=True)
    name: str = Field(max_length=50)
    transaction_type: TransactionType
    from_account_id: uuid.UUID = Field(foreign_key="accounts.id")
    to_account_id: uuid.UUID = Field(foreign_key="accounts.id")
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    description: str = Field(max_length=200)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    ledger: "Ledger" = Relationship(back_populates="templates")
    from_account: "Account" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TransactionTemplate.from_account_id]"}
    )
    to_account: "Account" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TransactionTemplate.to_account_id]"}
    )
