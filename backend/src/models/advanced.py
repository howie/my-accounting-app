import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

# Import Link model to use as class in Relationship
# This assumes transaction.py does NOT import advanced.py at runtime
from src.models.transaction import TransactionTagLink

if TYPE_CHECKING:
    from src.models.transaction import Transaction


class Frequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(index=True, unique=True, nullable=False)
    color: str = Field(default="#808080")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    transactions: list["Transaction"] = Relationship(
        back_populates="tags", link_model=TransactionTagLink
    )


class RecurringTransaction(SQLModel, table=True):
    __tablename__ = "recurring_transactions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False)
    amount: Decimal = Field(max_digits=15, decimal_places=2, nullable=False)
    transaction_type: str = Field(nullable=False)

    source_account_id: uuid.UUID = Field(foreign_key="accounts.id", nullable=False)
    dest_account_id: uuid.UUID = Field(foreign_key="accounts.id", nullable=False)

    frequency: Frequency = Field(sa_column=Column(SAEnum(Frequency)))
    start_date: date = Field(nullable=False)
    end_date: date | None = Field(default=None, nullable=True)
    last_generated_date: date | None = Field(default=None, nullable=True)

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InstallmentPlan(SQLModel, table=True):
    __tablename__ = "installment_plans"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str = Field(nullable=False)
    total_amount: Decimal = Field(max_digits=15, decimal_places=2, nullable=False)
    installment_count: int = Field(nullable=False)

    source_account_id: uuid.UUID = Field(foreign_key="accounts.id", nullable=False)
    dest_account_id: uuid.UUID = Field(foreign_key="accounts.id", nullable=False)

    start_date: date = Field(nullable=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    transactions: list["Transaction"] = Relationship(back_populates="installment_plan")
