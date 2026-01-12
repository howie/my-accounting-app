"""Contract tests for list_accounts MCP tool.

Tests the response format matches contracts/mcp-tools.md specification.
"""

from decimal import Decimal

import pytest
from sqlmodel import Session

from src.api.mcp.tools.accounts import list_accounts
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
    """Create test accounts."""
    _, ledger = user_with_ledger

    cash = Account(
        ledger_id=ledger.id,
        name="現金",
        type=AccountType.ASSET,
        balance=Decimal("15000"),
    )
    bank = Account(
        ledger_id=ledger.id,
        name="銀行存款",
        type=AccountType.ASSET,
        balance=Decimal("50000"),
    )
    food = Account(
        ledger_id=ledger.id,
        name="餐飲",
        type=AccountType.EXPENSE,
        balance=Decimal("3500"),
    )
    transport = Account(
        ledger_id=ledger.id,
        name="交通",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )
    salary = Account(
        ledger_id=ledger.id,
        name="薪資",
        type=AccountType.INCOME,
        balance=Decimal("50000"),
    )

    session.add_all([cash, bank, food, transport, salary])
    session.commit()
    for acc in [cash, bank, food, transport, salary]:
        session.refresh(acc)

    return {
        "cash": cash,
        "bank": bank,
        "food": food,
        "transport": transport,
        "salary": salary,
    }


class TestListAccountsContract:
    """Contract tests for list_accounts response format."""

    def test_success_response_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Response should match contract success schema."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter=None,
            include_zero_balance=True,
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
        assert "accounts" in data
        assert "summary" in data

        # Accounts structure
        assert len(data["accounts"]) == 5
        for account in data["accounts"]:
            assert "id" in account
            assert "name" in account
            assert "type" in account
            assert "balance" in account
            assert "parent_id" in account
            assert "depth" in account

    def test_summary_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Summary should contain all required fields."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        summary = result["data"]["summary"]
        assert "total_assets" in summary
        assert "total_liabilities" in summary
        assert "total_income" in summary
        assert "total_expenses" in summary

        # Verify calculated values
        assert summary["total_assets"] == 65000.0  # 15000 + 50000
        assert summary["total_expenses"] == 3500.0  # 3500 + 0
        assert summary["total_income"] == 50000.0

    def test_account_type_values(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Account type should be valid enum value."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        valid_types = {"ASSET", "LIABILITY", "INCOME", "EXPENSE"}
        for account in result["data"]["accounts"]:
            assert account["type"] in valid_types

    def test_error_response_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Error response should match contract error schema."""
        user, _ = user_with_ledger

        result = list_accounts(
            ledger_id="not-a-valid-uuid",
            type_filter=None,
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert "error" in result
        assert "code" in result["error"]
        assert "message" in result["error"]

    def test_type_filter_validation_error(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Invalid type filter should return VALIDATION_ERROR."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter="INVALID",
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is False
        assert result["error"]["code"] == "VALIDATION_ERROR"


class TestListAccountsFiltering:
    """Test filtering functionality."""

    def test_filter_by_type_asset(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should filter accounts by ASSET type."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter="ASSET",
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["accounts"]) == 2  # cash, bank
        for account in result["data"]["accounts"]:
            assert account["type"] == "ASSET"

    def test_filter_by_type_expense(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should filter accounts by EXPENSE type."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter="EXPENSE",
            include_zero_balance=True,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["accounts"]) == 2  # food, transport
        for account in result["data"]["accounts"]:
            assert account["type"] == "EXPENSE"

    def test_exclude_zero_balance(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should exclude accounts with zero balance when requested."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter=None,
            include_zero_balance=False,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["accounts"]) == 4  # Excludes transport (0 balance)
        for account in result["data"]["accounts"]:
            assert account["balance"] != 0

    def test_combined_filters(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should apply both type filter and zero balance exclusion."""
        user, ledger = user_with_ledger

        result = list_accounts(
            ledger_id=str(ledger.id),
            type_filter="EXPENSE",
            include_zero_balance=False,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["accounts"]) == 1  # Only food
        assert result["data"]["accounts"][0]["name"] == "餐飲"
