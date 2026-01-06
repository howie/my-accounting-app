"""Unit tests for DashboardService.

Tests for feature 002-ui-layout-dashboard.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType
from src.models.user import User
from src.services.dashboard_service import DashboardService


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="test@example.com")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    """Create a test ledger."""
    ledger = Ledger(user_id=user.id, name="Test Ledger")
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


@pytest.fixture
def accounts(session: Session, ledger: Ledger) -> dict[str, Account]:
    """Create test accounts for each type."""
    accounts_dict = {}

    # Create asset accounts
    cash = Account(
        ledger_id=ledger.id,
        name="Cash",
        type=AccountType.ASSET,
        is_system=True,
    )
    bank = Account(
        ledger_id=ledger.id,
        name="Bank Account",
        type=AccountType.ASSET,
    )

    # Create liability account
    credit_card = Account(
        ledger_id=ledger.id,
        name="Credit Card",
        type=AccountType.LIABILITY,
    )

    # Create income account
    salary = Account(
        ledger_id=ledger.id,
        name="Salary",
        type=AccountType.INCOME,
    )

    # Create expense account
    food = Account(
        ledger_id=ledger.id,
        name="Food",
        type=AccountType.EXPENSE,
    )

    for account in [cash, bank, credit_card, salary, food]:
        session.add(account)

    session.commit()

    for account in [cash, bank, credit_card, salary, food]:
        session.refresh(account)

    accounts_dict["cash"] = cash
    accounts_dict["bank"] = bank
    accounts_dict["credit_card"] = credit_card
    accounts_dict["salary"] = salary
    accounts_dict["food"] = food

    return accounts_dict


class TestGetDashboardSummary:
    """Tests for get_dashboard_summary method."""

    def test_returns_zero_for_empty_ledger(
        self, session: Session, ledger: Ledger
    ):
        """Dashboard should return zeros when ledger has no transactions."""
        service = DashboardService(session)
        result = service.get_dashboard_summary(ledger.id)

        assert result["total_assets"] == Decimal("0")
        assert result["current_month"]["income"] == 0.0
        assert result["current_month"]["expenses"] == 0.0
        assert result["current_month"]["net_cash_flow"] == 0.0
        assert len(result["trends"]) == 6

    def test_calculates_total_assets(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Total assets should sum all ASSET account balances."""
        # Create income transaction (salary -> cash)
        income_txn = Transaction(
            ledger_id=ledger.id,
            date=date.today(),
            description="Salary deposit",
            amount=Decimal("5000.00"),
            from_account_id=accounts["salary"].id,
            to_account_id=accounts["cash"].id,
            transaction_type=TransactionType.INCOME,
        )
        session.add(income_txn)
        session.commit()

        service = DashboardService(session)
        result = service.get_dashboard_summary(ledger.id)

        # Cash should have 5000 (incoming)
        assert result["total_assets"] == Decimal("5000.00")

    def test_calculates_current_month_income_expenses(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Current month should show income and expenses for this month."""
        today = date.today()

        # Income transaction
        income_txn = Transaction(
            ledger_id=ledger.id,
            date=today,
            description="Salary",
            amount=Decimal("3000.00"),
            from_account_id=accounts["salary"].id,
            to_account_id=accounts["cash"].id,
            transaction_type=TransactionType.INCOME,
        )

        # Expense transaction
        expense_txn = Transaction(
            ledger_id=ledger.id,
            date=today,
            description="Groceries",
            amount=Decimal("200.00"),
            from_account_id=accounts["cash"].id,
            to_account_id=accounts["food"].id,
            transaction_type=TransactionType.EXPENSE,
        )

        session.add(income_txn)
        session.add(expense_txn)
        session.commit()

        service = DashboardService(session)
        result = service.get_dashboard_summary(ledger.id)

        assert result["current_month"]["income"] == 3000.0
        assert result["current_month"]["expenses"] == 200.0
        assert result["current_month"]["net_cash_flow"] == 2800.0

    def test_raises_error_for_nonexistent_ledger(self, session: Session):
        """Should raise ValueError for non-existent ledger."""
        service = DashboardService(session)
        fake_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Ledger not found"):
            service.get_dashboard_summary(fake_id)


class TestGetAccountsByCategory:
    """Tests for get_accounts_by_category method."""

    def test_returns_empty_categories_for_new_ledger(
        self, session: Session, ledger: Ledger
    ):
        """Should return all categories even when empty."""
        service = DashboardService(session)
        result = service.get_accounts_by_category(ledger.id)

        assert len(result["categories"]) == 4
        assert result["categories"][0]["type"] == "ASSET"
        assert result["categories"][1]["type"] == "LIABILITY"
        assert result["categories"][2]["type"] == "INCOME"
        assert result["categories"][3]["type"] == "EXPENSE"

    def test_groups_accounts_by_type(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Accounts should be grouped by their type."""
        service = DashboardService(session)
        result = service.get_accounts_by_category(ledger.id)

        # Find asset category
        asset_category = next(
            c for c in result["categories"] if c["type"] == "ASSET"
        )
        assert len(asset_category["accounts"]) == 2  # Cash, Bank Account

        # Find expense category
        expense_category = next(
            c for c in result["categories"] if c["type"] == "EXPENSE"
        )
        assert len(expense_category["accounts"]) == 1  # Food

    def test_includes_account_balances(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Each account should include its calculated balance."""
        # Add a transaction
        income_txn = Transaction(
            ledger_id=ledger.id,
            date=date.today(),
            description="Income",
            amount=Decimal("1000.00"),
            from_account_id=accounts["salary"].id,
            to_account_id=accounts["cash"].id,
            transaction_type=TransactionType.INCOME,
        )
        session.add(income_txn)
        session.commit()

        service = DashboardService(session)
        result = service.get_accounts_by_category(ledger.id)

        # Find cash account
        asset_category = next(
            c for c in result["categories"] if c["type"] == "ASSET"
        )
        cash_account = next(
            a for a in asset_category["accounts"] if a["name"] == "Cash"
        )
        assert cash_account["balance"] == 1000.0


class TestGetAccountTransactions:
    """Tests for get_account_transactions method."""

    def test_returns_empty_for_account_without_transactions(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Should return empty list when account has no transactions."""
        service = DashboardService(session)
        result = service.get_account_transactions(accounts["cash"].id)

        assert result["account_name"] == "Cash"
        assert result["transactions"] == []
        assert result["total_count"] == 0
        assert result["has_more"] is False

    def test_returns_transactions_for_account(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Should return transactions involving the account."""
        # Add transaction
        txn = Transaction(
            ledger_id=ledger.id,
            date=date.today(),
            description="Test transaction",
            amount=Decimal("100.00"),
            from_account_id=accounts["salary"].id,
            to_account_id=accounts["cash"].id,
            transaction_type=TransactionType.INCOME,
        )
        session.add(txn)
        session.commit()

        service = DashboardService(session)
        result = service.get_account_transactions(accounts["cash"].id)

        assert len(result["transactions"]) == 1
        assert result["transactions"][0]["description"] == "Test transaction"
        assert result["transactions"][0]["amount"] == 100.0
        assert result["transactions"][0]["other_account_name"] == "Salary"

    def test_paginates_transactions(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Should paginate when many transactions exist."""
        # Add multiple transactions
        for i in range(10):
            txn = Transaction(
                ledger_id=ledger.id,
                date=date.today() - timedelta(days=i),
                description=f"Transaction {i}",
                amount=Decimal("10.00"),
                from_account_id=accounts["cash"].id,
                to_account_id=accounts["food"].id,
                transaction_type=TransactionType.EXPENSE,
            )
            session.add(txn)
        session.commit()

        service = DashboardService(session)

        # Get first page
        result = service.get_account_transactions(
            accounts["cash"].id, page=1, page_size=5
        )
        assert len(result["transactions"]) == 5
        assert result["total_count"] == 10
        assert result["has_more"] is True

        # Get second page
        result = service.get_account_transactions(
            accounts["cash"].id, page=2, page_size=5
        )
        assert len(result["transactions"]) == 5
        assert result["has_more"] is False

    def test_raises_error_for_nonexistent_account(self, session: Session):
        """Should raise ValueError for non-existent account."""
        service = DashboardService(session)
        fake_id = uuid.uuid4()

        with pytest.raises(ValueError, match="Account not found"):
            service.get_account_transactions(fake_id)

    def test_raises_error_for_invalid_page(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Should raise ValueError for invalid page number."""
        service = DashboardService(session)

        with pytest.raises(ValueError, match="Page number"):
            service.get_account_transactions(accounts["cash"].id, page=0)

    def test_raises_error_for_invalid_page_size(
        self, session: Session, ledger: Ledger, accounts: dict[str, Account]
    ):
        """Should raise ValueError for invalid page size."""
        service = DashboardService(session)

        with pytest.raises(ValueError, match="Page size"):
            service.get_account_transactions(
                accounts["cash"].id, page_size=101
            )
