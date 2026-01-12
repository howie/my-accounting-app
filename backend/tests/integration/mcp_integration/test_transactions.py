"""Integration tests for list_transactions MCP tool.

Tests the full flow including database queries and filters.
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
    transport = Account(
        ledger_id=ledger.id,
        name="交通",
        type=AccountType.EXPENSE,
        balance=Decimal("0"),
    )

    session.add_all([cash, food, transport])
    session.commit()
    for acc in [cash, food, transport]:
        session.refresh(acc)

    return {"cash": cash, "food": food, "transport": transport}


@pytest.fixture
def many_transactions(
    session: Session,
    user_with_ledger: tuple[User, Ledger],
    accounts: dict[str, Account],
) -> list[Transaction]:
    """Create many transactions for pagination testing."""
    _, ledger = user_with_ledger
    transactions = []

    for i in range(50):
        tx = Transaction(
            ledger_id=ledger.id,
            date=date(2026, 1, 1 + (i % 28)),  # Spread across January
            description=f"交易 {i + 1}",
            amount=Decimal(str(100 + i)),
            from_account_id=accounts["cash"].id,
            to_account_id=accounts["food"].id if i % 2 == 0 else accounts["transport"].id,
            transaction_type=TransactionType.EXPENSE,
        )
        transactions.append(tx)
        session.add(tx)

    session.commit()
    for tx in transactions:
        session.refresh(tx)

    return transactions


class TestListTransactionsAccountFilter:
    """Test account filtering."""

    def test_filter_by_account_id(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        many_transactions: list[Transaction],
    ):
        """Should filter by account ID."""
        user, ledger = user_with_ledger
        food = accounts["food"]

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=str(food.id),
            account_name=None,
            start_date=None,
            end_date=None,
            limit=100,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        # Half of 50 transactions go to food
        assert len(result["data"]["transactions"]) == 25
        for tx in result["data"]["transactions"]:
            assert tx["to_account"]["id"] == str(food.id)

    def test_filter_by_account_name(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        many_transactions: list[Transaction],
    ):
        """Should filter by account name."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name="交通",
            start_date=None,
            end_date=None,
            limit=100,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        # Half of 50 transactions go to transport
        assert len(result["data"]["transactions"]) == 25
        for tx in result["data"]["transactions"]:
            assert tx["to_account"]["name"] == "交通"


class TestListTransactionsPagination:
    """Test pagination functionality."""

    def test_default_limit(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        many_transactions: list[Transaction],
    ):
        """Should respect default limit."""
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
        assert len(result["data"]["transactions"]) == 20
        assert result["data"]["pagination"]["total"] == 50
        assert result["data"]["pagination"]["has_more"] is True

    def test_offset(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        many_transactions: list[Transaction],
    ):
        """Should skip transactions with offset."""
        user, ledger = user_with_ledger

        # Get first page
        result1 = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=10,
            offset=0,
            session=session,
            user=user,
        )

        # Get second page
        result2 = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=10,
            offset=10,
            session=session,
            user=user,
        )

        assert result1["success"] is True
        assert result2["success"] is True

        # Check no overlap
        ids1 = {tx["id"] for tx in result1["data"]["transactions"]}
        ids2 = {tx["id"] for tx in result2["data"]["transactions"]}
        assert ids1.isdisjoint(ids2)

    def test_has_more_false_on_last_page(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        many_transactions: list[Transaction],
    ):
        """has_more should be false on last page."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=20,
            offset=40,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["transactions"]) == 10  # Only 10 remaining
        assert result["data"]["pagination"]["has_more"] is False


class TestListTransactionsSummary:
    """Test summary calculation."""

    def test_summary_with_filter(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        many_transactions: list[Transaction],
    ):
        """Summary should reflect filtered results."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name="餐飲",
            start_date=None,
            end_date=None,
            limit=100,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        summary = result["data"]["summary"]
        assert summary["transaction_count"] == 25

        # Sum of 100, 102, 104, ... (even indices)
        expected_sum = sum(100 + i for i in range(0, 50, 2))
        assert summary["total_amount"] == float(expected_sum)

    def test_summary_respects_pagination_offset(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        many_transactions: list[Transaction],
    ):
        """Summary should show totals for all matching transactions (not just page)."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date=None,
            end_date=None,
            limit=10,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        # Summary should show total for ALL transactions, not just the 10 on page
        assert result["data"]["summary"]["transaction_count"] == 50


class TestListTransactionsEmptyResults:
    """Test empty result scenarios."""

    def test_empty_ledger(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
    ):
        """Should return empty list for ledger with no transactions."""
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
        assert len(result["data"]["transactions"]) == 0
        assert result["data"]["pagination"]["total"] == 0
        assert result["data"]["summary"]["transaction_count"] == 0
        assert result["data"]["summary"]["total_amount"] == 0.0

    def test_no_matching_date_range(
        self,
        session: Session,
        user_with_ledger: tuple[User, Ledger],
        accounts: dict[str, Account],
        many_transactions: list[Transaction],
    ):
        """Should return empty list when no transactions match date range."""
        user, ledger = user_with_ledger

        result = list_transactions(
            ledger_id=str(ledger.id),
            account_id=None,
            account_name=None,
            start_date="2025-01-01",
            end_date="2025-12-31",
            limit=20,
            offset=0,
            session=session,
            user=user,
        )

        assert result["success"] is True
        assert len(result["data"]["transactions"]) == 0
