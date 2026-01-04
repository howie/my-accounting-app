from typing import List, Optional
import sqlite3
from src.myab.models.transaction import Transaction
from src.myab.persistence.database import get_db_connection

class TransactionRepository:
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
        # Commit only if it's not an in-memory test connection that will be closed by pytest
        if not self._conn: # Only commit if connection is managed by the repo itself
             conn.commit()
             conn.close()
        elif conn.in_transaction: # If it's a fixture managed connection, commit there
             conn.commit()
        return cursor

    def _fetch_one(self, query: str, params: tuple = ()) -> Optional[Transaction]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        if not self._conn:
            conn.close()
        return Transaction(**row) if row else None

    def _fetch_all(self, query: str, params: tuple = ()) -> List[Transaction]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if not self._conn:
            conn.close()
        return [Transaction(**row) for row in rows]

    def add(self, transaction: Transaction) -> Transaction:
        query = """
            INSERT INTO transactions (ledger_id, date, type, amount, debit_account_id, credit_account_id,
                                     description, invoice_number, creation_timestamp, modification_timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor = self._execute_query(query, (
            transaction.ledger_id,
            transaction.date,
            transaction.type,
            transaction.amount,
            transaction.debit_account_id,
            transaction.credit_account_id,
            transaction.description,
            transaction.invoice_number,
            transaction.creation_timestamp,
            transaction.modification_timestamp
        ))
        transaction.id = cursor.lastrowid
        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        query = "SELECT * FROM transactions WHERE id = ?"
        return self._fetch_one(query, (transaction_id,))

    def get_by_ledger_id(self, ledger_id: int) -> List[Transaction]:
        query = "SELECT * FROM transactions WHERE ledger_id = ?"
        return self._fetch_all(query, (ledger_id,))

    def update(self, transaction: Transaction) -> bool:
        query = """
            UPDATE transactions
            SET ledger_id = ?, date = ?, type = ?, amount = ?, debit_account_id = ?, credit_account_id = ?,
                description = ?, invoice_number = ?, modification_timestamp = ?
            WHERE id = ?
        """
        transaction.modification_timestamp = sqlite3.Timestamp.now().isoformat()
        cursor = self._execute_query(query, (
            transaction.ledger_id,
            transaction.date,
            transaction.type,
            transaction.amount,
            transaction.debit_account_id,
            transaction.credit_account_id,
            transaction.description,
            transaction.invoice_number,
            transaction.modification_timestamp,
            transaction.id
        ))
        return cursor.rowcount > 0

    def delete(self, transaction_id: int) -> bool:
        query = "DELETE FROM transactions WHERE id = ?"
        cursor = self._execute_query(query, (transaction_id,))
        return cursor.rowcount > 0

    def get_transactions_for_account(self, account_id: int) -> List[Transaction]:
        """Retrieves all transactions involving a specific account."""
        query = """
            SELECT * FROM transactions
            WHERE debit_account_id = ? OR credit_account_id = ?
            ORDER BY date DESC, creation_timestamp DESC
        """
        return self._fetch_all(query, (account_id, account_id))

    def search_transactions(self, ledger_id: int, description_keyword: Optional[str] = None,
                            account_id: Optional[int] = None, start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> List[Transaction]:
        """
        Searches and filters transactions for a given ledger.
        """
        query = "SELECT * FROM transactions WHERE ledger_id = ?"
        params = [ledger_id]

        if description_keyword:
            query += " AND description LIKE ?"
            params.append(f"%{description_keyword}%")
        
        if account_id:
            query += " AND (debit_account_id = ? OR credit_account_id = ?)"
            params.append(account_id)
            params.append(account_id)
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)

        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY date DESC, creation_timestamp DESC"

        return self._fetch_all(query, tuple(params))