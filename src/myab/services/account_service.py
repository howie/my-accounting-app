from typing import List, Optional
from src.myab.models.account import Account
from src.myab.persistence.repositories.account_repository import AccountRepository

class AccountService:
    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository

    def create_account(self, ledger_id: int, name: str, account_type: str) -> Account:
        # FR-003a: System MUST automatically prepend the appropriate prefix
        prefixed_name = f"{account_type[0].upper()}-{name}"
        new_account = Account(
            ledger_id=ledger_id,
            name=prefixed_name,
            type=account_type,
            is_predefined=0
        )
        return self.account_repository.add(new_account)

    def create_initial_accounts(self, ledger_id: int, initial_cash_amount: float):
        # FR-004: System MUST prevent deletion of two predefined accounts: "Cash" (Asset) and "Equity" (Asset)
        cash_account = Account(
            ledger_id=ledger_id,
            name="A-Cash",
            type="ASSET",
            is_predefined=1
        )
        equity_account = Account(
            ledger_id=ledger_id,
            name="Equity",
            type="EQUITY", # Assuming 'EQUITY' is a valid type in the enum, or treated specially
            is_predefined=1
        )
        self.account_repository.add(cash_account)
        self.account_repository.add(equity_account)

        # In a full implementation, initial_cash_amount would involve creating an initial transaction
        # between the Cash account and Equity account. For now, we just create the accounts.

    def list_accounts(self, ledger_id: int) -> List[Account]:
        return self.account_repository.get_by_ledger_id(ledger_id)

    def get_account(self, account_id: int) -> Optional[Account]:
        return self.account_repository.get_by_id(account_id)

    def update_account(self, account: Account) -> bool:
        # Logic for renaming/updating accounts (FR-015)
        # Ensure account_type cannot be changed directly after creation if it's tied to prefix
        return self.account_repository.update(account)

    def delete_account(self, account_id: int) -> bool:
        account_to_delete = self.account_repository.get_by_id(account_id)
        if not account_to_delete:
            return False

        # FR-004: Prevent deletion of predefined accounts
        if account_to_delete.is_predefined:
            # Optionally raise an exception or return a specific error code
            return False

        # TODO: Check for associated transactions before deletion (as per spec)
        # This will require a dependency on TransactionRepository/Service

        return self.account_repository.delete(account_id)
