"""Contract tests for LedgerService.

Tests the service interface contract as defined in contracts/ledger_service.md.
These tests verify the service behaves according to the documented contract.
"""

import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.schemas.ledger import LedgerCreate, LedgerUpdate
from src.services.ledger_service import LedgerService


class TestLedgerServiceContract:
    """Contract tests for LedgerService per contracts/ledger_service.md."""

    @pytest.fixture
    def service(self, session: Session) -> LedgerService:
        """Create a LedgerService instance."""
        return LedgerService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        """Create a test user ID."""
        return uuid.uuid4()

    # --- create_ledger ---

    def test_create_ledger_returns_ledger_with_id(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """Creating a ledger returns a Ledger with a valid UUID id."""
        data = LedgerCreate(name="Test Ledger", initial_balance=Decimal("1000.00"))

        result = service.create_ledger(user_id, data)

        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)

    def test_create_ledger_stores_user_id(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """Created ledger is associated with the provided user_id."""
        data = LedgerCreate(name="Test Ledger")

        result = service.create_ledger(user_id, data)

        assert result.user_id == user_id

    def test_create_ledger_stores_name(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """Created ledger has the provided name."""
        data = LedgerCreate(name="My Personal Budget")

        result = service.create_ledger(user_id, data)

        assert result.name == "My Personal Budget"

    def test_create_ledger_stores_initial_balance(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """Created ledger has the provided initial balance."""
        data = LedgerCreate(name="Test", initial_balance=Decimal("5000.50"))

        result = service.create_ledger(user_id, data)

        assert result.initial_balance == Decimal("5000.50")

    def test_create_ledger_default_initial_balance_is_zero(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """When initial_balance is not provided, it defaults to 0."""
        data = LedgerCreate(name="Test")

        result = service.create_ledger(user_id, data)

        assert result.initial_balance == Decimal("0")

    def test_create_ledger_has_created_at_timestamp(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """Created ledger has a created_at timestamp."""
        data = LedgerCreate(name="Test")

        result = service.create_ledger(user_id, data)

        assert result.created_at is not None

    def test_create_ledger_creates_system_cash_account(
        self, service: LedgerService, user_id: uuid.UUID, session: Session
    ) -> None:
        """Creating a ledger automatically creates a Cash system account."""
        from src.models.account import Account

        data = LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))

        result = service.create_ledger(user_id, data)

        # Find the Cash account
        accounts = session.query(Account).filter(Account.ledger_id == result.id).all()
        cash_account = next((a for a in accounts if a.name == "Cash"), None)

        assert cash_account is not None
        assert cash_account.is_system is True
        assert cash_account.type.value == "ASSET"

    def test_create_ledger_creates_system_equity_account(
        self, service: LedgerService, user_id: uuid.UUID, session: Session
    ) -> None:
        """Creating a ledger automatically creates an Equity system account."""
        from src.models.account import Account

        data = LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))

        result = service.create_ledger(user_id, data)

        # Find the Equity account
        accounts = session.query(Account).filter(Account.ledger_id == result.id).all()
        equity_account = next((a for a in accounts if a.name == "Equity"), None)

        assert equity_account is not None
        assert equity_account.is_system is True
        assert equity_account.type.value == "ASSET"

    def test_create_ledger_creates_initial_transaction(
        self, service: LedgerService, user_id: uuid.UUID, session: Session
    ) -> None:
        """Creating a ledger with initial_balance creates Equity->Cash transaction."""
        from src.models.transaction import Transaction

        data = LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))

        result = service.create_ledger(user_id, data)

        transactions = (
            session.query(Transaction).filter(Transaction.ledger_id == result.id).all()
        )

        assert len(transactions) == 1
        assert transactions[0].amount == Decimal("1000.00")

    def test_create_ledger_no_transaction_when_zero_balance(
        self, service: LedgerService, user_id: uuid.UUID, session: Session
    ) -> None:
        """Creating a ledger with 0 initial_balance does not create a transaction."""
        from src.models.transaction import Transaction

        data = LedgerCreate(name="Test", initial_balance=Decimal("0"))

        result = service.create_ledger(user_id, data)

        transactions = (
            session.query(Transaction).filter(Transaction.ledger_id == result.id).all()
        )

        assert len(transactions) == 0

    # --- get_ledgers ---

    def test_get_ledgers_returns_list(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """get_ledgers returns a list."""
        result = service.get_ledgers(user_id)

        assert isinstance(result, list)

    def test_get_ledgers_returns_empty_for_new_user(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """get_ledgers returns empty list for user with no ledgers."""
        result = service.get_ledgers(user_id)

        assert result == []

    def test_get_ledgers_returns_user_ledgers(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """get_ledgers returns all ledgers for the specified user."""
        service.create_ledger(user_id, LedgerCreate(name="Ledger 1"))
        service.create_ledger(user_id, LedgerCreate(name="Ledger 2"))

        result = service.get_ledgers(user_id)

        assert len(result) == 2
        names = [l.name for l in result]
        assert "Ledger 1" in names
        assert "Ledger 2" in names

    def test_get_ledgers_does_not_return_other_user_ledgers(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """get_ledgers only returns ledgers for the specified user."""
        other_user_id = uuid.uuid4()
        service.create_ledger(user_id, LedgerCreate(name="My Ledger"))
        service.create_ledger(other_user_id, LedgerCreate(name="Other Ledger"))

        result = service.get_ledgers(user_id)

        assert len(result) == 1
        assert result[0].name == "My Ledger"

    # --- get_ledger ---

    def test_get_ledger_returns_ledger_by_id(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """get_ledger returns the ledger with the specified ID."""
        created = service.create_ledger(user_id, LedgerCreate(name="Test"))

        result = service.get_ledger(created.id, user_id)

        assert result is not None
        assert result.id == created.id
        assert result.name == "Test"

    def test_get_ledger_returns_none_for_nonexistent(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """get_ledger returns None for non-existent ledger ID."""
        result = service.get_ledger(uuid.uuid4(), user_id)

        assert result is None

    def test_get_ledger_returns_none_for_other_user(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """get_ledger returns None if ledger belongs to different user."""
        other_user_id = uuid.uuid4()
        created = service.create_ledger(other_user_id, LedgerCreate(name="Other"))

        result = service.get_ledger(created.id, user_id)

        assert result is None

    # --- update_ledger ---

    def test_update_ledger_changes_name(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """update_ledger changes the ledger name."""
        created = service.create_ledger(user_id, LedgerCreate(name="Old Name"))

        result = service.update_ledger(
            created.id, user_id, LedgerUpdate(name="New Name")
        )

        assert result is not None
        assert result.name == "New Name"

    def test_update_ledger_returns_none_for_nonexistent(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """update_ledger returns None for non-existent ledger."""
        result = service.update_ledger(
            uuid.uuid4(), user_id, LedgerUpdate(name="New Name")
        )

        assert result is None

    def test_update_ledger_returns_none_for_other_user(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """update_ledger returns None if ledger belongs to different user."""
        other_user_id = uuid.uuid4()
        created = service.create_ledger(other_user_id, LedgerCreate(name="Other"))

        result = service.update_ledger(
            created.id, user_id, LedgerUpdate(name="New Name")
        )

        assert result is None

    def test_update_ledger_preserves_initial_balance(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """update_ledger does not change initial_balance."""
        created = service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )

        result = service.update_ledger(
            created.id, user_id, LedgerUpdate(name="Updated")
        )

        assert result is not None
        assert result.initial_balance == Decimal("1000.00")

    # --- delete_ledger ---

    def test_delete_ledger_returns_true_on_success(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """delete_ledger returns True when ledger is deleted."""
        created = service.create_ledger(user_id, LedgerCreate(name="Test"))

        result = service.delete_ledger(created.id, user_id)

        assert result is True

    def test_delete_ledger_removes_ledger(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """delete_ledger removes the ledger from the database."""
        created = service.create_ledger(user_id, LedgerCreate(name="Test"))

        service.delete_ledger(created.id, user_id)

        assert service.get_ledger(created.id, user_id) is None

    def test_delete_ledger_returns_false_for_nonexistent(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """delete_ledger returns False for non-existent ledger."""
        result = service.delete_ledger(uuid.uuid4(), user_id)

        assert result is False

    def test_delete_ledger_returns_false_for_other_user(
        self, service: LedgerService, user_id: uuid.UUID
    ) -> None:
        """delete_ledger returns False if ledger belongs to different user."""
        other_user_id = uuid.uuid4()
        created = service.create_ledger(other_user_id, LedgerCreate(name="Other"))

        result = service.delete_ledger(created.id, user_id)

        assert result is False

    def test_delete_ledger_cascades_to_accounts(
        self, service: LedgerService, user_id: uuid.UUID, session: Session
    ) -> None:
        """delete_ledger also deletes associated accounts."""
        from src.models.account import Account

        created = service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        ledger_id = created.id

        service.delete_ledger(ledger_id, user_id)

        accounts = session.query(Account).filter(Account.ledger_id == ledger_id).all()
        assert len(accounts) == 0

    def test_delete_ledger_cascades_to_transactions(
        self, service: LedgerService, user_id: uuid.UUID, session: Session
    ) -> None:
        """delete_ledger also deletes associated transactions."""
        from src.models.transaction import Transaction

        created = service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        ledger_id = created.id

        service.delete_ledger(ledger_id, user_id)

        transactions = (
            session.query(Transaction).filter(Transaction.ledger_id == ledger_id).all()
        )
        assert len(transactions) == 0
