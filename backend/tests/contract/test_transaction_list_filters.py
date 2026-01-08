"""Contract tests for transaction list filters.

Tests the filtering capabilities of the TransactionService as defined
in contracts/transaction_service.md.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.account import AccountType
from src.models.transaction import TransactionType
from src.schemas.account import AccountCreate
from src.schemas.ledger import LedgerCreate
from src.schemas.transaction import TransactionCreate
from src.services.account_service import AccountService
from src.services.ledger_service import LedgerService
from src.services.transaction_service import TransactionService


class TestTransactionListFilters:
    """Contract tests for transaction filtering per contracts/transaction_service.md."""

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
    def ledger_id(self, ledger_service: LedgerService, user_id: uuid.UUID) -> uuid.UUID:
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("10000.00"))
        )
        return ledger.id

    @pytest.fixture
    def cash_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        accounts = account_service.get_accounts(ledger_id)
        return next(a.id for a in accounts if a.name == "Cash")

    @pytest.fixture
    def food_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        return account.id

    @pytest.fixture
    def transport_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Transport", type=AccountType.EXPENSE)
        )
        return account.id

    @pytest.fixture
    def salary_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )
        return account.id

    @pytest.fixture
    def sample_transactions(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
        transport_id: uuid.UUID,
        salary_id: uuid.UUID,
    ) -> list:
        """Create sample transactions for testing filters."""
        today = date.today()
        transactions = []

        # Expense 1: Food
        transactions.append(
            service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=today - timedelta(days=5),
                    description="Grocery shopping",
                    amount=Decimal("50.00"),
                    from_account_id=cash_id,
                    to_account_id=food_id,
                    transaction_type=TransactionType.EXPENSE,
                ),
            )
        )

        # Expense 2: Transport
        transactions.append(
            service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=today - timedelta(days=3),
                    description="Bus ticket",
                    amount=Decimal("5.00"),
                    from_account_id=cash_id,
                    to_account_id=transport_id,
                    transaction_type=TransactionType.EXPENSE,
                ),
            )
        )

        # Expense 3: Food
        transactions.append(
            service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=today - timedelta(days=1),
                    description="Restaurant dinner",
                    amount=Decimal("75.00"),
                    from_account_id=cash_id,
                    to_account_id=food_id,
                    transaction_type=TransactionType.EXPENSE,
                ),
            )
        )

        # Income: Salary
        transactions.append(
            service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=today,
                    description="Monthly salary payment",
                    amount=Decimal("5000.00"),
                    from_account_id=salary_id,
                    to_account_id=cash_id,
                    transaction_type=TransactionType.INCOME,
                ),
            )
        )

        return transactions

    # --- Search by description ---

    def test_search_by_description_finds_matching(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Search returns transactions matching description."""
        result = service.get_transactions(ledger_id, search="grocery")

        assert len(result.data) >= 1
        descriptions = [tx.description.lower() for tx in result.data]
        assert any("grocery" in d for d in descriptions)

    def test_search_by_description_case_insensitive(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Search is case insensitive."""
        result_lower = service.get_transactions(ledger_id, search="salary")
        result_upper = service.get_transactions(ledger_id, search="SALARY")

        assert len(result_lower.data) == len(result_upper.data)

    def test_search_by_description_partial_match(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Search matches partial text."""
        result = service.get_transactions(ledger_id, search="ticket")

        assert len(result.data) >= 1
        descriptions = [tx.description.lower() for tx in result.data]
        assert any("ticket" in d for d in descriptions)

    def test_search_no_match_returns_empty(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Search with no matches returns empty list."""
        result = service.get_transactions(ledger_id, search="nonexistent123xyz")

        assert len(result.data) == 0

    # --- Filter by date range ---

    def test_filter_by_from_date(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Filter by from_date returns transactions on or after that date."""
        today = date.today()
        from_date = today - timedelta(days=2)

        result = service.get_transactions(ledger_id, from_date=from_date)

        for tx in result.data:
            tx_date = date.fromisoformat(tx.date) if isinstance(tx.date, str) else tx.date
            assert tx_date >= from_date

    def test_filter_by_to_date(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Filter by to_date returns transactions on or before that date."""
        today = date.today()
        to_date = today - timedelta(days=2)

        result = service.get_transactions(ledger_id, to_date=to_date)

        for tx in result.data:
            tx_date = date.fromisoformat(tx.date) if isinstance(tx.date, str) else tx.date
            assert tx_date <= to_date

    def test_filter_by_date_range(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Filter by date range returns transactions within range."""
        today = date.today()
        from_date = today - timedelta(days=4)
        to_date = today - timedelta(days=2)

        result = service.get_transactions(ledger_id, from_date=from_date, to_date=to_date)

        for tx in result.data:
            tx_date = date.fromisoformat(tx.date) if isinstance(tx.date, str) else tx.date
            assert from_date <= tx_date <= to_date

    def test_filter_single_day(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Filter for single day returns only that day's transactions."""
        today = date.today()

        result = service.get_transactions(ledger_id, from_date=today, to_date=today)

        for tx in result.data:
            tx_date = date.fromisoformat(tx.date) if isinstance(tx.date, str) else tx.date
            assert tx_date == today

    # --- Filter by account ---

    def test_filter_by_account_id(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        food_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Filter by account_id returns transactions involving that account."""
        result = service.get_transactions(ledger_id, account_id=food_id)

        assert len(result.data) >= 1
        for tx in result.data:
            assert tx.from_account.id == food_id or tx.to_account.id == food_id

    def test_filter_by_account_includes_from_and_to(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Filter by account returns transactions where account is from OR to."""
        result = service.get_transactions(ledger_id, account_id=cash_id)

        # Cash is involved in all sample transactions
        assert len(result.data) >= 4  # At least our 4 sample transactions

    # --- Filter by transaction type ---

    def test_filter_by_transaction_type_expense(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Filter by transaction_type returns only matching types."""
        result = service.get_transactions(ledger_id, transaction_type=TransactionType.EXPENSE)

        for tx in result.data:
            assert tx.transaction_type == TransactionType.EXPENSE

    def test_filter_by_transaction_type_income(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Filter by transaction_type income returns only income."""
        result = service.get_transactions(ledger_id, transaction_type=TransactionType.INCOME)

        for tx in result.data:
            assert tx.transaction_type == TransactionType.INCOME

    # --- Combined filters ---

    def test_combined_search_and_date_filter(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Search and date filters can be combined."""
        today = date.today()
        from_date = today - timedelta(days=6)

        result = service.get_transactions(ledger_id, search="grocery", from_date=from_date)

        for tx in result.data:
            assert "grocery" in tx.description.lower()
            tx_date = date.fromisoformat(tx.date) if isinstance(tx.date, str) else tx.date
            assert tx_date >= from_date

    def test_combined_account_and_type_filter(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        food_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """Account and type filters can be combined."""
        result = service.get_transactions(
            ledger_id,
            account_id=food_id,
            transaction_type=TransactionType.EXPENSE,
        )

        for tx in result.data:
            assert tx.transaction_type == TransactionType.EXPENSE
            assert tx.from_account.id == food_id or tx.to_account.id == food_id

    def test_all_filters_combined(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        sample_transactions: list,
    ) -> None:
        """All filters can be combined together."""
        today = date.today()
        result = service.get_transactions(
            ledger_id,
            search="salary",
            from_date=today,
            to_date=today,
            account_id=cash_id,
            transaction_type=TransactionType.INCOME,
        )

        for tx in result.data:
            assert "salary" in tx.description.lower()
            assert tx.transaction_type == TransactionType.INCOME
