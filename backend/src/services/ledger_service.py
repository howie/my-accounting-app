"""Ledger service for business logic.

Based on contracts/ledger_service.md
"""

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlmodel import Session, select

from src.models.account import Account, AccountType
from src.models.audit_log import AuditLog
from src.models.import_session import ImportSession
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.transaction_template import TransactionTemplate
from src.schemas.ledger import LedgerCreate, LedgerUpdate


class LedgerService:
    """Service for managing ledgers.

    Handles ledger CRUD operations and automatic creation of
    system accounts (Cash, Equity) with initial transactions.
    """

    def __init__(self, session: Session) -> None:
        """Initialize service with database session."""
        self.session = session

    def create_ledger(self, user_id: uuid.UUID, data: LedgerCreate) -> Ledger:
        """Create a new ledger with initial system accounts.

        Side effects:
        - Creates Cash account with initial_balance
        - Creates Equity account with 0 balance
        - Creates initial transaction from Equity to Cash (if initial_balance > 0)
        """
        # Create the ledger
        ledger = Ledger(
            user_id=user_id,
            name=data.name,
            initial_balance=data.initial_balance,
        )
        self.session.add(ledger)
        self.session.flush()  # Get the ledger ID

        # Create system accounts
        cash_account = Account(
            ledger_id=ledger.id,
            name="Cash",
            type=AccountType.ASSET,
            is_system=True,
        )
        equity_account = Account(
            ledger_id=ledger.id,
            name="Equity",
            type=AccountType.ASSET,
            is_system=True,
        )
        self.session.add(cash_account)
        self.session.add(equity_account)
        self.session.flush()

        # Create initial transaction if initial_balance > 0
        if data.initial_balance > Decimal("0"):
            initial_transaction = Transaction(
                ledger_id=ledger.id,
                date=date.today(),
                description="Initial balance",
                amount=data.initial_balance,
                from_account_id=equity_account.id,
                to_account_id=cash_account.id,
                transaction_type=TransactionType.TRANSFER,
            )
            self.session.add(initial_transaction)

        self.session.commit()
        self.session.refresh(ledger)
        return ledger

    def get_ledgers(self, user_id: uuid.UUID) -> list[Ledger]:
        """List all ledgers for a user."""
        statement = select(Ledger).where(Ledger.user_id == user_id)
        result = self.session.exec(statement)
        return list(result.all())

    def get_ledger(self, ledger_id: uuid.UUID, user_id: uuid.UUID) -> Ledger | None:
        """Get a single ledger, ensuring ownership."""
        statement = select(Ledger).where(Ledger.id == ledger_id, Ledger.user_id == user_id)
        result = self.session.exec(statement)
        return result.first()

    def update_ledger(
        self, ledger_id: uuid.UUID, user_id: uuid.UUID, data: LedgerUpdate
    ) -> Ledger | None:
        """Update ledger name."""
        ledger = self.get_ledger(ledger_id, user_id)
        if not ledger:
            return None

        if data.name is not None:
            ledger.name = data.name

        self.session.add(ledger)
        self.session.commit()
        self.session.refresh(ledger)
        return ledger

    def delete_ledger(self, ledger_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete ledger and all associated data.

        Returns True if deleted, False if not found.
        Explicitly deletes in correct order to avoid foreign key violations:
        1. Transactions (reference accounts)
        2. Templates (reference accounts)
        3. Accounts (reference ledger)
        4. Ledger
        """
        ledger = self.get_ledger(ledger_id, user_id)
        if not ledger:
            return False

        # Delete transactions first (they reference accounts)
        tx_statement = select(Transaction).where(Transaction.ledger_id == ledger_id)
        transactions = self.session.exec(tx_statement).all()
        for tx in transactions:
            self.session.delete(tx)

        # Delete templates (they reference accounts)
        tpl_statement = select(TransactionTemplate).where(
            TransactionTemplate.ledger_id == ledger_id
        )
        templates = self.session.exec(tpl_statement).all()
        for tpl in templates:
            self.session.delete(tpl)

        # Delete accounts (they reference ledger)
        acc_statement = select(Account).where(Account.ledger_id == ledger_id)
        accounts = self.session.exec(acc_statement).all()
        for acc in accounts:
            self.session.delete(acc)

        # Delete audit logs
        audit_statement = select(AuditLog).where(AuditLog.ledger_id == ledger_id)
        audit_logs = self.session.exec(audit_statement).all()
        for log in audit_logs:
            self.session.delete(log)

        # Delete import sessions
        import_statement = select(ImportSession).where(ImportSession.ledger_id == ledger_id)
        import_sessions = self.session.exec(import_statement).all()
        for isess in import_sessions:
            self.session.delete(isess)

        # Finally delete the ledger
        self.session.delete(ledger)
        self.session.commit()
        return True

    def clear_transactions(self, ledger_id: uuid.UUID, user_id: uuid.UUID) -> int:
        """Clear all transactions from a ledger, keeping accounts.

        Returns the number of deleted transactions, or -1 if ledger not found.
        """
        ledger = self.get_ledger(ledger_id, user_id)
        if not ledger:
            return -1

        # Delete all transactions for this ledger
        statement = select(Transaction).where(Transaction.ledger_id == ledger_id)
        transactions = self.session.exec(statement).all()
        count = len(transactions)

        for tx in transactions:
            self.session.delete(tx)

        self.session.commit()
        return count

    def clear_accounts(self, ledger_id: uuid.UUID, user_id: uuid.UUID) -> dict[str, Any]:
        """Clear all accounts and transactions from a ledger.

        Recreates the default system accounts (Cash, Equity).

        Returns dict with counts of deleted transactions and accounts.
        """
        ledger = self.get_ledger(ledger_id, user_id)
        if not ledger:
            return {"error": "not_found"}

        # Count before deleting
        tx_statement = select(Transaction).where(Transaction.ledger_id == ledger_id)
        transactions = self.session.exec(tx_statement).all()
        tx_count = len(transactions)

        acc_statement = select(Account).where(Account.ledger_id == ledger_id)
        accounts = self.session.exec(acc_statement).all()
        acc_count = len(accounts)

        # Delete all transactions first (due to foreign key)
        for tx in transactions:
            self.session.delete(tx)

        # Delete all accounts
        for acc in accounts:
            self.session.delete(acc)

        self.session.flush()

        # Recreate system accounts
        cash_account = Account(
            ledger_id=ledger.id,
            name="Cash",
            type=AccountType.ASSET,
            is_system=True,
        )
        equity_account = Account(
            ledger_id=ledger.id,
            name="Equity",
            type=AccountType.ASSET,
            is_system=True,
        )
        self.session.add(cash_account)
        self.session.add(equity_account)

        self.session.commit()
        return {"transactions_deleted": tx_count, "accounts_deleted": acc_count}
