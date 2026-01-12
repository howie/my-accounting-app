"""Contract tests for list_ledgers MCP tool.

Tests the response format matches contracts/mcp-tools.md specification.
"""

from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.ledgers import list_ledgers
from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.user import User


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="test@example.com", display_name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledgers_with_data(session: Session, user: User) -> list[Ledger]:
    """Create ledgers with accounts and transactions."""
    from datetime import date

    # First ledger (Note: Ledger model doesn't have description field)
    ledger1 = Ledger(user_id=user.id, name="個人帳本")
    session.add(ledger1)
    session.commit()
    session.refresh(ledger1)

    # Add accounts to ledger1
    cash1 = Account(
        ledger_id=ledger1.id,
        name="現金",
        type=AccountType.ASSET,
        balance=Decimal("10000"),
    )
    food1 = Account(
        ledger_id=ledger1.id,
        name="餐飲",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )
    session.add_all([cash1, food1])
    session.commit()
    session.refresh(cash1)
    session.refresh(food1)

    # Add transactions to ledger1
    for i in range(5):
        tx = Transaction(
            ledger_id=ledger1.id,
            date=date(2026, 1, i + 1),
            description=f"交易 {i + 1}",
            amount=Decimal("100"),
            from_account_id=cash1.id,
            to_account_id=food1.id,
            transaction_type=TransactionType.EXPENSE,
        )
        session.add(tx)
    session.commit()

    # Second ledger
    ledger2 = Ledger(user_id=user.id, name="家庭帳本")
    session.add(ledger2)
    session.commit()
    session.refresh(ledger2)

    # Add accounts to ledger2
    cash2 = Account(
        ledger_id=ledger2.id,
        name="共同帳戶",
        type=AccountType.ASSET,
        balance=Decimal("50000"),
    )
    session.add(cash2)
    session.commit()

    return [ledger1, ledger2]


class TestListLedgersContract:
    """Contract tests for list_ledgers response format."""

    def test_success_response_structure(
        self,
        session: Session,
        user: User,
        ledgers_with_data: list[Ledger],
    ):
        """Response should match contract success schema."""
        result = list_ledgers(
            session=session,
            user=user,
        )

        # Top-level structure
        assert "success" in result
        assert result["success"] is True
        assert "data" in result
        assert "message" in result

        # Data structure
        data = result["data"]
        assert "ledgers" in data
        assert "default_ledger_id" in data

    def test_ledger_structure(
        self,
        session: Session,
        user: User,
        ledgers_with_data: list[Ledger],
    ):
        """Ledger objects should match contract format."""
        result = list_ledgers(
            session=session,
            user=user,
        )

        for ledger in result["data"]["ledgers"]:
            assert "id" in ledger
            assert "name" in ledger
            assert "description" in ledger
            assert "account_count" in ledger
            assert "transaction_count" in ledger

    def test_account_and_transaction_counts(
        self,
        session: Session,
        user: User,
        ledgers_with_data: list[Ledger],
    ):
        """Counts should reflect actual data."""
        result = list_ledgers(
            session=session,
            user=user,
        )

        # Find 個人帳本
        personal = next(l for l in result["data"]["ledgers"] if l["name"] == "個人帳本")
        assert personal["account_count"] == 2
        assert personal["transaction_count"] == 5

        # Find 家庭帳本
        family = next(l for l in result["data"]["ledgers"] if l["name"] == "家庭帳本")
        assert family["account_count"] == 1
        assert family["transaction_count"] == 0

    def test_default_ledger_id(
        self,
        session: Session,
        user: User,
        ledgers_with_data: list[Ledger],
    ):
        """default_ledger_id should be set."""
        result = list_ledgers(
            session=session,
            user=user,
        )

        # default_ledger_id should be the first ledger
        assert result["data"]["default_ledger_id"] is not None
        ledger_ids = [l["id"] for l in result["data"]["ledgers"]]
        assert result["data"]["default_ledger_id"] in ledger_ids

    def test_message_format(
        self,
        session: Session,
        user: User,
        ledgers_with_data: list[Ledger],
    ):
        """Message should reflect ledger count."""
        result = list_ledgers(
            session=session,
            user=user,
        )

        assert "2" in result["message"]
        assert "帳本" in result["message"]


class TestListLedgersEdgeCases:
    """Edge case tests for list_ledgers."""

    def test_user_with_no_ledgers(
        self,
        session: Session,
        user: User,
    ):
        """Should return empty list when user has no ledgers."""
        result = list_ledgers(
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["ledgers"]) == 0
        assert result["data"]["default_ledger_id"] is None

    def test_single_ledger(
        self,
        session: Session,
        user: User,
    ):
        """Should handle single ledger case."""
        ledger = Ledger(user_id=user.id, name="唯一帳本")
        session.add(ledger)
        session.commit()
        session.refresh(ledger)

        result = list_ledgers(
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["ledgers"]) == 1
        assert result["data"]["default_ledger_id"] == str(ledger.id)
        assert "1" in result["message"]

    def test_ledger_description_is_null(
        self,
        session: Session,
        user: User,
    ):
        """Description should always be null (Ledger model doesn't have this field)."""
        ledger = Ledger(user_id=user.id, name="測試帳本")
        session.add(ledger)
        session.commit()

        result = list_ledgers(
            session=session,
            user=user,
        )

        assert result["success"] is True
        # Description is always null since Ledger model doesn't have this field
        assert result["data"]["ledgers"][0]["description"] is None
