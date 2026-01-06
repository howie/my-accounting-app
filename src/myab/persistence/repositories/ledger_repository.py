from typing import List, Optional
import sqlite3
from src.myab.models.ledger import Ledger
from src.myab.persistence.database import get_db_connection

class LedgerRepository:
    def __init__(self, db_file: str, conn: Optional[sqlite3.Connection] = None):
        self.db_file = db_file
        self._conn = conn

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn:
            return self._conn
        return get_db_connection(self.db_file)

    def _execute_query(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        if not self._conn:
             conn.commit()
             conn.close()
        elif conn.in_transaction:
             conn.commit()
        return cursor

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Ledger]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not self._conn:
            conn.close()
        return Ledger(**row) if row else None

    def _fetch_all(self, query: str, params: tuple = ()) -> List[Ledger]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if not self._conn:
            conn.close()
        return [Ledger(**row) for row in rows]

    def add(self, ledger: Ledger) -> Ledger:
        query = """
            INSERT INTO ledger (user_account_id, name, creation_date, creation_timestamp, modification_timestamp)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor = self._execute_query(query, (
            ledger.user_account_id,
            ledger.name,
            ledger.creation_date,
            ledger.creation_timestamp,
            ledger.modification_timestamp
        ))
        ledger.id = cursor.lastrowid
        return ledger

    def get_by_id(self, ledger_id: int) -> Optional[Ledger]:
        query = "SELECT * FROM ledger WHERE id = ?"
        return self._fetch_one(query, (ledger_id,))

    def get_by_user_account_id(self, user_account_id: int) -> List[Ledger]:
        query = "SELECT * FROM ledger WHERE user_account_id = ?"
        return self._fetch_all(query, (user_account_id,))

    def update(self, ledger: Ledger) -> bool:
        query = """
            UPDATE ledger
            SET user_account_id = ?, name = ?, creation_date = ?, modification_timestamp = ?
            WHERE id = ?
        """
        ledger.modification_timestamp = sqlite3.Timestamp.now().isoformat()
        cursor = self._execute_query(query, (
            ledger.user_account_id,
            ledger.name,
            ledger.creation_date,
            ledger.modification_timestamp,
            ledger.id
        ))
        return cursor.rowcount > 0

    def delete(self, ledger_id: int) -> bool:
        query = "DELETE FROM ledger WHERE id = ?"
        cursor = self._execute_query(query, (ledger_id,))
        return cursor.rowcount > 0