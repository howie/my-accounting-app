import sqlite3
from pathlib import Path

DATABASE_FILE = "myab.db"
SCHEMA_FILE = Path(__file__).parent / "schema.sql"

def get_db_connection(db_file: str = DATABASE_FILE) -> sqlite3.Connection:
    """
    Establishes a connection to the SQLite database.
    If the database file does not exist, it will be created.
    """
    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row  # Access columns by name
    return conn

def initialize_database(db_file: str = DATABASE_FILE, schema_file: Path = SCHEMA_FILE):
    """
    Initializes the database by creating tables as defined in the schema file.
    """
    with get_db_connection(db_file) as conn:
        with open(schema_file, 'r') as f:
            conn.executescript(f.read())
    print(f"Database initialized: {db_file}")

if __name__ == "__main__":
    # Example usage:
    # Ensure the database file is in the project root as specified in .gitignore
    # For testing, you might want a different file or temporary one.
    db_path = Path.cwd() / DATABASE_FILE
    if db_path.exists():
        db_path.unlink() # Remove existing db for a clean start

    initialize_database(str(db_path))
    conn = get_db_connection(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    print("Tables created:", cursor.fetchall())
    conn.close()