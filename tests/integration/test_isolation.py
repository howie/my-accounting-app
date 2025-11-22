import pytest
from decimal import Decimal
from myab.persistence.repositories.user_account_repository import UserAccountRepository
from myab.persistence.repositories.ledger_repository import LedgerRepository
from myab.persistence.repositories.account_repository import AccountRepository
from myab.persistence.repositories.transaction_repository import TransactionRepository
from myab.services.user_account_service import UserAccountService
from myab.services.ledger_service import LedgerService
from myab.services.account_service import AccountService
from myab.services.transaction_service import TransactionService

def test_ledger_isolation(test_db):
    conn = test_db.get_connection()
    # Repos & Services
    user_repo = UserAccountRepository(conn)
    ledger_repo = LedgerRepository(conn)
    acc_repo = AccountRepository(conn)
    txn_repo = TransactionRepository(conn)
    
    user_service = UserAccountService(user_repo)
    ledger_service = LedgerService(ledger_repo, acc_repo, txn_repo)
    acc_service = AccountService(acc_repo, txn_repo)
    
    # 1. Setup
    user_id = user_service.create_user("u1", "p")
    l1_id = ledger_service.create_ledger(user_id, "L1")
    l2_id = ledger_service.create_ledger(user_id, "L2")
    
    # 2. Verify Accounts Isolated
    l1_accounts = acc_service.list_accounts(l1_id)
    l2_accounts = acc_service.list_accounts(l2_id)
    # Both have Cash/Equity but IDs should be different
    l1_cash = next(a for a in l1_accounts if a.name == "A-Cash")
    l2_cash = next(a for a in l2_accounts if a.name == "A-Cash")
    assert l1_cash.id != l2_cash.id
    
    # 3. Verify Transactions Isolated
    # (Assuming we add transaction service usage here later)
    # For now, just account name uniqueness check per ledger
    
    # Create custom account "Bank" in L1
    acc_service.create_account(l1_id, "Bank", "Asset")
    # Create custom account "Bank" in L2
    acc_service.create_account(l2_id, "Bank", "Asset")
    
    l1_bank = next(a for a in acc_service.list_accounts(l1_id) if a.name == "A-Bank")
    l2_bank = next(a for a in acc_service.list_accounts(l2_id) if a.name == "A-Bank")
    assert l1_bank.id != l2_bank.id
