from decimal import Decimal
from typing import List
from myab.models.ledger import Ledger
from myab.models.account import Account, AccountType
from myab.persistence.repositories.ledger_repository import LedgerRepository
from myab.persistence.repositories.account_repository import AccountRepository
from myab.persistence.repositories.transaction_repository import TransactionRepository

class LedgerService:
    def __init__(self, repo: LedgerRepository, account_repo: AccountRepository, transaction_repo: TransactionRepository):
        self.repo = repo
        self.account_repo = account_repo
        self.transaction_repo = transaction_repo

    def create_ledger(self, user_id: int, name: str, initial_cash: Decimal = Decimal("0.00")) -> int:
        ledger_id = self.repo.create(Ledger(user_account_id=user_id, name=name))
        
        # Default Accounts
        self.account_repo.create(Account(
            ledger_id=ledger_id, 
            name="A-Cash", 
            type=AccountType.ASSET,
            initial_balance=initial_cash
        ))
        self.account_repo.create(Account(
            ledger_id=ledger_id, 
            name="A-Equity", 
            type=AccountType.ASSET,
            initial_balance=Decimal("0.00") # Or balancing amount? For MVP, just 0.
        ))
        return ledger_id

    def get_ledger(self, ledger_id: int) -> Ledger:
        return self.repo.get_by_id(ledger_id)

    def list_ledgers(self, user_id: int) -> List[Ledger]:
        return self.repo.list_by_user(user_id)
