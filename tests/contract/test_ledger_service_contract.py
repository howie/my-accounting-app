import pytest
from decimal import Decimal
from myab.services.ledger_service import LedgerService
from myab.persistence.repositories.ledger_repository import LedgerRepository
from myab.persistence.repositories.account_repository import AccountRepository
from myab.persistence.repositories.transaction_repository import TransactionRepository

def test_create_ledger(test_db):
    conn = test_db.get_connection()
    # Need a user first (foreign key)
    conn.execute("INSERT INTO user_accounts (username, password_hash) VALUES ('u1', 'hash')")
    user_id = 1
    
    repo = LedgerRepository(conn)
    acc_repo = AccountRepository(conn)
    txn_repo = TransactionRepository(conn)
    service = LedgerService(repo, acc_repo, txn_repo)
    
    ledger_id = service.create_ledger(user_id=user_id, name="My Ledger", initial_cash=Decimal("100.00"))
    assert isinstance(ledger_id, int)
    
    ledger = service.get_ledger(ledger_id)
    assert ledger.name == "My Ledger"
    assert ledger.user_account_id == user_id

def test_list_ledgers(test_db):
    conn = test_db.get_connection()
    conn.execute("INSERT INTO user_accounts (username, password_hash) VALUES ('u1', 'hash')")
    
    repo = LedgerRepository(conn)
    # Mock others if needed or use None if service handles it
    service = LedgerService(repo, None, None)
    
    ledgers = service.list_ledgers(user_id=1)
    assert isinstance(ledgers, list)
