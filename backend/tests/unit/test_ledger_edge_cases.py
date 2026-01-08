"""Edge case tests for ledger and account operations.

Tests edge cases including:
- System account protection (FR-004)
- Duplicate name handling
- Boundary conditions
"""

import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.account import AccountType
from src.schemas.account import AccountCreate, AccountUpdate
from src.schemas.ledger import LedgerCreate
from src.services.account_service import AccountService
from src.services.ledger_service import LedgerService


class TestSystemAccountProtection:
    """Tests for system account protection rules (FR-004)."""

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

    @pytest.fixture
    def ledger_id(
        self, ledger_service: LedgerService, user_id: uuid.UUID
    ) -> uuid.UUID:
        """Create a test ledger and return its ID."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test Ledger")
        )
        return ledger.id

    def test_cannot_delete_cash_account(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Cash system account cannot be deleted."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        with pytest.raises(ValueError, match="system account"):
            account_service.delete_account(cash.id, ledger_id)

    def test_cannot_delete_equity_account(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Equity system account cannot be deleted."""
        accounts = account_service.get_accounts(ledger_id)
        equity = next(a for a in accounts if a.name == "Equity")

        with pytest.raises(ValueError, match="system account"):
            account_service.delete_account(equity.id, ledger_id)

    def test_cannot_rename_cash_account(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Cash system account cannot be renamed."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        with pytest.raises(ValueError, match="system account"):
            account_service.update_account(
                cash.id, ledger_id, AccountUpdate(name="My Cash")
            )

    def test_cannot_rename_equity_account(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Equity system account cannot be renamed."""
        accounts = account_service.get_accounts(ledger_id)
        equity = next(a for a in accounts if a.name == "Equity")

        with pytest.raises(ValueError, match="system account"):
            account_service.update_account(
                equity.id, ledger_id, AccountUpdate(name="My Equity")
            )

    def test_system_accounts_always_exist_after_creation(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """System accounts always exist after ledger creation."""
        accounts = account_service.get_accounts(ledger_id)
        system_accounts = [a for a in accounts if a.is_system]

        assert len(system_accounts) == 2
        names = {a.name for a in system_accounts}
        assert names == {"Cash", "Equity"}

    def test_user_account_can_be_deleted(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """User-created accounts can be deleted."""
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        result = account_service.delete_account(account.id, ledger_id)

        assert result is True
        assert account_service.get_account(account.id, ledger_id) is None

    def test_user_account_can_be_renamed(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """User-created accounts can be renamed."""
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        result = account_service.update_account(
            account.id, ledger_id, AccountUpdate(name="Groceries")
        )

        assert result is not None
        assert result.name == "Groceries"


class TestDuplicateNameHandling:
    """Tests for duplicate name validation."""

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

    @pytest.fixture
    def ledger_id(
        self, ledger_service: LedgerService, user_id: uuid.UUID
    ) -> uuid.UUID:
        """Create a test ledger and return its ID."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test Ledger")
        )
        return ledger.id

    def test_cannot_create_account_with_same_name(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Cannot create two accounts with the same name in a ledger."""
        account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        with pytest.raises(ValueError, match="already exists"):
            account_service.create_account(
                ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
            )

    def test_cannot_create_account_with_system_account_name(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Cannot create an account with the same name as a system account."""
        with pytest.raises(ValueError, match="already exists"):
            account_service.create_account(
                ledger_id, AccountCreate(name="Cash", type=AccountType.ASSET)
            )

    def test_duplicate_name_different_type_still_rejected(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Duplicate name is rejected even with different account type."""
        account_service.create_account(
            ledger_id, AccountCreate(name="Travel", type=AccountType.EXPENSE)
        )

        with pytest.raises(ValueError, match="already exists"):
            account_service.create_account(
                ledger_id, AccountCreate(name="Travel", type=AccountType.ASSET)
            )

    def test_same_name_allowed_in_different_ledgers(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Same account name is allowed in different ledgers."""
        ledger1 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Personal")
        )
        ledger2 = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Business")
        )

        # Both should succeed
        account1 = account_service.create_account(
            ledger1.id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        account2 = account_service.create_account(
            ledger2.id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        assert account1.name == "Food"
        assert account2.name == "Food"
        assert account1.id != account2.id

    def test_cannot_rename_to_existing_name(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Cannot rename an account to a name that already exists."""
        account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        travel = account_service.create_account(
            ledger_id, AccountCreate(name="Travel", type=AccountType.EXPENSE)
        )

        with pytest.raises(ValueError, match="already exists"):
            account_service.update_account(
                travel.id, ledger_id, AccountUpdate(name="Food")
            )

    def test_cannot_rename_to_system_account_name(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Cannot rename an account to a system account name."""
        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        with pytest.raises(ValueError, match="already exists"):
            account_service.update_account(
                food.id, ledger_id, AccountUpdate(name="Cash")
            )

    def test_can_rename_to_same_name(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Renaming to the same name should succeed (no change)."""
        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        # Should not raise
        result = account_service.update_account(
            food.id, ledger_id, AccountUpdate(name="Food")
        )

        assert result is not None
        assert result.name == "Food"


class TestBoundaryConditions:
    """Tests for boundary conditions and edge cases."""

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

    def test_ledger_name_maximum_length(
        self, ledger_service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """Ledger name at maximum length (100 chars) is accepted."""
        long_name = "A" * 100

        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name=long_name)
        )

        assert ledger.name == long_name

    def test_account_name_maximum_length(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Account name at maximum length (100 chars) is accepted."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test")
        )
        long_name = "B" * 100

        account = account_service.create_account(
            ledger.id, AccountCreate(name=long_name, type=AccountType.ASSET)
        )

        assert account.name == long_name

    def test_initial_balance_precision_preserved(
        self, ledger_service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """Initial balance preserves 2 decimal places."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1234.56"))
        )

        assert ledger.initial_balance == Decimal("1234.56")

    def test_large_initial_balance(
        self, ledger_service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """Large initial balance within NUMERIC(15,2) is accepted."""
        # Max value for NUMERIC(15,2) is 9999999999999.99
        large_balance = Decimal("1000000000.00")  # 1 billion

        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=large_balance)
        )

        assert ledger.initial_balance == large_balance

    def test_many_accounts_in_ledger(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Ledger can contain many accounts."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test")
        )

        for i in range(50):
            account_service.create_account(
                ledger.id,
                AccountCreate(name=f"Account {i}", type=AccountType.EXPENSE),
            )

        accounts = account_service.get_accounts(ledger.id)
        # 50 user accounts + 2 system accounts
        assert len(accounts) == 52

    def test_many_ledgers_per_user(
        self, ledger_service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """User can have many ledgers."""
        for i in range(20):
            ledger_service.create_ledger(
                user_id, LedgerCreate(name=f"Ledger {i}")
            )

        ledgers = ledger_service.get_ledgers(user_id)
        assert len(ledgers) == 20


class TestAccountWithTransactionsProtection:
    """Tests for protecting accounts that have transactions."""

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

    def test_cannot_delete_account_with_transactions(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """Cannot delete an account that has associated transactions."""
        # Create ledger with initial balance (creates transaction)
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )

        accounts = account_service.get_accounts(ledger.id)
        cash = next(a for a in accounts if a.name == "Cash")

        # Cash has transactions, should raise
        with pytest.raises(ValueError):
            account_service.delete_account(cash.id, ledger.id)

    def test_has_transactions_returns_true_for_account_with_transactions(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """has_transactions returns True for accounts with transactions."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )

        accounts = account_service.get_accounts(ledger.id)
        cash = next(a for a in accounts if a.name == "Cash")

        assert account_service.has_transactions(cash.id) is True

    def test_has_transactions_returns_false_for_empty_account(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """has_transactions returns False for accounts without transactions."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test")  # No initial balance = no transactions
        )

        food = account_service.create_account(
            ledger.id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        assert account_service.has_transactions(food.id) is False

    def test_can_delete_empty_user_account(
        self,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
    ) -> None:
        """User account without transactions can be deleted."""
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test")
        )

        food = account_service.create_account(
            ledger.id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        result = account_service.delete_account(food.id, ledger.id)
        assert result is True
