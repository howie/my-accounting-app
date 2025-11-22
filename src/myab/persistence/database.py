import sqlite3
import os
from pathlib import Path

class Database:
    def __init__(self, db_path: str = "myab.db"):
        self.db_path = db_path
        self._conn = None

    def get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON")
        return self._conn

    def init_schema(self, schema_path: str = None):
        if schema_path is None:
            # Default to schema.sql in same directory
            schema_path = Path(__file__).parent / "schema.sql"
        
        conn = self.get_connection()
        with open(schema_path, "r") as f:
            schema_sql = f.read()
            conn.executescript(schema_sql)
        conn.commit()

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None
