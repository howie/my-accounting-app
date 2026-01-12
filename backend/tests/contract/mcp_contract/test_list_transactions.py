"""Contract tests for list_transactions MCP tool.

Tests the response format matches contracts/mcp-tools.md specification.
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
        balance=Decimal("3500"),
    )
    salary = Account(
        ledger_id=ledger.id,
        name="薪資",
        type=AccountType.INCOME,
        balance=Decimal("50000"),
    )
    bank = Account(
        ledger_id=ledger.id,
        name="銀行存款",
        type=AccountType.ASSET,
        balance=Decimal("50000"),
    )

    session.add_all([cash, food, salary, bank])
    session.commit()
    for acc in [cash, food, salary, bank]:
        session.refresh(acc)

    return {"cash": cash, "food": food, "salary": salary, "bank": bank}


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
        description="午餐 - 便當",
        amount=Decimal("85"),
        from_account_id=accounts["cash"].id,
        to_account_id=accounts["food"].id,
        transaction_type=TransactionType.EXPENSE,
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
    tx3 = Transaction(
        ledger_id=ledger.id,
        date=date(2026, 1, 5),
        description="月薪",
        amount=Decimal("50000"),
        from_account_id=accounts["salary"].id,
        to_account_id=accounts["bank"].id,
        transaction_type=TransactionType.INCOME,
    )

    session.add_all([tx1, tx2, tx3])
    session.commit()
    for tx in [tx1, tx2, tx3]:
        session.refresh(tx)

    return [tx1, tx2, tx3]


class TestListTransactionsContract:
    """Contract tests for list_transactions response format."""

    def test_success_response_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Response should match contract success schema."""
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

        # Top-level structure
        assert "success" in result
        assert result["success"] is True
        assert "data" in result
        assert "message" in result

        # Data structure
        data = result["data"]
        assert "transactions" in data
        assert "pagination" in data
        assert "summary" in data

    def test_transaction_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Transaction objects should match contract format."""
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

        for tx in result["data"]["transactions"]:
            assert "id" in tx
            assert "date" in tx
            assert "description" in tx
            assert "amount" in tx
            assert "from_account" in tx
            assert "to_account" in tx
            assert "notes" in tx

            # Account reference structure
            assert "id" in tx["from_account"]
            assert "name" in tx["from_account"]
            assert "id" in tx["to_account"]
            assert "name" in tx["to_account"]

    def test_pagination_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Pagination should match contract format."""
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

        pagination = result["data"]["pagination"]
        assert "total" in pagination
        assert "limit" in pagination
        assert "offset" in pagination
        assert "has_more" in pagination

        assert pagination["total"] == 3
        assert pagination["limit"] == 20
        assert pagination["offset"] == 0
        assert pagination["has_more"] is False

    def test_summary_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Summary should match contract format."""
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

        summary = result["data"]["summary"]
        assert "total_amount" in summary
        assert "transaction_count" in summary

        # 85 + 120 + 50000 = 50205
        assert summary["total_amount"] == 50205.0
        assert summary["transaction_count"] == 3

    def test_error_response_structure(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
    ):
        """Error response should match contract error schema."""
        user, _ = user_with_ledger

        result = list_transactions(
            ledger_id="invalid-uuid",
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
        assert "error" in result
        assert "code" in result["error"]
        assert "message" in result["error"]


class TestListTransactionsOrdering:
    """Test transaction ordering."""

    def test_ordered_by_date_desc(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Transactions should be ordered by date descending."""
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

        tx_list = result["data"]["transactions"]
        dates = [tx["date"] for tx in tx_list]
        assert dates == sorted(dates, reverse=True)


class TestListTransactionsDateFilter:
    """Test date filtering."""

    def test_filter_by_date_range(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Should filter by date range."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date="2026-01-10",
            end_date="2026-01-11",
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["transactions"]) == 2
        for tx in result["data"]["transactions"]:
            assert tx["date"] >= "2026-01-10"
            assert tx["date"] <= "2026-01-11"

    def test_filter_by_start_date_only(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Should filter by start date only."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date="2026-01-10",
            end_date=None,
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["transactions"]) == 2

    def test_filter_by_end_date_only(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        transactions: list[Transaction],
    ):
        """Should filter by end date only."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date="2026-01-05",
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["transactions"]) == 1
        assert result["data"]["transactions"][0]["description"] == "月薪"
