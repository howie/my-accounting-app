"""Ledger service for business logic.

Based on contracts/ledger_service.md
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
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
        statement = select(Ledger).where(
            Ledger.id == ledger_id, Ledger.user_id == user_id
        )
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
        """
        ledger = self.get_ledger(ledger_id, user_id)
        if not ledger:
            return False

        self.session.delete(ledger)
        self.session.commit()
        return True
