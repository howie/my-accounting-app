import pytest
from datetime import date
from decimal import Decimal
from myab.persistence.repositories.transaction_repository import TransactionRepository
from myab.models.transaction import Transaction

def test_search_transactions(test_db):
    conn = test_db.get_connection()
    repo = TransactionRepository(conn)
    
    # Setup
    conn.execute("INSERT INTO user_accounts (username, password_hash) VALUES ('u', 'p')")
    conn.execute("INSERT INTO ledgers (user_account_id, name) VALUES (1, 'L1')")
    # Accounts
    
    txn1 = Transaction(
        ledger_id=1,
        date=date(2024, 1, 1),
        type="Expense",
        debit_account_id=1, credit_account_id=2, amount=Decimal("10"), description="Lunch at Cafe"
    )
    repo.create(txn1)
    
    txn2 = Transaction(
        ledger_id=1,
        date=date(2024, 1, 2),
        type="Expense",
        debit_account_id=1, credit_account_id=2, amount=Decimal("20"), description="Dinner"
    )
    repo.create(txn2)
    
    results = repo.search(ledger_id=1, query="Lunch")
    assert len(results) == 1
    assert results[0].description == "Lunch at Cafe"
