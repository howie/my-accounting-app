from typing import List, Optional
import sqlite3
from src.myab.models.user_account import UserAccount
from src.myab.persistence.database import get_db_connection

class UserAccountRepository:
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

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[UserAccount]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not self._conn:
            conn.close()
        return UserAccount(**row) if row else None

    def _fetch_all(self, query: str, params: tuple = ()) -> List[UserAccount]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if not self._conn:
            conn.close()
        return [UserAccount(**row) for row in rows]

    def add(self, user_account: UserAccount) -> UserAccount:
        query = """
            INSERT INTO user_account (username, password_hash, creation_timestamp, modification_timestamp)
            VALUES (?, ?, ?, ?)
        """
        cursor = self._execute_query(query, (
            user_account.username,
            user_account.password_hash,
            user_account.creation_timestamp,
            user_account.modification_timestamp
        ))
        user_account.id = cursor.lastrowid
        return user_account

    def get_by_id(self, user_id: int) -> Optional[UserAccount]:
        query = "SELECT * FROM user_account WHERE id = ?"
        return self._fetch_one(query, (user_id,))

    def get_by_username(self, username: str) -> Optional[UserAccount]:
        query = "SELECT * FROM user_account WHERE username = ?"
        return self._fetch_one(query, (username,))

    def update(self, user_account: UserAccount) -> bool:
        query = """
            UPDATE user_account
            SET username = ?, password_hash = ?, modification_timestamp = ?
            WHERE id = ?
        """
        user_account.modification_timestamp = sqlite3.Timestamp.now().isoformat()
        cursor = self._execute_query(query, (
            user_account.username,
            user_account.password_hash,
            user_account.modification_timestamp,
            user_account.id
        ))
        return cursor.rowcount > 0

    def delete(self, user_id: int) -> bool:
        query = "DELETE FROM user_account WHERE id = ?"
        cursor = self._execute_query(query, (user_id,))
        return cursor.rowcount > 0