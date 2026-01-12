"""Contract tests for create_transaction MCP tool.

Tests the MCP tool contract as defined in contracts/mcp-tools.md.
"""

import uuid
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.transactions import create_transaction
from src.models.account import Account, AccountType
from src.models.ledger import Ledger
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
    """Create test accounts for transactions."""
    _, ledger = user_with_ledger

    cash = Account(
        ledger_id=ledger.id,
        name="現金",
        type=AccountType.ASSET,
        balance=Decimal("10000"),
        is_system=True,
    )
    food = Account(
        ledger_id=ledger.id,
        name="餐飲",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )
    income = Account(
        ledger_id=ledger.id,
        name="薪資",
        type=AccountType.INCOME,
        balance=Decimal("0"),
    )

    session.add_all([cash, food, income])
    session.commit()
    session.refresh(cash)
    session.refresh(food)
    session.refresh(income)

    return {"cash": cash, "food": food, "income": income}


class TestCreateTransactionContract:
    """Test create_transaction tool contract."""

    def test_create_expense_transaction_success(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Create expense transaction with valid parameters."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=85.0,
            from_account="現金",
            to_account="餐飲",
            description="午餐 - 便當",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        # Verify response structure per contract
        assert result["success"] is True
        assert "data" in result
        assert "transaction" in result["data"]
        assert "message" in result

        tx = result["data"]["transaction"]
        assert tx["amount"] == 85.0
        assert tx["description"] == "午餐 - 便當"
        assert tx["from_account"]["name"] == "現金"
        assert tx["to_account"]["name"] == "餐飲"

    def test_create_transaction_with_account_id(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Create transaction using account IDs instead of names."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=100.0,
            from_account=str(accounts["cash"].id),
            to_account=str(accounts["food"].id),
            description="晚餐",
            date=None,  # Should default to today
            notes="測試備註",
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert result["data"]["transaction"]["notes"] == "測試備註"

    def test_create_transaction_returns_id(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Created transaction should have a UUID id."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=50.0,
            from_account="現金",
            to_account="餐飲",
            description="下午茶",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        assert result["success"] is True
        tx_id = result["data"]["transaction"]["id"]
        # Should be a valid UUID
        uuid.UUID(tx_id)


class TestCreateTransactionResponseFormat:
    """Test create_transaction response format matches contract."""

    def test_success_response_format(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Success response should match contract format."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=85.0,
            from_account="現金",
            to_account="餐飲",
            description="午餐",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        # Required top-level keys
        assert "success" in result
        assert "data" in result
        assert "message" in result

        # Required transaction keys
        tx = result["data"]["transaction"]
        assert "id" in tx
        assert "date" in tx
        assert "description" in tx
        assert "amount" in tx
        assert "from_account" in tx
        assert "to_account" in tx

        # Required account reference keys
        assert "id" in tx["from_account"]
        assert "name" in tx["from_account"]
        assert "id" in tx["to_account"]
        assert "name" in tx["to_account"]

    def test_error_response_format_account_not_found(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Error response for account not found should match contract."""
        user, ledger = user_with_ledger

        result = create_transaction(
            amount=85.0,
            from_account="現金",
            to_account="早餐",  # Non-existent account
            description="午餐",
            date="2026-01-11",
            notes=None,
            ledger_id=str(ledger.id),
            session=session,
            user=user,
        )

        # Required top-level keys
        assert result["success"] is False
        assert "error" in result

        # Required error keys per contract
        error = result["error"]
        assert "code" in error
        assert error["code"] == "ACCOUNT_NOT_FOUND"
        assert "message" in error
        assert "suggestions" in error  # Should suggest similar accounts
