from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .base import BaseModel

@dataclass
class Ledger(BaseModel):
    user_account_id: int
    name: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
