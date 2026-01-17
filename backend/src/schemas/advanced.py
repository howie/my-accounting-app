from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.models.advanced import Frequency
from src.models.transaction import TransactionType


# Tag Schemas
class TagBase(BaseModel):
    name: str
    color: str | None = "#808080"


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = None
    color: str | None = None


class TagRead(TagBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# Recurring Transaction Schemas
class RecurringTransactionBase(BaseModel):
    name: str
    amount: Decimal
    transaction_type: TransactionType
    source_account_id: UUID
    dest_account_id: UUID
    frequency: Frequency
    start_date: date
    end_date: date | None = None


class RecurringTransactionCreate(RecurringTransactionBase):
    pass


class RecurringTransactionRead(RecurringTransactionBase):
    id: UUID
    last_generated_date: date | None = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class RecurringTransactionDue(BaseModel):
    id: UUID
    name: str
    amount: Decimal
    due_date: date
    model_config = ConfigDict(from_attributes=True)


# Installment Plan Schemas
class InstallmentPlanBase(BaseModel):
    name: str
    total_amount: Decimal
    installment_count: int
    source_account_id: UUID
    dest_account_id: UUID
    start_date: date


class InstallmentPlanCreate(InstallmentPlanBase):
    pass


class InstallmentPlanRead(InstallmentPlanBase):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
