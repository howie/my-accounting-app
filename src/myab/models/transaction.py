from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from .base import BaseModel

@dataclass
class Transaction(BaseModel):
    ledger_id: int
    date: date
    type: str
    debit_account_id: int
    credit_account_id: int
    amount: Decimal
    description: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
