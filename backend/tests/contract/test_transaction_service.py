"""Contract tests for TransactionService.

Tests the service interface contract as defined in contracts/transaction_service.md.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlmodel import Session

from src.models.account import AccountType
from src.models.transaction import TransactionType
from src.schemas.account import AccountCreate
from src.schemas.ledger import LedgerCreate
from src.schemas.transaction import TransactionCreate, TransactionUpdate
from src.services.account_service import AccountService
from src.services.ledger_service import LedgerService
from src.services.transaction_service import TransactionService


class TestTransactionServiceContract:
    """Contract tests for TransactionService per contracts/transaction_service.md."""

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
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        return ledger.id

    @pytest.fixture
    def expense_account_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        return account.id

    @pytest.fixture
    def income_account_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )
        return account.id

    @pytest.fixture
    def cash_account_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        accounts = account_service.get_accounts(ledger_id)
        return next(a.id for a in accounts if a.name == "Cash")

    @pytest.fixture
    def bank_account_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Bank", type=AccountType.ASSET)
        )
        return account.id

    # --- create_transaction ---

    def test_create_transaction_returns_transaction_with_id(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Creating a transaction returns a Transaction with a valid UUID id."""
        data = TransactionCreate(
            date=date.today(),
            description="Test expense",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)

        assert result.id is not None
        assert isinstance(result.id, uuid.UUID)

    def test_create_transaction_stores_ledger_id(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Created transaction is associated with the provided ledger_id."""
        data = TransactionCreate(
            date=date.today(),
            description="Test",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)

        assert result.ledger_id == ledger_id

    def test_create_transaction_stores_all_fields(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Created transaction stores all provided fields."""
        today = date.today()
        data = TransactionCreate(
            date=today,
            description="Lunch",
            amount=Decimal("25.50"),
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)

        assert result.date == today
        assert result.description == "Lunch"
        assert result.amount == Decimal("25.50")
        assert result.from_account_id == cash_account_id
        assert result.to_account_id == expense_account_id
        assert result.transaction_type == TransactionType.EXPENSE

    def test_create_transaction_has_timestamps(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Created transaction has created_at and updated_at timestamps."""
        data = TransactionCreate(
            date=date.today(),
            description="Test",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)

        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_expense_transaction_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """EXPENSE: from Asset → to Expense is valid."""
        data = TransactionCreate(
            date=date.today(),
            description="Valid expense",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)
        assert result is not None

    def test_create_income_transaction_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        income_account_id: uuid.UUID,
    ) -> None:
        """INCOME: from Income → to Asset is valid."""
        data = TransactionCreate(
            date=date.today(),
            description="Valid income",
            amount=Decimal("1000.00"),
            from_account_id=income_account_id,
            to_account_id=cash_account_id,
            transaction_type=TransactionType.INCOME,
        )

        result = service.create_transaction(ledger_id, data)
        assert result is not None

    def test_create_transfer_transaction_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        bank_account_id: uuid.UUID,
    ) -> None:
        """TRANSFER: from Asset → to Asset is valid."""
        data = TransactionCreate(
            date=date.today(),
            description="Valid transfer",
            amount=Decimal("500.00"),
            from_account_id=cash_account_id,
            to_account_id=bank_account_id,
            transaction_type=TransactionType.TRANSFER,
        )

        result = service.create_transaction(ledger_id, data)
        assert result is not None

    def test_create_transaction_same_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """Cannot create transaction with same from and to account."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=cash_account_id,
            transaction_type=TransactionType.TRANSFER,
        )

        with pytest.raises(ValueError, match="same account"):
            service.create_transaction(ledger_id, data)

    def test_create_expense_invalid_from_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        income_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """EXPENSE from Income account raises error."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid expense",
            amount=Decimal("50.00"),
            from_account_id=income_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        with pytest.raises(ValueError, match="(type|EXPENSE)"):
            service.create_transaction(ledger_id, data)

    def test_create_income_invalid_to_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        income_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """INCOME to Expense account raises error."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid income",
            amount=Decimal("50.00"),
            from_account_id=income_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.INCOME,
        )

        with pytest.raises(ValueError, match="(type|INCOME)"):
            service.create_transaction(ledger_id, data)

    # --- get_transactions ---

    def test_get_transactions_returns_paginated_result(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
    ) -> None:
        """get_transactions returns paginated result with data, cursor, has_more."""
        result = service.get_transactions(ledger_id)

        assert hasattr(result, "data")
        assert hasattr(result, "cursor")
        assert hasattr(result, "has_more")
        assert isinstance(result.data, list)

    def test_get_transactions_returns_created_transactions(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """get_transactions returns transactions after creation."""
        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Test",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        result = service.get_transactions(ledger_id)

        # Should include initial balance transaction + our new one
        assert len(result.data) >= 1

    def test_get_transactions_includes_account_details(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """get_transactions includes from_account and to_account details."""
        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Test",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        result = service.get_transactions(ledger_id)

        tx = next(t for t in result.data if t.description == "Test")
        assert tx.from_account is not None
        assert tx.to_account is not None
        assert tx.from_account.name == "Cash"
        assert tx.to_account.name == "Food"

    # --- get_transaction ---

    def test_get_transaction_returns_transaction_by_id(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """get_transaction returns the transaction with the specified ID."""
        created = service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Find me",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        result = service.get_transaction(created.id, ledger_id)

        assert result is not None
        assert result.id == created.id
        assert result.description == "Find me"

    def test_get_transaction_returns_none_for_nonexistent(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
    ) -> None:
        """get_transaction returns None for non-existent transaction ID."""
        result = service.get_transaction(uuid.uuid4(), ledger_id)
        assert result is None

    # --- update_transaction ---

    def test_update_transaction_changes_fields(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """update_transaction changes the transaction fields."""
        created = service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Original",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        result = service.update_transaction(
            created.id,
            ledger_id,
            TransactionUpdate(
                date=date.today(),
                description="Updated",
                amount=Decimal("75.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        assert result is not None
        assert result.description == "Updated"
        assert result.amount == Decimal("75.00")

    def test_update_transaction_returns_none_for_nonexistent(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """update_transaction returns None for non-existent transaction."""
        result = service.update_transaction(
            uuid.uuid4(),
            ledger_id,
            TransactionUpdate(
                date=date.today(),
                description="Test",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )
        assert result is None

    # --- delete_transaction ---

    def test_delete_transaction_returns_true_on_success(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """delete_transaction returns True when transaction is deleted."""
        created = service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="To delete",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        result = service.delete_transaction(created.id, ledger_id)
        assert result is True

    def test_delete_transaction_removes_transaction(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """delete_transaction removes the transaction from the database."""
        created = service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="To delete",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        service.delete_transaction(created.id, ledger_id)

        assert service.get_transaction(created.id, ledger_id) is None

    def test_delete_transaction_returns_false_for_nonexistent(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
    ) -> None:
        """delete_transaction returns False for non-existent transaction."""
        result = service.delete_transaction(uuid.uuid4(), ledger_id)
        assert result is False
