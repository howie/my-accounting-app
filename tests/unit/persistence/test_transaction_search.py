import pytest
import sqlite3
from src.myab.persistence.repositories.transaction_repository import TransactionRepository
from src.myab.persistence.database import initialize_database, get_db_connection
from src.myab.models.transaction import Transaction
from src.myab.models.account import Account
from src.myab.models.ledger import Ledger
from src.myab.models.user_account import UserAccount

@pytest.fixture
def in_memory_db():
    """Provides an in-memory SQLite database connection for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    # Manually create schema since initialize_database expects a file path
    schema_sql = """
    CREATE TABLE IF NOT EXISTS user_account (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        creation_timestamp TEXT NOT NULL,
        modification_timestamp TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_account_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        creation_date TEXT NOT NULL,
        creation_timestamp TEXT NOT NULL,
        modification_timestamp TEXT NOT NULL,
        FOREIGN KEY (user_account_id) REFERENCES user_account (id)
    );
    CREATE TABLE IF NOT EXISTS account (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ledger_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        is_predefined INTEGER NOT NULL DEFAULT 0,
        creation_timestamp TEXT NOT NULL,
        modification_timestamp TEXT NOT NULL,
        FOREIGN KEY (ledger_id) REFERENCES ledger (id)
    );
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ledger_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        type TEXT NOT NULL,
        amount INTEGER NOT NULL,
        debit_account_id INTEGER NOT NULL,
        credit_account_id INTEGER NOT NULL,
        description TEXT,
        invoice_number TEXT,
        creation_timestamp TEXT NOT NULL,
        modification_timestamp TEXT NOT NULL,
        FOREIGN KEY (ledger_id) REFERENCES ledger (id),
        FOREIGN KEY (debit_account_id) REFERENCES account (id),
        FOREIGN KEY (credit_account_id) REFERENCES account (id)
    );
    """
    conn.executescript(schema_sql)
    return conn

@pytest.fixture
def setup_data(in_memory_db):
    """Inserts test data into the in-memory database."""
    cursor = in_memory_db.cursor()
    
    # User
    cursor.execute("INSERT INTO user_account (username, password_hash, creation_timestamp, modification_timestamp) VALUES (?, ?, ?, ?)",
                   ("testuser", "hashed", "2023-01-01T00:00:00", "2023-01-01T00:00:00"))
    user_id = cursor.lastrowid

    # Ledger
    cursor.execute("INSERT INTO ledger (user_account_id, name, creation_date, creation_timestamp, modification_timestamp) VALUES (?, ?, ?, ?, ?)",
                   (user_id, "Test Ledger", "2023-01-01", "2023-01-01T00:00:00", "2023-01-01T00:00:00"))
    ledger_id = cursor.lastrowid

    # Accounts
    cursor.execute("INSERT INTO account (ledger_id, name, type, is_predefined, creation_timestamp, modification_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (ledger_id, "A-Cash", "ASSET", 1, "2023-01-01T00:00:00", "2023-01-01T00:00:00"))
    cash_id = cursor.lastrowid
    cursor.execute("INSERT INTO account (ledger_id, name, type, is_predefined, creation_timestamp, modification_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (ledger_id, "E-Food", "EXPENSE", 0, "2023-01-01T00:00:00", "2023-01-01T00:00:00"))
    food_id = cursor.lastrowid
    cursor.execute("INSERT INTO account (ledger_id, name, type, is_predefined, creation_timestamp, modification_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (ledger_id, "I-Salary", "INCOME", 0, "2023-01-01T00:00:00", "2023-01-01T00:00:00"))
    salary_id = cursor.lastrowid
    cursor.execute("INSERT INTO account (ledger_id, name, type, is_predefined, creation_timestamp, modification_timestamp) VALUES (?, ?, ?, ?, ?, ?)",
                   (ledger_id, "A-Bank", "ASSET", 0, "2023-01-01T00:00:00", "2023-01-01T00:00:00"))
    bank_id = cursor.lastrowid

    # Transactions
    transactions_data = [
        (ledger_id, "2023-01-10", "EXPENSE", 5000, food_id, cash_id, "Lunch at local cafe", None, "2023-01-10T12:00:00", "2023-01-10T12:00:00"),
        (ledger_id, "2023-01-15", "EXPENSE", 3500, food_id, cash_id, "Dinner with friends", None, "2023-01-15T19:00:00", "2023-01-15T19:00:00"),
        (ledger_id, "2023-02-05", "INCOME", 200000, cash_id, salary_id, "Monthly Salary", "INV001", "2023-02-05T09:00:00", "2023-02-05T09:00:00"),
        (ledger_id, "2023-02-10", "EXPENSE", 12000, food_id, bank_id, "Groceries for the week", None, "2023-02-10T14:00:00", "2023-02-10T14:00:00"),
        (ledger_id, "2023-03-01", "TRANSFER", 100000, bank_id, cash_id, "Cash deposit", None, "2023-03-01T10:00:00", "2023-03-01T10:00:00"),
    ]
    cursor.executemany(
        """
        INSERT INTO transactions (ledger_id, date, type, amount, debit_account_id, credit_account_id,
                                 description, invoice_number, creation_timestamp, modification_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        transactions_data
    )
    in_memory_db.commit()
    
    return {
        "ledger_id": ledger_id,
        "cash_id": cash_id,
        "food_id": food_id,
        "salary_id": salary_id,
        "bank_id": bank_id
    }

@pytest.fixture
def transaction_repo_with_data(in_memory_db):
    """Provides a TransactionRepository instance with pre-populated data."""
    repo = TransactionRepository(":memory:", conn=in_memory_db) # Pass the connection directly
    return repo


def test_search_by_description(transaction_repo_with_data, setup_data):
    repo = transaction_repo_with_data
    ledger_id = setup_data["ledger_id"]
    
    results = repo.search_transactions(ledger_id, description_keyword="lunch")
    assert len(results) == 1
    assert "Lunch at local cafe" in results[0].description

    results = repo.search_transactions(ledger_id, description_keyword="friends")
    assert len(results) == 1
    assert "Dinner with friends" in results[0].description

    results = repo.search_transactions(ledger_id, description_keyword="salary")
    assert len(results) == 1
    assert "Monthly Salary" in results[0].description

def test_filter_by_account(transaction_repo_with_data, setup_data):
    repo = transaction_repo_with_data
    ledger_id = setup_data["ledger_id"]
    food_id = setup_data["food_id"]
    
    results = repo.search_transactions(ledger_id, account_id=food_id)
    assert len(results) == 3 # 2 expenses (food->cash, food->bank), 1 expense (food->bank)

def test_filter_by_date_range(transaction_repo_with_data, setup_data):
    repo = transaction_repo_with_data
    ledger_id = setup_data["ledger_id"]
    
    results = repo.search_transactions(ledger_id, start_date="2023-02-01", end_date="2023-02-28")
    assert len(results) == 2 # Salary and Groceries

    results = repo.search_transactions(ledger_id, start_date="2023-01-01", end_date="2023-01-31")
    assert len(results) == 2 # Lunch, Dinner

def test_combined_search_and_filter(transaction_repo_with_data, setup_data):
    repo = transaction_repo_with_data
    ledger_id = setup_data["ledger_id"]
    cash_id = setup_data["cash_id"]
    
    results = repo.search_transactions(ledger_id, description_keyword="cafe", account_id=cash_id)
    assert len(results) == 1 # Lunch at local cafe (debit food, credit cash)

    results = repo.search_transactions(ledger_id, description_keyword="salary", account_id=cash_id, start_date="2023-02-01")
    assert len(results) == 1 # Monthly Salary
