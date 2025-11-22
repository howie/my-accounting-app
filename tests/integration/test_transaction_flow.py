import pytest
from decimal import Decimal
from datetime import date
from myab.services.transaction_service import TransactionService
from myab.services.account_service import AccountService
from myab.services.ledger_service import LedgerService
from myab.services.user_account_service import UserAccountService
from myab.persistence.repositories.transaction_repository import TransactionRepository
from myab.persistence.repositories.account_repository import AccountRepository
from myab.persistence.repositories.ledger_repository import LedgerRepository
from myab.persistence.repositories.user_account_repository import UserAccountRepository

def test_transaction_flow(test_db):
    conn = test_db.get_connection()
    
    # Setup Repos
    txn_repo = TransactionRepository(conn)
    acc_repo = AccountRepository(conn)
    ledger_repo = LedgerRepository(conn)
    user_repo = UserAccountRepository(conn)
    
    # Setup Services
    acc_service = AccountService(acc_repo)
    txn_service = TransactionService(txn_repo, acc_repo)
    
    # 1. Setup Data
    user_repo.create(user_repo._map_row({'id':1, 'username':'u', 'password_hash':'p'})) # Quick hack or use service
    # Better use proper create
    conn.execute("INSERT INTO user_accounts (username, password_hash) VALUES ('u', 'p')")
    conn.execute("INSERT INTO ledgers (user_account_id, name) VALUES (1, 'L1')")
    ledger_id = 1
    
    cash_id = acc_service.create_account(ledger_id, "Cash", "Asset", Decimal("100.00"))
    food_id = acc_service.create_account(ledger_id, "Food", "Expense", Decimal("0.00"))
    
    # 2. Record Expense: 20.00 for Food (Debit Food, Credit Cash)
    txn_service.record_transaction(
        ledger_id=ledger_id,
        date=date(2024, 1, 1),
        type="Expense",
        debit_account_id=food_id,
        credit_account_id=cash_id,
        amount=Decimal("20.00"),
        description="Lunch"
    )
    
    # 3. Verify Balances
    # Cash: 100 - 20 = 80
    # Food: 0 + 20 = 20
    
    # AccountService needs update to calculate balance from transactions!
    # Currently it only returns initial_balance.
    # T039 is "Update AccountService to support balance calculation requests".
    # So this test expects that update.
    
    cash_bal = acc_service.get_account_balance(cash_id)
    # This assertion will FAIL until T039 is done
    assert cash_bal == Decimal("80.00")
    
    food_bal = acc_service.get_account_balance(food_id)
    assert food_bal == Decimal("20.00")
