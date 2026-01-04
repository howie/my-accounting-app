from typing import List, Optional
from datetime import datetime
from src.myab.models.ledger import Ledger
from src.myab.persistence.repositories.ledger_repository import LedgerRepository
from src.myab.services.account_service import AccountService
from src.myab.services.transaction_service import TransactionService # New import

class LedgerService:
    def __init__(self, ledger_repository: LedgerRepository,
                 account_service: AccountService,
                 transaction_service: TransactionService): # New dependency
        self.ledger_repository = ledger_repository
        self.account_service = account_service
        self.transaction_service = transaction_service # Store new dependency

    def create_ledger(self, user_account_id: int, name: str, initial_cash_amount: float) -> Ledger:
        new_ledger = Ledger(
            user_account_id=user_account_id,
            name=name,
            creation_date=datetime.now().isoformat() # Store as ISO 8601 string
        )
        created_ledger = self.ledger_repository.add(new_ledger)

        # Create initial Cash and Equity accounts for the new ledger
        self.account_service.create_initial_accounts(created_ledger.id, initial_cash_amount)

        # Find the Cash and Equity accounts to create the initial transaction
        accounts = self.account_service.list_accounts(created_ledger.id)
        cash_account = next(acc for acc in accounts if acc.name == "A-Cash")
        equity_account = next(acc for acc in accounts if acc.name == "Equity")

        # Create an initial transaction to set the cash balance
        if initial_cash_amount > 0:
            transaction, msg = self.transaction_service.create_transaction(
                ledger_id=created_ledger.id,
                date=created_ledger.creation_date, # Use ledger creation date
                type="INCOME", # Represent as an initial income
                amount=int(initial_cash_amount), # Assuming amount is in cents
                debit_account_id=cash_account.id,
                credit_account_id=equity_account.id, # Equity is the balancing account
                description="Initial Cash Balance",
                confirm_zero_amount=False # Not a zero amount
            )
            if not transaction:
                # Handle error if initial transaction creation fails
                print(f"Warning: Failed to create initial cash transaction: {msg}")

        return created_ledger

    def list_ledgers(self, user_account_id: int) -> List[Ledger]:
        return self.ledger_repository.get_by_user_account_id(user_account_id)

    def get_ledger(self, ledger_id: int) -> Optional[Ledger]:
        return self.ledger_repository.get_by_id(ledger_id)

    def update_ledger(self, ledger: Ledger) -> bool:
        # Before updating, perform any necessary business logic or validation
        return self.ledger_repository.update(ledger)

    def delete_ledger(self, ledger_id: int) -> bool:
        # Add checks for existing transactions or user confirmation as per spec
        # For now, just call repository delete
        return self.ledger_repository.delete(ledger_id)