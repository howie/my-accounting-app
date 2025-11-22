from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from .base import BaseModel

@dataclass
class UserAccount(BaseModel):
    username: str
    password_hash: str
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
