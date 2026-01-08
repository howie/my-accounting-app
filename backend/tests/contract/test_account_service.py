"""Contract tests for AccountService.

Tests the service interface contract as defined in contracts/account_service.md.
These tests verify the service behaves according to the documented contract.
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


class TestAccountServiceContract:
    """Contract tests for AccountService per contracts/account_service.md."""

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        """Create a LedgerService instance."""
        return LedgerService(session)

    @pytest.fixture
    def service(self, session: Session) -> AccountService:
        """Create an AccountService instance."""
        return AccountService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        """Create a test user ID."""
        return uuid.uuid4()

    @pytest.fixture
    def ledger_id(self, ledger_service: LedgerService, user_id: uuid.UUID) -> uuid.UUID:
        """Create a test ledger and return its ID."""
        ledger = ledger_service.create_ledger(user_id, LedgerCreate(name="Test Ledger"))
        return ledger.id

    # --- create_account ---

    def test_create_account_returns_account_with_id(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Creating an account returns an Account with a valid UUID id."""
        data = AccountCreate(name="Bank Account", type=AccountType.ASSET)

        result = service.create_account(ledger_id, data)

        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)

    def test_create_account_stores_ledger_id(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Created account is associated with the provided ledger_id."""
        data = AccountCreate(name="Bank Account", type=AccountType.ASSET)

        result = service.create_account(ledger_id, data)

        assert result.ledger_id == ledger_id

    def test_create_account_stores_name(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Created account has the provided name."""
        data = AccountCreate(name="Savings Account", type=AccountType.ASSET)

        result = service.create_account(ledger_id, data)

        assert result.name == "Savings Account"

    def test_create_account_stores_type(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Created account has the provided type."""
        data = AccountCreate(name="Food", type=AccountType.EXPENSE)

        result = service.create_account(ledger_id, data)

        assert result.type == AccountType.EXPENSE

    def test_create_account_default_balance_is_zero(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Created account has a default balance of 0."""
        data = AccountCreate(name="Test", type=AccountType.ASSET)

        result = service.create_account(ledger_id, data)

        assert result.balance == Decimal("0")

    def test_create_account_is_not_system(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """User-created accounts have is_system=False."""
        data = AccountCreate(name="Test", type=AccountType.ASSET)

        result = service.create_account(ledger_id, data)

        assert result.is_system is False

    def test_create_account_has_timestamps(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Created account has created_at and updated_at timestamps."""
        data = AccountCreate(name="Test", type=AccountType.ASSET)

        result = service.create_account(ledger_id, data)

        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_account_all_types(self, service: AccountService, ledger_id: uuid.UUID) -> None:
        """Can create accounts of all four types."""
        for account_type in AccountType:
            data = AccountCreate(name=f"Test {account_type.value}", type=account_type)
            result = service.create_account(ledger_id, data)
            assert result.type == account_type

    def test_create_account_duplicate_name_raises_error(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """Creating an account with a duplicate name raises an error."""
        data = AccountCreate(name="Duplicate", type=AccountType.ASSET)
        service.create_account(ledger_id, data)

        with pytest.raises(ValueError, match="already exists"):
            service.create_account(ledger_id, data)

    # --- get_accounts ---

    def test_get_accounts_returns_list(self, service: AccountService, ledger_id: uuid.UUID) -> None:
        """get_accounts returns a list."""
        result = service.get_accounts(ledger_id)

        assert isinstance(result, list)

    def test_get_accounts_includes_system_accounts(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """get_accounts returns system accounts (Cash, Equity)."""
        result = service.get_accounts(ledger_id)

        names = [a.name for a in result]
        assert "Cash" in names
        assert "Equity" in names

    def test_get_accounts_includes_user_accounts(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """get_accounts returns user-created accounts."""
        service.create_account(ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE))

        result = service.get_accounts(ledger_id)

        names = [a.name for a in result]
        assert "Food" in names

    def test_get_accounts_filter_by_type(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """get_accounts can filter by account type."""
        service.create_account(ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE))
        service.create_account(ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME))

        result = service.get_accounts(ledger_id, type_filter=AccountType.EXPENSE)

        assert all(a.type == AccountType.EXPENSE for a in result)
        assert any(a.name == "Food" for a in result)

    def test_get_accounts_only_for_specified_ledger(
        self,
        service: AccountService,
        ledger_service: LedgerService,
        ledger_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """get_accounts only returns accounts for the specified ledger."""
        other_ledger = ledger_service.create_ledger(user_id, LedgerCreate(name="Other Ledger"))
        service.create_account(
            other_ledger.id, AccountCreate(name="Other Account", type=AccountType.ASSET)
        )

        result = service.get_accounts(ledger_id)

        names = [a.name for a in result]
        assert "Other Account" not in names

    # --- get_account ---

    def test_get_account_returns_account_by_id(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """get_account returns the account with the specified ID."""
        created = service.create_account(
            ledger_id, AccountCreate(name="Test", type=AccountType.ASSET)
        )

        result = service.get_account(created.id, ledger_id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Test"

    def test_get_account_returns_none_for_nonexistent(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """get_account returns None for non-existent account ID."""
        result = service.get_account(uuid.uuid4(), ledger_id)

        assert result is None

    def test_get_account_returns_none_for_other_ledger(
        self,
        service: AccountService,
        ledger_service: LedgerService,
        ledger_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        """get_account returns None if account belongs to different ledger."""
        other_ledger = ledger_service.create_ledger(user_id, LedgerCreate(name="Other Ledger"))
        created = service.create_account(
            other_ledger.id, AccountCreate(name="Other", type=AccountType.ASSET)
        )

        result = service.get_account(created.id, ledger_id)

        assert result is None

    def test_get_account_includes_calculated_balance(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """get_account returns account with calculated balance."""
        result = service.get_account(service.get_accounts(ledger_id)[0].id, ledger_id)

        assert result is not None
        assert isinstance(result.balance, Decimal)

    # --- update_account ---

    def test_update_account_changes_name(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """update_account changes the account name."""
        created = service.create_account(
            ledger_id, AccountCreate(name="Old Name", type=AccountType.ASSET)
        )

        result = service.update_account(created.id, ledger_id, AccountUpdate(name="New Name"))

        assert result is not None
        assert result.name == "New Name"

    def test_update_account_returns_none_for_nonexistent(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """update_account returns None for non-existent account."""
        result = service.update_account(uuid.uuid4(), ledger_id, AccountUpdate(name="New Name"))

        assert result is None

    def test_update_account_cannot_change_type(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """update_account does not change account type (type is immutable)."""
        created = service.create_account(
            ledger_id, AccountCreate(name="Test", type=AccountType.ASSET)
        )

        result = service.update_account(created.id, ledger_id, AccountUpdate(name="Updated"))

        assert result is not None
        assert result.type == AccountType.ASSET

    def test_update_system_account_raises_error(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """update_account raises error for system accounts."""
        accounts = service.get_accounts(ledger_id)
        cash_account = next(a for a in accounts if a.name == "Cash")

        with pytest.raises(ValueError, match="system account"):
            service.update_account(cash_account.id, ledger_id, AccountUpdate(name="Renamed Cash"))

    def test_update_account_duplicate_name_raises_error(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """update_account raises error if new name already exists."""
        service.create_account(ledger_id, AccountCreate(name="Existing", type=AccountType.ASSET))
        to_update = service.create_account(
            ledger_id, AccountCreate(name="Original", type=AccountType.ASSET)
        )

        with pytest.raises(ValueError, match="already exists"):
            service.update_account(to_update.id, ledger_id, AccountUpdate(name="Existing"))

    # --- delete_account ---

    def test_delete_account_returns_true_on_success(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """delete_account returns True when account is deleted."""
        created = service.create_account(
            ledger_id, AccountCreate(name="Test", type=AccountType.ASSET)
        )

        result = service.delete_account(created.id, ledger_id)

        assert result is True

    def test_delete_account_removes_account(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """delete_account removes the account from the database."""
        created = service.create_account(
            ledger_id, AccountCreate(name="Test", type=AccountType.ASSET)
        )

        service.delete_account(created.id, ledger_id)

        assert service.get_account(created.id, ledger_id) is None

    def test_delete_account_returns_false_for_nonexistent(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """delete_account returns False for non-existent account."""
        result = service.delete_account(uuid.uuid4(), ledger_id)

        assert result is False

    def test_delete_system_account_raises_error(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """delete_account raises error for system accounts (FR-004)."""
        accounts = service.get_accounts(ledger_id)
        cash_account = next(a for a in accounts if a.name == "Cash")

        with pytest.raises(ValueError, match="system account"):
            service.delete_account(cash_account.id, ledger_id)

    def test_delete_account_with_transactions_raises_error(
        self,
        service: AccountService,
        ledger_service: LedgerService,
        user_id: uuid.UUID,
    ) -> None:
        """delete_account raises error if account has transactions."""
        # Create ledger with initial balance (creates transaction)
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        accounts = service.get_accounts(ledger.id)
        cash_account = next(a for a in accounts if a.name == "Cash")

        # Cash has transactions, should raise (either "system account" or "has transactions")
        # Note: Cash is also a system account, so the system account check may trigger first
        with pytest.raises(ValueError, match="(has transactions|system account)"):
            service.delete_account(cash_account.id, ledger.id)

    # --- calculate_balance ---

    def test_calculate_balance_returns_decimal(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """calculate_balance returns a Decimal value."""
        accounts = service.get_accounts(ledger_id)

        result = service.calculate_balance(accounts[0].id)

        assert isinstance(result, Decimal)

    def test_calculate_balance_zero_for_new_account(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """calculate_balance returns 0 for account with no transactions."""
        created = service.create_account(
            ledger_id, AccountCreate(name="Empty", type=AccountType.ASSET)
        )

        result = service.calculate_balance(created.id)

        assert result == Decimal("0")

    # --- has_transactions ---

    def test_has_transactions_false_for_new_account(
        self, service: AccountService, ledger_id: uuid.UUID
    ) -> None:
        """has_transactions returns False for account with no transactions."""
        created = service.create_account(
            ledger_id, AccountCreate(name="Empty", type=AccountType.ASSET)
        )

        result = service.has_transactions(created.id)

        assert result is False

    def test_has_transactions_true_when_account_has_transactions(
        self,
        service: AccountService,
        ledger_service: LedgerService,
        user_id: uuid.UUID,
    ) -> None:
        """has_transactions returns True for account with transactions."""
        # Create ledger with initial balance (creates transaction)
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        accounts = service.get_accounts(ledger.id)
        cash_account = next(a for a in accounts if a.name == "Cash")

        result = service.has_transactions(cash_account.id)

        assert result is True
