import pytest
from decimal import Decimal
from datetime import date
from myab.services.transaction_service import TransactionService
from myab.persistence.repositories.transaction_repository import TransactionRepository
from myab.persistence.repositories.account_repository import AccountRepository

def test_record_transaction(test_db):
    conn = test_db.get_connection()
    # Setup context
    conn.execute("INSERT INTO user_accounts (username, password_hash) VALUES ('u1', 'hash')")
    conn.execute("INSERT INTO ledgers (user_account_id, name) VALUES (1, 'L1')")
    conn.execute("INSERT INTO accounts (ledger_id, name, type, initial_balance) VALUES (1, 'A-Cash', 'Asset', '100.00')")
    conn.execute("INSERT INTO accounts (ledger_id, name, type, initial_balance) VALUES (1, 'E-Food', 'Expense', '0.00')")
    
    repo = TransactionRepository(conn)
    acc_repo = AccountRepository(conn)
    # Service needs account repo to validate accounts
    service = TransactionService(repo, acc_repo)
    
    txn_id = service.record_transaction(
        ledger_id=1,
        date=date(2024, 1, 1),
        type="Expense",
        debit_account_id=2, # E-Food
        credit_account_id=1, # A-Cash
        amount=Decimal("10.00"),
        description="Lunch"
    )
    assert isinstance(txn_id, int)
