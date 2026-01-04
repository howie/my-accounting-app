from typing import List, Optional
from datetime import datetime
from src.myab.models.transaction import Transaction
from src.myab.models.account import Account
from src.myab.persistence.repositories.transaction_repository import TransactionRepository
from src.myab.persistence.repositories.account_repository import AccountRepository
from src.myab.validation.validators import TransactionValidator

class TransactionService:
    def __init__(self, transaction_repository: TransactionRepository,
                 account_repository: AccountRepository,
                 validator: TransactionValidator):
        self.transaction_repository = transaction_repository
        self.account_repository = account_repository
        self.validator = validator

    def create_transaction(self, ledger_id: int, date: str, type: str, amount: int,
                           debit_account_id: int, credit_account_id: int,
                           description: Optional[str] = None, invoice_number: Optional[str] = None,
                           confirm_zero_amount: bool = False) -> tuple[Optional[Transaction], str]:
        """
        Creates a new transaction after validation.
        Returns a tuple of (created_transaction, message).
        """
        is_valid, validation_message = self.validator.validate_transaction(
            ledger_id, date, type, amount, debit_account_id, credit_account_id,
            allow_zero_amount=confirm_zero_amount # Pass flag for zero amount
        )

        if not is_valid:
            return None, validation_message
        
        # If amount is zero and it was not explicitly confirmed, return a warning
        if amount == 0 and not confirm_zero_amount:
            return None, "Confirm zero-amount transaction before saving."

        new_transaction = Transaction(
            ledger_id=ledger_id, date=date, type=type, amount=amount,
            debit_account_id=debit_account_id, credit_account_id=credit_account_id,
            description=description, invoice_number=invoice_number,
            creation_timestamp=datetime.now().isoformat(),
            modification_timestamp=datetime.now().isoformat()
        )
        created_transaction = self.transaction_repository.add(new_transaction)
        return created_transaction, "Transaction created successfully."

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        return self.transaction_repository.get_by_id(transaction_id)

    def update_transaction(self, transaction: Transaction) -> tuple[bool, str]:
        """
        Updates an existing transaction after validation.
        Returns a tuple of (is_successful, message).
        """
        # For simplicity, re-validate entire transaction on update
        is_valid, validation_message = self.validator.validate_transaction(
            transaction.ledger_id, transaction.date, transaction.type, transaction.amount,
            transaction.debit_account_id, transaction.credit_account_id
        )
        if not is_valid:
            return False, validation_message

        transaction.modification_timestamp = datetime.now().isoformat()
        if self.transaction_repository.update(transaction):
            return True, "Transaction updated successfully."
        return False, "Failed to update transaction."

    def delete_transaction(self, transaction_id: int) -> tuple[bool, str]:
        """
        Deletes a transaction.
        Returns a tuple of (is_successful, message).
        """
        if self.transaction_repository.delete(transaction_id):
            return True, "Transaction deleted successfully."
        return False, "Failed to delete transaction."

    def calculate_account_balance(self, account_id: int) -> int:
        """
        Calculates the current balance for a given account based on all related transactions.
        Balance is in cents.
        """
        transactions = self.transaction_repository.get_transactions_for_account(account_id)
        account = self.account_repository.get_by_id(account_id)
        if not account:
            return 0 # Account not found

        balance = 0
        for transaction in transactions:
            if transaction.debit_account_id == account_id:
                if account.type in ["ASSET", "EXPENSE"]: # Debiting an asset/expense increases its value/expense
                    balance += transaction.amount
                elif account.type in ["LIABILITY", "INCOME", "EQUITY"]: # Debiting a liability/income/equity decreases its value
                    balance -= transaction.amount
            elif transaction.credit_account_id == account_id:
                if account.type in ["ASSET", "EXPENSE"]: # Crediting an asset/expense decreases its value/expense
                    balance -= transaction.amount
                elif account.type in ["LIABILITY", "INCOME", "EQUITY"]: # Crediting a liability/income/equity increases its value
                    balance += transaction.amount
        return balance