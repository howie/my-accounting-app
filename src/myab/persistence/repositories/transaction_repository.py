import sqlite3
from decimal import Decimal
from datetime import date, datetime
from typing import List, Optional, Tuple
from myab.models.transaction import Transaction

class TransactionRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, txn: Transaction) -> int:
        cursor = self.conn.execute(
            """INSERT INTO transactions 
               (ledger_id, date, type, debit_account_id, credit_account_id, amount, description) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (txn.ledger_id, txn.date.isoformat(), txn.type, 
             txn.debit_account_id, txn.credit_account_id, str(txn.amount), txn.description)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_balance_impact(self, account_id: int) -> Tuple[Decimal, Decimal]:
        cursor = self.conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE debit_account_id = ?", (account_id,)
        )
        row = cursor.fetchone()
        debits = Decimal(row[0]) if row and row[0] else Decimal("0.00")
        
        cursor = self.conn.execute(
            "SELECT SUM(amount) FROM transactions WHERE credit_account_id = ?", (account_id,)
        )
        row = cursor.fetchone()
        credits = Decimal(row[0]) if row and row[0] else Decimal("0.00")
        
        return debits, credits

    def search(self, ledger_id: int, query: str = None, account_id: int = None) -> List[Transaction]:
        sql = "SELECT * FROM transactions WHERE ledger_id = ?"
        params = [ledger_id]
        
        if query:
            sql += " AND description LIKE ?"
            params.append(f"%{query}%")
            
        if account_id:
            sql += " AND (debit_account_id = ? OR credit_account_id = ?)"
            params.extend([account_id, account_id])
            
        cursor = self.conn.execute(sql, params)
        return [self._map_row(row) for row in cursor.fetchall()]

    def _map_row(self, row) -> Transaction:
        # date is stored as string YYYY-MM-DD
        return Transaction(
            id=row['id'],
            ledger_id=row['ledger_id'],
            date=date.fromisoformat(row['date']),
            type=row['type'],
            debit_account_id=row['debit_account_id'],
            credit_account_id=row['credit_account_id'],
            amount=Decimal(row['amount']),
            description=row['description']
        )
