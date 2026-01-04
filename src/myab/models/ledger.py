from typing import Optional
from src.myab.models.base import BaseModel

class Ledger(BaseModel):
    """
    Represents a container for financial records.
    Each ledger has independent chart of accounts and transaction list.
    """
    def __init__(self, user_account_id: int, name: str, creation_date: str,
                 id: Optional[int] = None,
                 creation_timestamp: Optional[str] = None,
                 modification_timestamp: Optional[str] = None):
        super().__init__(id, creation_timestamp, modification_timestamp)
        self.user_account_id = user_account_id
        self.name = name
        self.creation_date = creation_date # ISO 8601 format

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "user_account_id": self.user_account_id,
            "name": self.name,
            "creation_date": self.creation_date
        })
        return data

    def __repr__(self) -> str:
        return f"Ledger(id={self.id}, name='{self.name}', user_account_id={self.user_account_id})"