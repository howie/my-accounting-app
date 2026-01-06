from typing import Optional
from src.myab.models.account import Account
from src.myab.persistence.repositories.account_repository import AccountRepository

class TransactionValidator:
    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository

    def validate_transaction(self, ledger_id: int, date: str, type: str, amount: int,
                             debit_account_id: int, credit_account_id: int,
                             allow_zero_amount: bool = False) -> tuple[bool, str]:
        """
        Validates a transaction based on business rules.
        Returns a tuple of (is_valid, message).
        """
        if amount <= 0 and not allow_zero_amount:
            return False, "Transaction amount must be positive."

        if debit_account_id == credit_account_id:
            return False, "Cannot transfer between the same account."

        debit_account = self.account_repository.get_by_id(debit_account_id)
        credit_account = self.account_repository.get_by_id(credit_account_id)

        if not debit_account or not credit_account:
            return False, "Debit or Credit account not found."
        
        if debit_account.ledger_id != ledger_id or credit_account.ledger_id != ledger_id:
            return False, "Accounts must belong to the same ledger."

        # FR-006: Transaction rules
        if type == "EXPENSE":
            if not (debit_account.type == "EXPENSE" and credit_account.type in ["ASSET", "LIABILITY"]):
                return False, "Expense transaction: debit must be EXPENSE, credit must be ASSET or LIABILITY."
        elif type == "INCOME":
            if not (debit_account.type in ["ASSET", "LIABILITY"] and credit_account.type in ["INCOME", "EQUITY"]):
                return False, "Income transaction: debit must be ASSET or LIABILITY, credit must be INCOME or EQUITY."
        elif type == "TRANSFER":
            if not (debit_account.type in ["ASSET", "LIABILITY"] and credit_account.type in ["ASSET", "LIABILITY"]):
                return False, "Transfer transaction: both debit and credit must be ASSET or LIABILITY."
        else:
            return False, "Invalid transaction type."

        # TODO: Add validation for unbalanced transactions (debits = credits) once this concept is clearer in current context.
        # This currently implies a single amount is provided, not separate debit/credit amounts.

        return True, "Transaction is valid."
