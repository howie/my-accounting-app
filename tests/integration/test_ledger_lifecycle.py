import pytest
from decimal import Decimal
from myab.persistence.repositories.user_account_repository import UserAccountRepository
from myab.persistence.repositories.ledger_repository import LedgerRepository
from myab.persistence.repositories.account_repository import AccountRepository
from myab.persistence.repositories.transaction_repository import TransactionRepository
from myab.services.user_account_service import UserAccountService
from myab.services.ledger_service import LedgerService
from myab.services.account_service import AccountService

def test_ledger_lifecycle(test_db):
    conn = test_db.get_connection()
    
    # Setup Repos
    user_repo = UserAccountRepository(conn)
    ledger_repo = LedgerRepository(conn)
    acc_repo = AccountRepository(conn)
    txn_repo = TransactionRepository(conn)
    
    # Setup Services
    user_service = UserAccountService(user_repo)
    ledger_service = LedgerService(ledger_repo, acc_repo, txn_repo)
    account_service = AccountService(acc_repo)
    
    # 1. Create User
    user_id = user_service.create_user("newuser", "pass")
    
    # 2. Create Ledger with initial cash
    ledger_id = ledger_service.create_ledger(user_id, "2024 Finances", initial_cash=Decimal("5000.00"))
    
    # 3. Verify Default Accounts
    accounts = account_service.list_accounts(ledger_id)
    names = [a.name for a in accounts]
    assert "A-Cash" in names
    assert "A-Equity" in names
    
    # 4. Verify Initial Balance
    cash_acc = next(a for a in accounts if a.name == "A-Cash")
    # Initial balance is recorded as transaction? Or just set on account?
    # Spec FR-014 says "Set initial balance".
    # LedgerService logic says "If initial_cash > 0, records initial balance transaction" (Contract).
    # Or account.initial_balance? 
    # Data model has `initial_balance` column on accounts.
    # But usually double entry means initial balance comes from Equity.
    # Contract says: "Side Effects: Creates A-Cash... A-Equity... records initial balance transaction".
    # So balance should be reflected.
    balance = account_service.get_account_balance(cash_acc.id)
    assert balance == Decimal("5000.00")
    
    # 5. Add Custom Account
    gym_id = account_service.create_account(ledger_id, "Gym", "Expense")
    gym_acc = next(a for a in account_service.list_accounts(ledger_id) if a.id == gym_id)
    assert gym_acc.name == "E-Gym"
    assert gym_acc.type == "Expense"
