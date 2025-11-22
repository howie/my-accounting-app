from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from enum import Enum
from .base import BaseModel

class AccountType(str, Enum):
    ASSET = "Asset"
    LIABILITY = "Liability"
    INCOME = "Income"
    EXPENSE = "Expense"

@dataclass
class Account(BaseModel):
    ledger_id: int
    name: str
    type: AccountType
    initial_balance: Decimal = Decimal("0.00")
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
