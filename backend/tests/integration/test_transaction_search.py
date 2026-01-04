"""Integration tests for transaction search and filtering.

Tests the complete search/filter flow from data creation to retrieval.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.account import AccountType
from src.models.transaction import TransactionType
from src.services.transaction_service import TransactionService
from src.services.ledger_service import LedgerService
from src.services.account_service import AccountService
from src.schemas.transaction import TransactionCreate
from src.schemas.ledger import LedgerCreate
from src.schemas.account import AccountCreate


class TestTransactionSearchIntegration:
    """Integration tests for transaction search functionality."""

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        return LedgerService(session)

    @pytest.fixture
    def account_service(self, session: Session) -> AccountService:
        return AccountService(session)

    @pytest.fixture
    def service(self, session: Session) -> TransactionService:
        return TransactionService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def ledger_id(
        self, ledger_service: LedgerService, user_id: uuid.UUID
    ) -> uuid.UUID:
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("10000.00"))
        )
        return ledger.id

    @pytest.fixture
    def setup_accounts(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> dict:
        """Create a set of accounts for testing."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        rent = account_service.create_account(
            ledger_id, AccountCreate(name="Rent", type=AccountType.EXPENSE)
        )
        utilities = account_service.create_account(
            ledger_id, AccountCreate(name="Utilities", type=AccountType.EXPENSE)
        )
        salary = account_service.create_account(
            ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )
        bonus = account_service.create_account(
            ledger_id, AccountCreate(name="Bonus", type=AccountType.INCOME)
        )
        savings = account_service.create_account(
            ledger_id, AccountCreate(name="Savings", type=AccountType.ASSET)
        )

        return {
            "cash": cash.id,
            "food": food.id,
            "rent": rent.id,
            "utilities": utilities.id,
            "salary": salary.id,
            "bonus": bonus.id,
            "savings": savings.id,
        }

    @pytest.fixture
    def create_transactions(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        setup_accounts: dict,
    ) -> list:
        """Create a variety of transactions for search testing."""
        today = date.today()
        transactions = []

        # Create transactions over the past month
        test_data = [
            # (days_ago, description, amount, from_key, to_key, type)
            (30, "Monthly rent payment", "1500.00", "cash", "rent", "EXPENSE"),
            (28, "Grocery store", "120.50", "cash", "food", "EXPENSE"),
            (25, "Electric bill", "85.00", "cash", "utilities", "EXPENSE"),
            (20, "Restaurant dinner", "45.00", "cash", "food", "EXPENSE"),
            (15, "Monthly salary", "5000.00", "salary", "cash", "INCOME"),
            (14, "Gas bill", "55.00", "cash", "utilities", "EXPENSE"),
            (10, "Grocery shopping", "95.00", "cash", "food", "EXPENSE"),
            (7, "Water bill", "30.00", "cash", "utilities", "EXPENSE"),
            (5, "Fast food lunch", "15.00", "cash", "food", "EXPENSE"),
            (3, "Transfer to savings", "500.00", "cash", "savings", "TRANSFER"),
            (1, "Quarterly bonus", "1000.00", "bonus", "cash", "INCOME"),
            (0, "Coffee shop", "8.50", "cash", "food", "EXPENSE"),
        ]

        for days_ago, desc, amount, from_key, to_key, tx_type in test_data:
            tx = service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=today - timedelta(days=days_ago),
                    description=desc,
                    amount=Decimal(amount),
                    from_account_id=setup_accounts[from_key],
                    to_account_id=setup_accounts[to_key],
                    transaction_type=TransactionType[tx_type],
                ),
            )
            transactions.append(tx)

        return transactions

    # --- Search functionality tests ---

    def test_search_finds_exact_match(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Search finds transactions with exact description match."""
        result = service.get_transactions(ledger_id, search="Monthly rent payment")

        assert len(result.data) == 1
        assert result.data[0].description == "Monthly rent payment"

    def test_search_finds_multiple_matches(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Search finds all matching transactions."""
        result = service.get_transactions(ledger_id, search="bill")

        # Should find: Electric bill, Gas bill, Water bill
        assert len(result.data) == 3
        for tx in result.data:
            assert "bill" in tx.description.lower()

    def test_search_word_boundary(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Search handles word boundaries correctly."""
        result = service.get_transactions(ledger_id, search="grocery")

        # Should find: Grocery store, Grocery shopping
        assert len(result.data) == 2
        for tx in result.data:
            assert "grocery" in tx.description.lower()

    # --- Date range filtering tests ---

    def test_filter_last_week(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Filter returns transactions from last 7 days."""
        today = date.today()
        week_ago = today - timedelta(days=7)

        result = service.get_transactions(ledger_id, from_date=week_ago)

        # Should include transactions from days 0, 1, 3, 5, 7
        for tx in result.data:
            tx_date = date.fromisoformat(tx.date) if isinstance(tx.date, str) else tx.date
            assert tx_date >= week_ago

    def test_filter_specific_month(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Filter returns transactions within a specific date range."""
        today = date.today()
        from_date = today - timedelta(days=20)
        to_date = today - timedelta(days=10)

        result = service.get_transactions(ledger_id, from_date=from_date, to_date=to_date)

        for tx in result.data:
            tx_date = date.fromisoformat(tx.date) if isinstance(tx.date, str) else tx.date
            assert from_date <= tx_date <= to_date

    # --- Account filtering tests ---

    def test_filter_by_expense_account(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        setup_accounts: dict,
        create_transactions: list,
    ) -> None:
        """Filter by expense account returns all related transactions."""
        food_id = setup_accounts["food"]
        result = service.get_transactions(ledger_id, account_id=food_id)

        # All food-related transactions
        assert len(result.data) >= 4  # Grocery store, Restaurant, Grocery shopping, Fast food, Coffee
        for tx in result.data:
            assert tx.from_account.id == food_id or tx.to_account.id == food_id

    def test_filter_by_income_account(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        setup_accounts: dict,
        create_transactions: list,
    ) -> None:
        """Filter by income account returns income transactions."""
        salary_id = setup_accounts["salary"]
        result = service.get_transactions(ledger_id, account_id=salary_id)

        assert len(result.data) == 1
        assert result.data[0].description == "Monthly salary"

    # --- Transaction type filtering tests ---

    def test_filter_expenses_only(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Filter returns only expense transactions."""
        result = service.get_transactions(
            ledger_id, transaction_type=TransactionType.EXPENSE
        )

        for tx in result.data:
            assert tx.transaction_type == TransactionType.EXPENSE

    def test_filter_income_only(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Filter returns only income transactions."""
        result = service.get_transactions(
            ledger_id, transaction_type=TransactionType.INCOME
        )

        # Should find: Monthly salary, Quarterly bonus
        assert len(result.data) == 2
        for tx in result.data:
            assert tx.transaction_type == TransactionType.INCOME

    def test_filter_transfers_only(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Filter returns only transfer transactions."""
        result = service.get_transactions(
            ledger_id, transaction_type=TransactionType.TRANSFER
        )

        # 2 transfers: Initial balance + Transfer to savings
        assert len(result.data) == 2
        for tx in result.data:
            assert tx.transaction_type == TransactionType.TRANSFER
        # One of them should be our explicit transfer
        descriptions = [tx.description for tx in result.data]
        assert "Transfer to savings" in descriptions

    # --- Combined filters tests ---

    def test_search_within_date_range(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Search combined with date range narrows results."""
        today = date.today()
        result = service.get_transactions(
            ledger_id,
            search="grocery",
            from_date=today - timedelta(days=15),
        )

        # Only "Grocery shopping" (10 days ago), not "Grocery store" (28 days ago)
        assert len(result.data) == 1
        assert "grocery" in result.data[0].description.lower()

    def test_account_filter_with_type(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        setup_accounts: dict,
        create_transactions: list,
    ) -> None:
        """Account filter combined with type filter."""
        cash_id = setup_accounts["cash"]
        result = service.get_transactions(
            ledger_id,
            account_id=cash_id,
            transaction_type=TransactionType.INCOME,
        )

        # All income transactions involve cash (as destination)
        assert len(result.data) == 2
        for tx in result.data:
            assert tx.transaction_type == TransactionType.INCOME

    def test_all_filters_together(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        setup_accounts: dict,
        create_transactions: list,
    ) -> None:
        """All filters work together to narrow results."""
        today = date.today()
        result = service.get_transactions(
            ledger_id,
            search="bill",
            from_date=today - timedelta(days=20),
            to_date=today - timedelta(days=10),
            transaction_type=TransactionType.EXPENSE,
        )

        # Only "Gas bill" (14 days ago) matches all criteria
        assert len(result.data) == 1
        assert result.data[0].description == "Gas bill"

    # --- Edge cases ---

    def test_empty_search_returns_all(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Empty search string returns all transactions."""
        result_all = service.get_transactions(ledger_id)
        result_empty = service.get_transactions(ledger_id, search="")

        assert len(result_all.data) == len(result_empty.data)

    def test_future_date_range_returns_empty(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Date range in the future returns no results."""
        tomorrow = date.today() + timedelta(days=1)
        next_week = date.today() + timedelta(days=7)

        result = service.get_transactions(ledger_id, from_date=tomorrow, to_date=next_week)

        assert len(result.data) == 0

    def test_nonexistent_account_returns_empty(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        create_transactions: list,
    ) -> None:
        """Filter by non-existent account returns empty list."""
        result = service.get_transactions(ledger_id, account_id=uuid.uuid4())

        assert len(result.data) == 0
