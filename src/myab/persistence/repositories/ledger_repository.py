import sqlite3
from typing import List, Optional
from myab.models.ledger import Ledger

class LedgerRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, ledger: Ledger) -> int:
        cursor = self.conn.execute(
            "INSERT INTO ledgers (user_account_id, name) VALUES (?, ?)",
            (ledger.user_account_id, ledger.name)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_by_id(self, ledger_id: int) -> Optional[Ledger]:
        cursor = self.conn.execute(
            "SELECT * FROM ledgers WHERE id = ?", (ledger_id,)
        )
        row = cursor.fetchone()
        if row:
            return self._map_row(row)
        return None

    def list_by_user(self, user_id: int) -> List[Ledger]:
        cursor = self.conn.execute(
            "SELECT * FROM ledgers WHERE user_account_id = ?", (user_id,)
        )
        return [self._map_row(row) for row in cursor.fetchall()]

    def delete(self, ledger_id: int):
        self.conn.execute("DELETE FROM ledgers WHERE id = ?", (ledger_id,))
        self.conn.commit()

    def _map_row(self, row) -> Ledger:
        return Ledger(
            id=row['id'],
            user_account_id=row['user_account_id'],
            name=row['name']
        )
