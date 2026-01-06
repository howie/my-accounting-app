from typing import Optional
from src.myab.models.base import BaseModel

class Transaction(BaseModel):
    """
    Represents a financial event recorded using double-entry bookkeeping.
    Every transaction has exactly two sides (debit and credit) affecting two different accounts.
    """
    def __init__(self, ledger_id: int, date: str, type: str, amount: int,
                 debit_account_id: int, credit_account_id: int,
                 description: Optional[str] = None, invoice_number: Optional[str] = None,
                 id: Optional[int] = None,
                 creation_timestamp: Optional[str] = None,
                 modification_timestamp: Optional[str] = None):
        super().__init__(id, creation_timestamp, modification_timestamp)
        self.ledger_id = ledger_id
        self.date = date # ISO 8601 format
        self.type = type # ENUM('EXPENSE', 'INCOME', 'TRANSFER')
        self.amount = amount # Stored in cents
        self.debit_account_id = debit_account_id
        self.credit_account_id = credit_account_id
        self.description = description
        self.invoice_number = invoice_number

    def to_dict(self) -> dict:
        data = super().to_dict()
        data.update({
            "ledger_id": self.ledger_id,
            "date": self.date,
            "type": self.type,
            "amount": self.amount,
            "debit_account_id": self.debit_account_id,
            "credit_account_id": self.credit_account_id,
            "description": self.description,
            "invoice_number": self.invoice_number
        })
        return data

    def __repr__(self) -> str:
        return (f"Transaction(id={self.id}, type='{self.type}', amount={self.amount}, "
                f"debit_account_id={self.debit_account_id}, credit_account_id={self.credit_account_id})")