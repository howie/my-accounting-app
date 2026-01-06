import pytest
import sqlite3
from pathlib import Path
from src.myab.persistence.database import initialize_database, get_db_connection
from src.myab.persistence.repositories.ledger_repository import LedgerRepository
from src.myab.persistence.repositories.account_repository import AccountRepository
from src.myab.services.ledger_service import LedgerService
from src.myab.services.account_service import AccountService
from src.myab.persistence.repositories.transaction_repository import TransactionRepository
from src.myab.validation.validators import TransactionValidator
from src.myab.services.transaction_service import TransactionService

@pytest.fixture
def temp_db_file(tmp_path):
    """Provides a temporary database file for testing."""
    db_file = tmp_path / "test_myab.db"
    return str(db_file)

@pytest.fixture
def initialized_db(temp_db_file):
    """Initializes a temporary database with the schema."""
    initialize_database(temp_db_file)
    return temp_db_file

@pytest.fixture
def db_connection(initialized_db):
    """Provides a database connection to the initialized temporary database."""
    conn = get_db_connection(initialized_db)
    yield conn
    conn.close()

@pytest.fixture
def ledger_repository(initialized_db):
    """Provides an instance of LedgerRepository."""
    return LedgerRepository(initialized_db)

@pytest.fixture
def account_repository(initialized_db):
    """Provides an instance of AccountRepository."""
    return AccountRepository(initialized_db)

@pytest.fixture
def account_service(account_repository):
    """Provides an instance of AccountService."""
    return AccountService(account_repository)

@pytest.fixture
def ledger_service(ledger_repository, account_service, transaction_service):
    """Provides an instance of LedgerService."""
    return LedgerService(ledger_repository, account_service, transaction_service)

@pytest.fixture
def transaction_repository(initialized_db):
    """Provides an instance of TransactionRepository."""
    return TransactionRepository(initialized_db)

@pytest.fixture
def transaction_validator(account_repository):
    """Provides an instance of TransactionValidator."""
    return TransactionValidator(account_repository)

@pytest.fixture
def transaction_service(transaction_repository, account_repository, transaction_validator):
    """Provides an instance of TransactionService."""
    return TransactionService(transaction_repository, account_repository, transaction_validator)


# Add a dummy user account for tests requiring a user_account_id
@pytest.fixture
def dummy_user_id(db_connection):
    cursor = db_connection.cursor()
    # Provide values for creation_timestamp and modification_timestamp
    now = sqlite3.Timestamp.now().isoformat()
    cursor.execute(
        "INSERT INTO user_account (username, password_hash, creation_timestamp, modification_timestamp) VALUES (?, ?, ?, ?)",
        ("testuser_conftest", "hashed_password_conftest", now, now)
    )
    db_connection.commit()
    return cursor.lastrowid

@pytest.fixture
def user_account_repository(initialized_db):
    """Provides an instance of UserAccountRepository."""
    return UserAccountRepository(initialized_db)

@pytest.fixture
def user_account_service(user_account_repository):
    """Provides an instance of UserAccountService."""
    return UserAccountService(user_account_repository)

