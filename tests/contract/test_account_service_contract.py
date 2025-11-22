import pytest
from decimal import Decimal
from myab.services.account_service import AccountService
from myab.persistence.repositories.account_repository import AccountRepository

def test_create_account(test_db):
    conn = test_db.get_connection()
    conn.execute("INSERT INTO user_accounts (username, password_hash) VALUES ('u1', 'hash')")
    conn.execute("INSERT INTO ledgers (user_account_id, name) VALUES (1, 'L1')")
    ledger_id = 1
    
    repo = AccountRepository(conn)
    service = AccountService(repo)
    
    acc_id = service.create_account(ledger_id, "Bank", "Asset")
    assert isinstance(acc_id, int)
    
    accounts = service.list_accounts(ledger_id)
    assert len(accounts) > 0
    assert accounts[0].name == "A-Bank" # Auto-prefix check contract

def test_account_balance(test_db):
    conn = test_db.get_connection()
    conn.execute("INSERT INTO user_accounts (username, password_hash) VALUES ('u1', 'hash')")
    conn.execute("INSERT INTO ledgers (user_account_id, name) VALUES (1, 'L1')")
    conn.execute("INSERT INTO accounts (ledger_id, name, type, initial_balance) VALUES (1, 'A-Cash', 'Asset', '100.00')")
    acc_id = 1
    
    repo = AccountRepository(conn)
    service = AccountService(repo)
    
    balance = service.get_account_balance(acc_id)
    assert balance == Decimal("100.00")
