import sqlite3
from typing import Optional
from myab.models.user_account import UserAccount

class UserAccountRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, user: UserAccount) -> int:
        try:
            cursor = self.conn.execute(
                "INSERT INTO user_accounts (username, password_hash) VALUES (?, ?)",
                (user.username, user.password_hash)
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"User {user.username} already exists")

    def get_by_username(self, username: str) -> Optional[UserAccount]:
        cursor = self.conn.execute(
            "SELECT * FROM user_accounts WHERE username = ?", (username,)
        )
        row = cursor.fetchone()
        if row:
            return self._map_row(row)
        return None

    def get_by_id(self, user_id: int) -> Optional[UserAccount]:
        cursor = self.conn.execute(
            "SELECT * FROM user_accounts WHERE id = ?", (user_id,)
        )
        row = cursor.fetchone()
        if row:
            return self._map_row(row)
        return None

    def _map_row(self, row) -> UserAccount:
        return UserAccount(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash']
            # Datetime conversion can be added here
        )
