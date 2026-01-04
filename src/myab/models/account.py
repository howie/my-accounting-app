from typing import Optional
from src.myab.models.base import BaseModel

class Account(BaseModel):
    """
    Represents a classification category in the chart of accounts.
    Must be one of four types: Asset, Liability, Income, Expense.
    """
    def __init__(self, ledger_id: int, name: str, type: str, is_predefined: int = 0,
                 id: Optional[int] = None,
                 creation_timestamp: Optional[str] = None,
                 modification_timestamp: Optional[str] = None):
        super().__init__(id, creation_timestamp, modification_timestamp)
        self.ledger_id = ledger_id
        self.name = name
        self.type = type # ENUM('ASSET', 'LIABILITY', 'INCOME', 'EXPENSE')
        self.is_predefined = is_predefined # 0 or 1

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "ledger_id": self.ledger_id,
            "name": self.name,
            "type": self.type,
            "is_predefined": self.is_predefined
        })
        return data

    def __repr__(self) -> str:
        return f"Account(id={self.id}, name='{self.name}', type='{self.type}', ledger_id={self.ledger_id})"