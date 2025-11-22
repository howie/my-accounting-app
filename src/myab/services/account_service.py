from decimal import Decimal
from typing import List, Optional
from myab.models.account import Account, AccountType
from myab.persistence.repositories.account_repository import AccountRepository
from myab.persistence.repositories.transaction_repository import TransactionRepository

class AccountService:
    def __init__(self, repo: AccountRepository, transaction_repo: Optional[TransactionRepository] = None):
        self.repo = repo
        self.transaction_repo = transaction_repo

    def create_account(self, ledger_id: int, name: str, type: str, initial_balance: Decimal = Decimal("0.00")) -> int:
        prefix_map = {
            "Asset": "A-",
            "Liability": "L-",
            "Income": "I-",
            "Expense": "E-"
        }
        
        if type not in prefix_map:
            raise ValueError(f"Invalid account type: {type}")
            
        prefix = prefix_map[type]
        if not name.startswith(prefix):
            full_name = f"{prefix}{name}"
        else:
            full_name = name
            
        acc = Account(
            ledger_id=ledger_id,
            name=full_name,
            type=AccountType(type),
            initial_balance=initial_balance
        )
        return self.repo.create(acc)

    def list_accounts(self, ledger_id: int) -> List[Account]:
        return self.repo.list_by_ledger(ledger_id)
        
    def get_account_balance(self, account_id: int) -> Decimal:
        acc = self.repo.get_by_id(account_id)
        if not acc:
            raise ValueError("Account not found")
            
        if self.transaction_repo:
            debits, credits = self.transaction_repo.get_balance_impact(account_id)
            if acc.type in [AccountType.ASSET, AccountType.EXPENSE]:
                return acc.initial_balance + debits - credits
            else:
                return acc.initial_balance + credits - debits
        
        return acc.initial_balance
        
    def delete_account(self, account_id: int):
        acc = self.repo.get_by_id(account_id)
        if not acc:
            raise ValueError("Account not found")
        
        if acc.name in ["A-Cash", "A-Equity"]:
             raise ValueError("Cannot delete system account")
             
        self.repo.delete(account_id)