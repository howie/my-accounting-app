from typing import List, Optional
import sqlite3
from src.myab.models.account import Account
from src.myab.persistence.database import get_db_connection

class AccountRepository:
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

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Account]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not self._conn:
            conn.close()
        return Account(**row) if row else None

    def _fetch_all(self, query: str, params: tuple = ()) -> List[Account]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if not self._conn:
            conn.close()
        return [Account(**row) for row in rows]

    def add(self, account: Account) -> Account:
        query = """
            INSERT INTO account (ledger_id, name, type, is_predefined, creation_timestamp, modification_timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor = self._execute_query(query, (
            account.ledger_id,
            account.name,
            account.type,
            account.is_predefined,
            account.creation_timestamp,
            account.modification_timestamp
        ))
        account.id = cursor.lastrowid
        return account

    def get_by_id(self, account_id: int) -> Optional[Account]:
        query = "SELECT * FROM account WHERE id = ?"
        return self._fetch_one(query, (account_id,))

    def get_by_ledger_id(self, ledger_id: int) -> List[Account]:
        query = "SELECT * FROM account WHERE ledger_id = ?"
        return self._fetch_all(query, (ledger_id,))

    def update(self, account: Account) -> bool:
        query = """
            UPDATE account
            SET ledger_id = ?, name = ?, type = ?, is_predefined = ?, modification_timestamp = ?
            WHERE id = ?
        """
        account.modification_timestamp = sqlite3.Timestamp.now().isoformat()
        cursor = self._execute_query(query, (
            account.ledger_id,
            account.name,
            account.type,
            account.is_predefined,
            account.modification_timestamp,
            account.id
        ))
        return cursor.rowcount > 0

    def delete(self, account_id: int) -> bool:
        query = "DELETE FROM account WHERE id = ?"
        cursor = self._execute_query(query, (account_id,))
        return cursor.rowcount > 0