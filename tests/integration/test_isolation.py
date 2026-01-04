import pytest
import sqlite3
from typing import Optional
from src.myab.persistence.database import get_db_connection
from src.myab.models.ledger import Ledger
from src.myab.models.account import Account
from src.myab.models.transaction import Transaction
from src.myab.models.user_account import UserAccount
from src.myab.services.user_account_service import UserAccountService # Will be implemented soon
from src.myab.services.ledger_service import LedgerService
from src.myab.services.account_service import AccountService
from src.myab.services.transaction_service import TransactionService
from src.myab.persistence.repositories.user_account_repository import UserAccountRepository # Will be implemented soon

@pytest.fixture
def user_account_repository(initialized_db):
    """Provides an instance of UserAccountRepository."""
    # This will be replaced by the actual UserAccountRepository implementation
    class MockUserAccountRepository:
        def __init__(self, db_file):
            self.db_file = db_file
        
        def add(self, user_account: UserAccount) -> UserAccount:
            conn = get_db_connection(self.db_file)
            cursor = conn.cursor()
            now = sqlite3.Timestamp.now().isoformat()
            cursor.execute(
                "INSERT INTO user_account (username, password_hash, creation_timestamp, modification_timestamp) VALUES (?, ?, ?, ?)",
                (user_account.username, user_account.password_hash, now, now)
            )
            conn.commit()
            user_account.id = cursor.lastrowid
            conn.close()
            return user_account
        
        def get_by_id(self, user_id: int) -> Optional[UserAccount]:
            conn = get_db_connection(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_account WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            return UserAccount(**row) if row else None
        
        def get_by_username(self, username: str) -> Optional[UserAccount]:
            conn = get_db_connection(self.db_file)
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_account WHERE username = ?", (username,))
            row = cursor.fetchone()
            conn.close()
            return UserAccount(**row) if row else None
    return MockUserAccountRepository(initialized_db)


@pytest.fixture
def user_account_service(user_account_repository):
    """Provides an instance of UserAccountService."""
    return UserAccountService(user_account_repository)

def test_ledger_data_isolation(user_account_service: UserAccountService, ledger_service: LedgerService, 
                                account_service: AccountService, transaction_service: TransactionService, 
                                initialized_db: str):
    
    # Create two user accounts
    user1, msg1 = user_account_service.create_user_account("user1", "hash1")
    user2, msg2 = user_account_service.create_user_account("user2", "hash2")
    assert user1 is not None and user2 is not None, f"User creation failed: {msg1}, {msg2}"

    # User 1 creates two ledgers
    ledger1_user1 = ledger_service.create_ledger(user1.id, "User1_LedgerA", 10000)
    ledger2_user1 = ledger_service.create_ledger(user1.id, "User1_LedgerB", 20000)
    assert ledger1_user1 is not None and ledger2_user1 is not None

    # User 2 creates one ledger
    ledger1_user2 = ledger_service.create_ledger(user2.id, "User2_LedgerA", 30000)
    assert ledger1_user2 is not None

    # Add accounts and transactions to Ledger 1 (User 1)
    acc1_l1 = account_service.create_account(ledger1_user1.id, "Expense1", "EXPENSE")
    acc2_l1 = account_service.create_account(ledger1_user1.id, "Cash", "ASSET")
    trans1_l1, msg = transaction_service.create_transaction(ledger1_user1.id, "2023-01-01", "EXPENSE", 1000, acc1_l1.id, acc2_l1.id)
    assert trans1_l1 is not None

    # Add accounts and transactions to Ledger 2 (User 1)
    acc1_l2 = account_service.create_account(ledger2_user1.id, "Income1", "INCOME")
    acc2_l2 = account_service.create_account(ledger2_user1.id, "Bank", "ASSET")
    trans1_l2, msg = transaction_service.create_transaction(ledger2_user1.id, "2023-01-01", "INCOME", 5000, acc2_l2.id, acc1_l2.id)
    assert trans1_l2 is not None

    # Add accounts and transactions to Ledger 1 (User 2)
    acc1_l1_u2 = account_service.create_account(ledger1_user2.id, "ExpenseX", "EXPENSE")
    acc2_l1_u2 = account_service.create_account(ledger1_user2.id, "Credit", "LIABILITY")
    trans1_l1_u2, msg = transaction_service.create_transaction(ledger1_user2.id, "2023-01-01", "EXPENSE", 2000, acc1_l1_u2.id, acc2_l1_u2.id)
    assert trans1_l1_u2 is not None

    # Verify data isolation for ledgers of User 1
    user1_ledgers = ledger_service.list_ledgers(user1.id)
    assert len(user1_ledgers) == 2
    user1_ledger_names = {l.name for l in user1_ledgers}
    assert "User1_LedgerA" in user1_ledger_names
    assert "User1_LedgerB" in user1_ledger_names
    assert "User2_LedgerA" not in user1_ledger_names

    # Verify accounts are isolated
    accounts_l1 = account_service.list_accounts(ledger1_user1.id)
    assert any(acc.name == "E-Expense1" for acc in accounts_l1)
    assert not any(acc.name == "I-Income1" for acc in accounts_l1)
    assert not any(acc.name == "E-ExpenseX" for acc in accounts_l1)

    accounts_l2 = account_service.list_accounts(ledger2_user1.id)
    assert any(acc.name == "I-Income1" for acc in accounts_l2)
    assert not any(acc.name == "E-Expense1" for acc in accounts_l2)
    assert not any(acc.name == "E-ExpenseX" for acc in accounts_l2)

    # Verify transactions are isolated (e.g., query for transactions in ledger1_user1)
    # This will require search_transactions method in TransactionService (Phase 5)
    # For now, we can check by querying the database directly if needed, but this test relies on TransactionService
    conn = get_db_connection(initialized_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE ledger_id = ?", (ledger1_user1.id,))
    assert cursor.fetchone()[0] > 0
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE ledger_id = ?", (ledger1_user2.id,))
    assert cursor.fetchone()[0] > 0
    
    # Attempt to retrieve a transaction from ledger1_user1 via ledger1_user2's account (should fail)
    # This is more service-level.
    # For now, just ensure that a list of transactions from one ledger doesn't contain transactions from another.
    transactions_l1_u1 = transaction_service.transaction_repository.get_by_ledger_id(ledger1_user1.id)
    transactions_l2_u1 = transaction_service.transaction_repository.get_by_ledger_id(ledger2_user1.id)
    transactions_l1_u2 = transaction_service.transaction_repository.get_by_ledger_id(ledger1_user2.id)

    assert trans1_l1 in transactions_l1_u1
    assert trans1_l2 in transactions_l2_u1
    assert trans1_l1_u2 in transactions_l1_u2

    assert trans1_l1 not in transactions_l2_u1
    assert trans1_l1 not in transactions_l1_u2
    
    # Verify user account isolation (listing ledgers for user2)
    user2_ledgers = ledger_service.list_ledgers(user2.id)
    assert len(user2_ledgers) == 1
    assert user2_ledgers[0].name == "User2_LedgerA"
    assert "User1_LedgerA" not in {l.name for l in user2_ledgers}
    
    conn.close()
