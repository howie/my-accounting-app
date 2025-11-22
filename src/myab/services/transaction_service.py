from decimal import Decimal
from datetime import date
from typing import List, Optional
from myab.models.transaction import Transaction
from myab.models.account import AccountType
from myab.persistence.repositories.transaction_repository import TransactionRepository
from myab.persistence.repositories.account_repository import AccountRepository

class TransactionService:
    def __init__(self, repo: TransactionRepository, account_repo: AccountRepository):
        self.repo = repo
        self.account_repo = account_repo

    def record_transaction(self, ledger_id: int, date: date, type: str, 
                          debit_account_id: int, credit_account_id: int, 
                          amount: Decimal, description: str) -> int:
        # Validation
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if debit_account_id == credit_account_id:
            raise ValueError("Debit and Credit accounts must be different")
            
        debit_acc = self.account_repo.get_by_id(debit_account_id)
        credit_acc = self.account_repo.get_by_id(credit_account_id)
        
        if not debit_acc or not credit_acc:
            raise ValueError("Account not found")
            
        if debit_acc.ledger_id != ledger_id or credit_acc.ledger_id != ledger_id:
            raise ValueError("Accounts must belong to the ledger")
            
        # Type Rules (Simplified for MVP)
        if type == "Expense":
            if debit_acc.type != AccountType.EXPENSE:
                 raise ValueError("Expense transaction must debit an Expense account")
        elif type == "Income":
            if credit_acc.type != AccountType.INCOME:
                 raise ValueError("Income transaction must credit an Income account")
        
        txn = Transaction(
            ledger_id=ledger_id,
            date=date,
            type=type,
            debit_account_id=debit_account_id,
            credit_account_id=credit_account_id,
            amount=amount,
            description=description
        )
        return self.repo.create(txn)

    def search_transactions(self, ledger_id: int, query: str = None, account_id: int = None) -> List[Transaction]:
        return self.repo.search(ledger_id, query, account_id)