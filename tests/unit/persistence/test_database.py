import pytest
import os
from myab.persistence.database import Database

def test_database_connection_and_schema():
    db_path = ":memory:"
    db = Database(db_path)
    conn = db.get_connection()
    assert conn is not None
    
    # Init schema
    db.init_schema()
    
    # Check if tables exist
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = ['user_accounts', 'ledgers', 'accounts', 'transactions', 'sqlite_sequence']
    for table in expected_tables:
        if table == 'sqlite_sequence': continue # Created automatically by autoincrement
        assert table in tables, f"Table {table} should exist"
        
    db.close()
