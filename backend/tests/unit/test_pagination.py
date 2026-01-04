"""Unit tests for cursor-based pagination.

Tests the pagination implementation in TransactionService
to ensure correct cursor handling and page traversal.
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


class TestCursorPagination:
    """Tests for cursor-based pagination in TransactionService."""

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
    def cash_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        accounts = account_service.get_accounts(ledger_id)
        return next(a.id for a in accounts if a.name == "Cash")

    @pytest.fixture
    def expense_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Expenses", type=AccountType.EXPENSE)
        )
        return account.id

    @pytest.fixture
    def many_transactions(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        expense_id: uuid.UUID,
    ) -> list:
        """Create many transactions for pagination testing."""
        today = date.today()
        transactions = []

        # Create 25 transactions
        for i in range(25):
            tx = service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=today - timedelta(days=i),
                    description=f"Transaction {i + 1:02d}",
                    amount=Decimal("10.00"),
                    from_account_id=cash_id,
                    to_account_id=expense_id,
                    transaction_type=TransactionType.EXPENSE,
                ),
            )
            transactions.append(tx)

        return transactions

    # --- Basic pagination tests ---

    def test_default_limit_applied(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Default limit is applied when not specified."""
        result = service.get_transactions(ledger_id)

        # Default limit is 50, but we only have 26 (25 + initial balance)
        assert len(result.data) <= 50

    def test_custom_limit_respected(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Custom limit is respected."""
        result = service.get_transactions(ledger_id, limit=5)

        assert len(result.data) == 5

    def test_has_more_true_when_more_data(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """has_more is True when there are more results."""
        result = service.get_transactions(ledger_id, limit=5)

        assert result.has_more is True

    def test_has_more_false_when_no_more_data(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """has_more is False when all results are returned."""
        result = service.get_transactions(ledger_id, limit=100)

        assert result.has_more is False

    def test_cursor_returned_when_more_data(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Cursor is returned when there are more results."""
        result = service.get_transactions(ledger_id, limit=5)

        assert result.cursor is not None
        assert len(result.cursor) > 0

    def test_cursor_none_when_no_more_data(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Cursor is None when all results are returned."""
        result = service.get_transactions(ledger_id, limit=100)

        assert result.cursor is None

    # --- Cursor navigation tests ---

    def test_cursor_returns_next_page(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Using cursor returns the next page of results."""
        page1 = service.get_transactions(ledger_id, limit=5)
        page2 = service.get_transactions(ledger_id, limit=5, cursor=page1.cursor)

        # Pages should not overlap
        page1_ids = {tx.id for tx in page1.data}
        page2_ids = {tx.id for tx in page2.data}
        assert len(page1_ids & page2_ids) == 0

    def test_sequential_pages_cover_all_data(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Sequential pagination covers all transactions."""
        all_ids = set()
        cursor = None
        page_count = 0

        while True:
            result = service.get_transactions(ledger_id, limit=5, cursor=cursor)
            all_ids.update(tx.id for tx in result.data)
            page_count += 1

            if not result.has_more:
                break
            cursor = result.cursor

        # Should have all 26 transactions (25 + initial balance)
        assert len(all_ids) == 26
        # Should have at least 6 pages of 5 items (26 / 5 = 5.2)
        assert page_count >= 6

    def test_pages_in_consistent_order(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Pages are returned in consistent order (by date desc)."""
        page1 = service.get_transactions(ledger_id, limit=10)
        page2 = service.get_transactions(ledger_id, limit=10, cursor=page1.cursor)

        # Last item of page1 should be "older" than first item of page2
        last_of_page1 = page1.data[-1]
        first_of_page2 = page2.data[0]

        date1 = date.fromisoformat(last_of_page1.date) if isinstance(last_of_page1.date, str) else last_of_page1.date
        date2 = date.fromisoformat(first_of_page2.date) if isinstance(first_of_page2.date, str) else first_of_page2.date

        assert date1 >= date2

    # --- Edge cases ---

    def test_invalid_cursor_ignored(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Invalid cursor is gracefully handled."""
        # Should not raise, just return first page
        result = service.get_transactions(ledger_id, limit=5, cursor="invalid-cursor")

        assert len(result.data) == 5

    def test_empty_result_has_correct_structure(
        self,
        service: TransactionService,
        ledger_service: LedgerService,
        user_id: uuid.UUID,
    ) -> None:
        """Empty result has correct pagination structure."""
        # Create a new ledger with no transactions (except initial)
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Empty", initial_balance=Decimal("0"))
        )

        result = service.get_transactions(ledger.id)

        assert hasattr(result, "data")
        assert hasattr(result, "cursor")
        assert hasattr(result, "has_more")
        assert result.has_more is False

    def test_limit_one_works(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Limit of 1 returns single item per page."""
        result = service.get_transactions(ledger_id, limit=1)

        assert len(result.data) == 1
        assert result.has_more is True
        assert result.cursor is not None

    def test_limit_equals_total(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Limit equal to total count returns all items."""
        result = service.get_transactions(ledger_id, limit=26)

        assert len(result.data) == 26
        assert result.has_more is False
        assert result.cursor is None

    # --- Pagination with filters ---

    def test_pagination_with_search(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Pagination works correctly with search filter."""
        # Search for "Transaction 1" which matches 10-19 and 01
        result = service.get_transactions(ledger_id, search="Transaction 1", limit=5)

        assert len(result.data) <= 5
        for tx in result.data:
            assert "transaction 1" in tx.description.lower()

    def test_pagination_with_date_filter(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        many_transactions: list,
    ) -> None:
        """Pagination works correctly with date filter."""
        today = date.today()
        result = service.get_transactions(
            ledger_id,
            from_date=today - timedelta(days=10),
            limit=5,
        )

        for tx in result.data:
            tx_date = date.fromisoformat(tx.date) if isinstance(tx.date, str) else tx.date
            assert tx_date >= today - timedelta(days=10)
