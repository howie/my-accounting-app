"""Integration tests for ledger creation lifecycle.

Tests the complete flow of creating a ledger, including automatic
creation of system accounts and initial transactions.
"""

import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.services.ledger_service import LedgerService
from src.services.account_service import AccountService
from src.schemas.ledger import LedgerCreate
from src.schemas.account import AccountCreate
from src.models.account import AccountType


class TestLedgerCreationLifecycle:
    """Integration tests for the complete ledger creation process."""

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        """Create a LedgerService instance."""
        return LedgerService(session)

    @pytest.fixture
    def account_service(self, session: Session) -> AccountService:
        """Create an AccountService instance."""
        return AccountService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        """Create a test user ID."""
        return uuid.uuid4()

    def test_ledger_creation_creates_cash_and_equity_accounts(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Creating a ledger automatically creates Cash and Equity accounts."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )

        accounts = account_service.get_accounts(ledger.id)
        names = [a.name for a in accounts]

        assert "Cash" in names
        assert "Equity" in names
        assert len(accounts) == 2

    def test_system_accounts_have_correct_type(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """System accounts are created with ASSET type."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test")
        )

        accounts = account_service.get_accounts(ledger.id)
        cash = next(a for a in accounts if a.name == "Cash")
        equity = next(a for a in accounts if a.name == "Equity")

        assert cash.type == AccountType.ASSET
        assert equity.type == AccountType.ASSET

    def test_system_accounts_are_marked_as_system(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """System accounts have is_system=True."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test")
        )

        accounts = account_service.get_accounts(ledger.id)
        cash = next(a for a in accounts if a.name == "Cash")
        equity = next(a for a in accounts if a.name == "Equity")

        assert cash.is_system is True
        assert equity.is_system is True

    def test_initial_balance_creates_transaction(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
        session: Session,
    ) -> None:
        """Creating ledger with initial_balance creates Equity->Cash transaction."""
        from src.models.transaction import Transaction

        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("5000.00"))
        )

        transactions = (
            session.query(Transaction)
            .filter(Transaction.ledger_id == ledger.id)
            .all()
        )

        assert len(transactions) == 1
        tx = transactions[0]
        assert tx.amount == Decimal("5000.00")
        assert tx.description == "Initial balance"

    def test_initial_transaction_flows_from_equity_to_cash(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
        session: Session,
    ) -> None:
        """Initial transaction flows from Equity to Cash account."""
        from src.models.transaction import Transaction

        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )

        accounts = account_service.get_accounts(ledger.id)
        cash = next(a for a in accounts if a.name == "Cash")
        equity = next(a for a in accounts if a.name == "Equity")

        transactions = (
            session.query(Transaction)
            .filter(Transaction.ledger_id == ledger.id)
            .all()
        )

        tx = transactions[0]
        assert tx.from_account_id == equity.id
        assert tx.to_account_id == cash.id

    def test_cash_balance_reflects_initial_balance(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Cash account balance equals initial_balance after creation."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("2500.00"))
        )

        cash_balance = account_service.calculate_balance(
            next(
                a.id
                for a in account_service.get_accounts(ledger.id)
                if a.name == "Cash"
            )
        )

        assert cash_balance == Decimal("2500.00")

    def test_equity_balance_is_negative_initial_balance(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Equity account balance equals negative initial_balance (source of funds)."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("3000.00"))
        )

        equity_balance = account_service.calculate_balance(
            next(
                a.id
                for a in account_service.get_accounts(ledger.id)
                if a.name == "Equity"
            )
        )

        assert equity_balance == Decimal("-3000.00")

    def test_zero_initial_balance_creates_no_transaction(
        self,
        ledger_service: LedgerService,
        user_id: uuid.UUID,
        session: Session,
    ) -> None:
        """Creating ledger with 0 initial_balance creates no transactions."""
        from src.models.transaction import Transaction

        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("0"))
        )

        transactions = (
            session.query(Transaction)
            .filter(Transaction.ledger_id == ledger.id)
            .all()
        )

        assert len(transactions) == 0

    def test_zero_initial_balance_accounts_have_zero_balance(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """With 0 initial_balance, both accounts have 0 balance."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("0"))
        )

        accounts = account_service.get_accounts(ledger.id)
        for account in accounts:
            balance = account_service.calculate_balance(account.id)
            assert balance == Decimal("0")

    def test_user_can_add_accounts_after_creation(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """User can add custom accounts after ledger creation."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test")
        )

        food_account = account_service.create_account(
            ledger.id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        salary_account = account_service.create_account(
            ledger.id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )

        accounts = account_service.get_accounts(ledger.id)
        names = [a.name for a in accounts]

        assert "Food" in names
        assert "Salary" in names
        assert len(accounts) == 4  # Cash, Equity, Food, Salary

    def test_user_accounts_are_not_system(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """User-created accounts have is_system=False."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test")
        )

        food_account = account_service.create_account(
            ledger.id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        assert food_account.is_system is False

    def test_deleting_ledger_removes_all_accounts(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
        session: Session,
    ) -> None:
        """Deleting a ledger cascades to all associated accounts."""
        from src.models.account import Account

        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        ledger_id = ledger.id

        # Add a user account
        account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        # Delete ledger
        ledger_service.delete_ledger(ledger_id, user_id)

        # Verify all accounts are deleted
        remaining = session.query(Account).filter(Account.ledger_id == ledger_id).all()
        assert len(remaining) == 0

    def test_deleting_ledger_removes_all_transactions(
        self,
        ledger_service: LedgerService,
        user_id: uuid.UUID,
        session: Session,
    ) -> None:
        """Deleting a ledger cascades to all associated transactions."""
        from src.models.transaction import Transaction

        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        ledger_id = ledger.id

        # Delete ledger
        ledger_service.delete_ledger(ledger_id, user_id)

        # Verify all transactions are deleted
        remaining = (
            session.query(Transaction)
            .filter(Transaction.ledger_id == ledger_id)
            .all()
        )
        assert len(remaining) == 0


class TestMultipleLedgerIsolation:
    """Integration tests for ledger data isolation."""

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        """Create a LedgerService instance."""
        return LedgerService(session)

    @pytest.fixture
    def account_service(self, session: Session) -> AccountService:
        """Create an AccountService instance."""
        return AccountService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        """Create a test user ID."""
        return uuid.uuid4()

    def test_each_ledger_has_own_system_accounts(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Each ledger gets its own Cash and Equity accounts."""
        ledger1 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Personal")
        )
        ledger2 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Business")
        )

        accounts1 = account_service.get_accounts(ledger1.id)
        accounts2 = account_service.get_accounts(ledger2.id)

        # Each ledger has 2 accounts
        assert len(accounts1) == 2
        assert len(accounts2) == 2

        # Account IDs are different
        ids1 = {a.id for a in accounts1}
        ids2 = {a.id for a in accounts2}
        assert ids1.isdisjoint(ids2)

    def test_ledgers_have_independent_balances(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Initial balances are independent between ledgers."""
        ledger1 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Personal", initial_balance=Decimal("1000.00"))
        )
        ledger2 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Business", initial_balance=Decimal("5000.00"))
        )

        cash1 = next(
            a for a in account_service.get_accounts(ledger1.id) if a.name == "Cash"
        )
        cash2 = next(
            a for a in account_service.get_accounts(ledger2.id) if a.name == "Cash"
        )

        balance1 = account_service.calculate_balance(cash1.id)
        balance2 = account_service.calculate_balance(cash2.id)

        assert balance1 == Decimal("1000.00")
        assert balance2 == Decimal("5000.00")

    def test_user_accounts_are_ledger_specific(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """User-created accounts only appear in their ledger."""
        ledger1 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Personal")
        )
        ledger2 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Business")
        )

        # Add account to ledger1 only
        account_service.create_account(
            ledger1.id, AccountCreate(name="Personal Expense", type=AccountType.EXPENSE)
        )

        accounts1 = account_service.get_accounts(ledger1.id)
        accounts2 = account_service.get_accounts(ledger2.id)

        names1 = [a.name for a in accounts1]
        names2 = [a.name for a in accounts2]

        assert "Personal Expense" in names1
        assert "Personal Expense" not in names2

    def test_deleting_one_ledger_preserves_others(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Deleting one ledger does not affect other ledgers."""
        ledger1 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="ToDelete", initial_balance=Decimal("1000.00"))
        )
        ledger2 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="ToKeep", initial_balance=Decimal("2000.00"))
        )

        # Delete first ledger
        ledger_service.delete_ledger(ledger1.id, user_id)

        # Second ledger still exists with its data
        remaining_ledger = ledger_service.get_ledger(ledger2.id, user_id)
        assert remaining_ledger is not None
        assert remaining_ledger.name == "ToKeep"

        remaining_accounts = account_service.get_accounts(ledger2.id)
        assert len(remaining_accounts) == 2
