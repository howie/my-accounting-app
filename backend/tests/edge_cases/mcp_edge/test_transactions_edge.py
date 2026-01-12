"""Edge case tests for list_transactions MCP tool.

Tests error handling, boundary conditions, and special scenarios.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.transactions import list_transactions
from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.user import User


@pytest.fixture
def user_with_ledger(session: Session) -> tuple[User, Ledger]:
    """Create a user with a default ledger."""
    user = User(email="test@example.com", display_name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)

    ledger = Ledger(user_id=user.id, name="個人帳本", description="測試帳本")
    session.add(ledger)
    session.commit()
    session.refresh(ledger)

    return user, ledger


@pytest.fixture
def accounts(session: Session, user_with_ledger: tuple[User, Ledger]) -> dict[str, Account]:
    """Create test accounts."""
    _, ledger = user_with_ledger

    cash = Account(
        ledger_id=ledger.id,
        name="現金",
        type=AccountType.ASSET,
        balance=Decimal("10000"),
    )
    food = Account(
        ledger_id=ledger.id,
        name="餐飲",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )

    session.add_all([cash, food])
    session.commit()
    for acc in [cash, food]:
        session.refresh(acc)

    return {"cash": cash, "food": food}


@pytest.fixture
def transactions(
    session: Session,
    user_with_ledger: tuple[User, Ledger],
    accounts: dict[str, Account],
) -> list[Transaction]:
    """Create test transactions."""
    _, ledger = user_with_ledger

    tx1 = Transaction(
        ledger_id=ledger.id,
        date=date(2026, 1, 11),
        description="午餐",
        amount=Decimal("85"),
        from_account_id=accounts["cash"].id,
        to_account_id=accounts["food"].id,
        transaction_type=TransactionType.EXPENSE,
        notes="測試備註",
    )
    tx2 = Transaction(
        ledger_id=ledger.id,
        date=date(2026, 1, 10),
        description="晚餐",
        amount=Decimal("120"),
        from_account_id=accounts["cash"].id,
        to_account_id=accounts["food"].id,
        transaction_type=TransactionType.EXPENSE,
    )

    session.add_all([tx1, tx2])
    session.commit()
    for tx in [tx1, tx2]:
        session.refresh(tx)

    return [tx1, tx2]


class TestListTransactionsEdgeCases:
    """Edge case tests for list_transactions."""

    def test_user_with_no_ledgers(self, session: Session):
        """Should return error when user has no ledgers."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        result = list_transactions(
            ledger_id=None,
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_NOT_FOUND"

    def test_invalid_ledger_id_format(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Should return validation error for invalid UUID."""
        user, _ = user_with_ledger

        result = list_transactions(
            ledger_id="not-a-uuid",
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"

    def test_invalid_date_format(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return error for invalid date format."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date="2026/01/01",  # Wrong format
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "INVALID_DATE"

    def test_end_date_before_start_date(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Should return empty results when end_date is before start_date."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date="2026-01-11",
            end_date="2026-01-01",  # Before start
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        # This should still succeed but return no results
        assert result["success"] is True
        assert len(result["data"]["transactions"]) == 0

    def test_account_not_found_by_id(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return error when account UUID doesn't exist."""
        user, ledger = user_with_ledger
        import uuid

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=str(uuid.uuid4()),  # Random UUID
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"

    def test_account_not_found_by_name(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return error when account name doesn't exist."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name="不存在的科目",
            start_date=None,
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "ACCOUNT_NOT_FOUND"

    def test_limit_exceeds_maximum(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Should cap limit at maximum (100)."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=500,  # Exceeds max
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        # Should be capped at 100
        assert result["data"]["pagination"]["limit"] == 100

    def test_negative_offset(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Should treat negative offset as zero."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=-10,  # Negative
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["pagination"]["offset"] == 0

    def test_offset_beyond_total(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Should return empty list when offset exceeds total."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=100,  # Beyond total
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["transactions"]) == 0
        assert result["data"]["pagination"]["has_more"] is False


class TestListTransactionsMultipleLedgers:
    """Test behavior with multiple ledgers."""

    def test_requires_ledger_id_when_multiple(self, session: Session):
        """Should require ledger_id when user has multiple ledgers."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        ledger1 = Ledger(user_id=user.id, name="帳本1")
        ledger2 = Ledger(user_id=user.id, name="帳本2")
        session.add_all([ledger1, ledger2])
        session.commit()

        result = list_transactions(
            ledger_id=None,
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_REQUIRED"
        assert "available_ledgers" in result["error"]

    def test_cannot_access_other_users_ledger(self, session: Session):
        """Should not allow access to other user's ledger."""
        user1 = User(email="user1@example.com", display_name="User 1")
        user2 = User(email="user2@example.com", display_name="User 2")
        session.add_all([user1, user2])
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        ledger1 = Ledger(user_id=user1.id, name="User1 Ledger")
        session.add(ledger1)
        session.commit()
        session.refresh(ledger1)

        result = list_transactions(
            ledger_id=str(ledger1.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user2,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "LEDGER_NOT_FOUND"


class TestListTransactionsNotes:
    """Test transaction notes handling."""

    def test_transaction_with_notes(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Transaction with notes should include them."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        # Find transaction with notes
        tx_with_notes = next(
            tx for tx in result["data"]["transactions"] if tx["description"] == "午餐"
        )
        assert tx_with_notes["notes"] == "測試備註"

    def test_transaction_without_notes(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Transaction without notes should have null."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        # Find transaction without notes
        tx_without_notes = next(
            tx for tx in result["data"]["transactions"] if tx["description"] == "晚餐"
        )
        assert tx_without_notes["notes"] is None
