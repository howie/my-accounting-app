import pytest
from myab.persistence.database import Database

@pytest.fixture
def test_db():
    """Returns a configured Database instance with schema initialized."""
    db = Database(":memory:")
    db.init_schema()
    return db

@pytest.fixture
def db_connection(test_db):
    """Returns a raw sqlite3 connection from the test_db."""
    return test_db.get_connection()