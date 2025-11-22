import sqlite3
from typing import List, Optional
from decimal import Decimal
from myab.models.account import Account, AccountType

class AccountRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, account: Account) -> int:
        try:
            cursor = self.conn.execute(
                "INSERT INTO accounts (ledger_id, name, type, initial_balance) VALUES (?, ?, ?, ?)",
                (account.ledger_id, account.name, account.type.value, str(account.initial_balance))
            )
            self.conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Account {account.name} already exists in ledger")

    def get_by_id(self, account_id: int) -> Optional[Account]:
        cursor = self.conn.execute(
            "SELECT * FROM accounts WHERE id = ?", (account_id,)
        )
        row = cursor.fetchone()
        if row:
            return self._map_row(row)
        return None
        
    def get_by_name(self, ledger_id: int, name: str) -> Optional[Account]:
        cursor = self.conn.execute(
            "SELECT * FROM accounts WHERE ledger_id = ? AND name = ?", (ledger_id, name)
        )
        row = cursor.fetchone()
        if row:
            return self._map_row(row)
        return None

    def list_by_ledger(self, ledger_id: int) -> List[Account]:
        cursor = self.conn.execute(
            "SELECT * FROM accounts WHERE ledger_id = ?", (ledger_id,)
        )
        return [self._map_row(row) for row in cursor.fetchall()]

    def delete(self, account_id: int):
        try:
            self.conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
            self.conn.commit()
        except sqlite3.IntegrityError:
            # This happens if FK constraint fails (transactions exist)
            raise ValueError("Cannot delete account with associated transactions")

    def _map_row(self, row) -> Account:
        return Account(
            id=row['id'],
            ledger_id=row['ledger_id'],
            name=row['name'],
            type=AccountType(row['type']),
            initial_balance=Decimal(row['initial_balance'])
        )
