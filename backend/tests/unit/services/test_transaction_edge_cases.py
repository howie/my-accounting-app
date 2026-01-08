"""Edge case tests for transaction handling.

Tests for edge cases like same account transactions, negative amounts,
invalid account combinations, and boundary conditions.
"""

import uuid
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlmodel import Session

from src.models.account import AccountType
from src.models.transaction import TransactionType
from src.schemas.account import AccountCreate
from src.schemas.ledger import LedgerCreate
from src.schemas.transaction import TransactionCreate
from src.services.account_service import AccountService
from src.services.ledger_service import LedgerService
from src.services.transaction_service import TransactionService


class TestTransactionEdgeCases:
    """Edge case tests for TransactionService."""

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
    def cash_account_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        accounts = account_service.get_accounts(ledger_id)
        return next(a.id for a in accounts if a.name == "Cash")

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

    # --- Same account validation ---

    def test_transaction_same_from_and_to_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """Cannot create transaction where from and to are the same account."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid same account",
            amount=Decimal("100.00"),
            from_account_id=cash_account_id,
            to_account_id=cash_account_id,
            transaction_type=TransactionType.TRANSFER,
        )

        with pytest.raises(ValueError, match="same account"):
            service.create_transaction(ledger_id, data)

    # --- Amount validation ---

    def test_transaction_zero_amount_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Cannot create transaction with zero amount."""
        # Validation happens at schema level (Pydantic)
        with pytest.raises(ValidationError):
            TransactionCreate(
                date=date.today(),
                description="Zero amount",
                amount=Decimal("0.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            )

    def test_transaction_negative_amount_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Cannot create transaction with negative amount."""
        # Validation happens at schema level (Pydantic)
        with pytest.raises(ValidationError):
            TransactionCreate(
                date=date.today(),
                description="Negative amount",
                amount=Decimal("-50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            )

    def test_transaction_very_small_amount_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Transaction with very small (but positive) amount is valid."""
        data = TransactionCreate(
            date=date.today(),
            description="Small amount",
            amount=Decimal("0.01"),
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)
        assert result.amount == Decimal("0.01")

    def test_transaction_large_amount_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Transaction with large amount is valid."""
        data = TransactionCreate(
            date=date.today(),
            description="Large amount",
            amount=Decimal("999999999.99"),
            from_account_id=cash_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)
        assert result.amount == Decimal("999999999.99")

    # --- Account type validation for EXPENSE ---

    def test_expense_from_income_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        income_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """EXPENSE transaction from Income account is invalid."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid expense",
            amount=Decimal("50.00"),
            from_account_id=income_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        with pytest.raises(ValueError, match="(type|EXPENSE|Asset|Liability)"):
            service.create_transaction(ledger_id, data)

    def test_expense_to_income_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        income_account_id: uuid.UUID,
    ) -> None:
        """EXPENSE transaction to Income account is invalid."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid expense",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=income_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        with pytest.raises(ValueError, match="(type|EXPENSE|Expense)"):
            service.create_transaction(ledger_id, data)

    # --- Account type validation for INCOME ---

    def test_income_from_expense_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        expense_account_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """INCOME transaction from Expense account is invalid."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid income",
            amount=Decimal("50.00"),
            from_account_id=expense_account_id,
            to_account_id=cash_account_id,
            transaction_type=TransactionType.INCOME,
        )

        with pytest.raises(ValueError, match="(type|INCOME|Income)"):
            service.create_transaction(ledger_id, data)

    def test_income_to_expense_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        income_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """INCOME transaction to Expense account is invalid."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid income",
            amount=Decimal("50.00"),
            from_account_id=income_account_id,
            to_account_id=expense_account_id,
            transaction_type=TransactionType.INCOME,
        )

        with pytest.raises(ValueError, match="(type|INCOME|Asset|Liability)"):
            service.create_transaction(ledger_id, data)

    # --- Account type validation for TRANSFER ---

    def test_transfer_from_expense_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        expense_account_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """TRANSFER from Expense account is invalid."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid transfer",
            amount=Decimal("50.00"),
            from_account_id=expense_account_id,
            to_account_id=cash_account_id,
            transaction_type=TransactionType.TRANSFER,
        )

        with pytest.raises(ValueError, match="(type|TRANSFER|Asset|Liability)"):
            service.create_transaction(ledger_id, data)

    def test_transfer_to_income_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        income_account_id: uuid.UUID,
    ) -> None:
        """TRANSFER to Income account is invalid."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid transfer",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=income_account_id,
            transaction_type=TransactionType.TRANSFER,
        )

        with pytest.raises(ValueError, match="(type|TRANSFER|Asset|Liability)"):
            service.create_transaction(ledger_id, data)

    # --- Non-existent account validation ---

    def test_transaction_nonexistent_from_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Transaction with non-existent from_account raises error."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid",
            amount=Decimal("50.00"),
            from_account_id=uuid.uuid4(),
            to_account_id=expense_account_id,
            transaction_type=TransactionType.EXPENSE,
        )

        with pytest.raises(ValueError, match="(not found|does not exist|invalid)"):
            service.create_transaction(ledger_id, data)

    def test_transaction_nonexistent_to_account_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """Transaction with non-existent to_account raises error."""
        data = TransactionCreate(
            date=date.today(),
            description="Invalid",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=uuid.uuid4(),
            transaction_type=TransactionType.EXPENSE,
        )

        with pytest.raises(ValueError, match="(not found|does not exist|invalid)"):
            service.create_transaction(ledger_id, data)

    # --- Cross-ledger validation ---

    def test_transaction_accounts_from_different_ledgers_raises_error(
        self,
        service: TransactionService,
        ledger_service: LedgerService,
        account_service: AccountService,
        user_id: uuid.UUID,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """Transaction with accounts from different ledgers raises error."""
        # Create another ledger with its own accounts
        other_ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Other", initial_balance=Decimal("500.00"))
        )
        other_expense = account_service.create_account(
            other_ledger.id, AccountCreate(name="Other Expense", type=AccountType.EXPENSE)
        )

        data = TransactionCreate(
            date=date.today(),
            description="Cross-ledger",
            amount=Decimal("50.00"),
            from_account_id=cash_account_id,
            to_account_id=other_expense.id,
            transaction_type=TransactionType.EXPENSE,
        )

        with pytest.raises(ValueError, match="(ledger|different|belong)"):
            service.create_transaction(ledger_id, data)

    # --- Description validation ---

    def test_transaction_empty_description_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Transaction with empty description raises error."""
        # Validation happens at schema level (Pydantic)
        with pytest.raises(ValidationError):
            TransactionCreate(
                date=date.today(),
                description="",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            )

    def test_transaction_whitespace_description_raises_error(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Transaction with whitespace-only description raises error."""
        # Validation happens at schema level (Pydantic)
        with pytest.raises(ValidationError):
            TransactionCreate(
                date=date.today(),
                description="   ",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
            )
