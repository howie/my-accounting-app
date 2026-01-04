"""Account service for business logic.

Based on contracts/account_service.md
"""

import uuid
from decimal import Decimal

from sqlmodel import Session, select, func

from src.models.account import Account, AccountType
from src.models.transaction import Transaction
from src.schemas.account import AccountCreate, AccountUpdate


class AccountService:
    """Service for managing accounts within a ledger.

    Handles account CRUD operations with protection for system accounts
    and accounts with transactions.
    """

    def __init__(self, session: Session) -> None:
        """Initialize service with database session."""
        self.session = session

    def create_account(self, ledger_id: uuid.UUID, data: AccountCreate) -> Account:
        """Create a new account in the ledger.

        Raises ValueError if account name already exists in the ledger.
        """
        # Check for duplicate name
        existing = self.session.exec(
            select(Account).where(
                Account.ledger_id == ledger_id, Account.name == data.name
            )
        ).first()

        if existing:
            raise ValueError(f"Account with name '{data.name}' already exists")

        account = Account(
            ledger_id=ledger_id,
            name=data.name,
            type=data.type,
            is_system=False,
        )
        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account

    def get_accounts(
        self, ledger_id: uuid.UUID, type_filter: AccountType | None = None
    ) -> list[Account]:
        """List all accounts for a ledger.

        Optionally filter by account type.
        """
        statement = select(Account).where(Account.ledger_id == ledger_id)

        if type_filter is not None:
            statement = statement.where(Account.type == type_filter)

        result = self.session.exec(statement)
        return list(result.all())

    def get_account(
        self, account_id: uuid.UUID, ledger_id: uuid.UUID
    ) -> Account | None:
        """Get a single account with calculated balance."""
        statement = select(Account).where(
            Account.id == account_id, Account.ledger_id == ledger_id
        )
        result = self.session.exec(statement)
        account = result.first()

        if account:
            # Update balance from transactions
            account.balance = self.calculate_balance(account_id)

        return account

    def update_account(
        self, account_id: uuid.UUID, ledger_id: uuid.UUID, data: AccountUpdate
    ) -> Account | None:
        """Update account name.

        Raises ValueError for system accounts or duplicate names.
        """
        account = self.session.exec(
            select(Account).where(
                Account.id == account_id, Account.ledger_id == ledger_id
            )
        ).first()

        if not account:
            return None

        # Cannot rename system accounts
        if account.is_system:
            raise ValueError("Cannot modify system account")

        if data.name is not None:
            # Check for duplicate name (except self)
            existing = self.session.exec(
                select(Account).where(
                    Account.ledger_id == ledger_id,
                    Account.name == data.name,
                    Account.id != account_id,
                )
            ).first()

            if existing:
                raise ValueError(f"Account with name '{data.name}' already exists")

            account.name = data.name

        self.session.add(account)
        self.session.commit()
        self.session.refresh(account)
        return account

    def delete_account(self, account_id: uuid.UUID, ledger_id: uuid.UUID) -> bool:
        """Delete an account.

        Raises ValueError for system accounts or accounts with transactions.
        Returns True if deleted, False if not found.
        """
        account = self.session.exec(
            select(Account).where(
                Account.id == account_id, Account.ledger_id == ledger_id
            )
        ).first()

        if not account:
            return False

        # Cannot delete system accounts
        if account.is_system:
            raise ValueError("Cannot delete system account")

        # Cannot delete accounts with transactions
        if self.has_transactions(account_id):
            raise ValueError("Cannot delete account that has transactions")

        self.session.delete(account)
        self.session.commit()
        return True

    def calculate_balance(self, account_id: uuid.UUID) -> Decimal:
        """Calculate account balance from all transactions.

        For Asset: SUM(incoming) - SUM(outgoing) (what you have)
        For Liability: SUM(outgoing) - SUM(incoming) (what you owe)
            - When you charge to credit card (from liability), outgoing ↑, balance ↑
            - When you pay off (to liability), incoming ↑, balance ↓
        For Income: SUM(outgoing)  # Money flows OUT to assets
        For Expense: SUM(incoming) # Money flows IN from assets
        """
        account = self.session.get(Account, account_id)
        if not account:
            return Decimal("0")

        # Sum of transactions where this account is the destination (incoming)
        incoming_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
                Transaction.to_account_id == account_id
            )
        ).one()
        incoming = Decimal(str(incoming_result)) if incoming_result else Decimal("0")

        # Sum of transactions where this account is the source (outgoing)
        outgoing_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
                Transaction.from_account_id == account_id
            )
        ).one()
        outgoing = Decimal(str(outgoing_result)) if outgoing_result else Decimal("0")

        if account.type == AccountType.ASSET:
            return incoming - outgoing
        elif account.type == AccountType.LIABILITY:
            return outgoing - incoming  # What you owe (positive when in debt)
        elif account.type == AccountType.INCOME:
            return outgoing  # Income "earns" by sending to assets
        else:  # EXPENSE
            return incoming  # Expense "spends" by receiving from assets

    def has_transactions(self, account_id: uuid.UUID) -> bool:
        """Check if account has any associated transactions."""
        count = self.session.exec(
            select(func.count()).where(
                (Transaction.from_account_id == account_id)
                | (Transaction.to_account_id == account_id)
            )
        ).one()
        return count > 0
