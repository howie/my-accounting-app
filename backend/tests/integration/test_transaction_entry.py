"""Integration tests for transaction entry flow (004-transaction-entry).

Tests the complete flow of creating transactions with the new
notes and amount_expression fields from User Story 1.
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
from src.schemas.transaction import TransactionCreate
from src.services.account_service import AccountService
from src.services.ledger_service import LedgerService
from src.services.transaction_service import TransactionService


class TestTransactionEntryFlow:
    """Integration tests for transaction entry (004-transaction-entry US1)."""

    @pytest.fixture
    def ledger_service(self, session: Session) -> LedgerService:
        return LedgerService(session)

    @pytest.fixture
    def account_service(self, session: Session) -> AccountService:
        return AccountService(session)

    @pytest.fixture
    def transaction_service(self, session: Session) -> TransactionService:
        return TransactionService(session)

    @pytest.fixture
    def user_id(self) -> uuid.UUID:
        return uuid.uuid4()

    @pytest.fixture
    def ledger_id(self, ledger_service: LedgerService, user_id: uuid.UUID) -> uuid.UUID:
        ledger = ledger_service.create_ledger(
            user_id, LedgerCreate(name="Test Ledger", initial_balance=Decimal("5000.00"))
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
            ledger_id, AccountCreate(name="Groceries", type=AccountType.EXPENSE)
        )
        return account.id

    @pytest.fixture
    def income_account_id(self, account_service: AccountService, ledger_id: uuid.UUID) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )
        return account.id

    # --- Transaction Entry with Notes ---

    def test_create_expense_with_notes_updates_balance_and_stores_notes(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Creating expense with notes updates balance and stores notes."""
        initial_balance = account_service.calculate_balance(cash_account_id)

        transaction = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Weekly groceries",
                amount=Decimal("150.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
                notes="Bought items for the week including fruits and vegetables",
            ),
        )

        # Verify notes stored
        assert transaction.notes == "Bought items for the week including fruits and vegetables"

        # Verify balance updated
        new_balance = account_service.calculate_balance(cash_account_id)
        assert new_balance == initial_balance - Decimal("150.00")

    def test_create_income_with_notes_updates_balance_and_stores_notes(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        income_account_id: uuid.UUID,
    ) -> None:
        """Creating income with notes updates balance and stores notes."""
        initial_balance = account_service.calculate_balance(cash_account_id)

        transaction = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Monthly salary",
                amount=Decimal("3000.00"),
                from_account_id=income_account_id,
                to_account_id=cash_account_id,
                transaction_type=TransactionType.INCOME,
                notes="January 2024 payment",
            ),
        )

        # Verify notes stored
        assert transaction.notes == "January 2024 payment"

        # Verify balance updated
        new_balance = account_service.calculate_balance(cash_account_id)
        assert new_balance == initial_balance + Decimal("3000.00")

    # --- Transaction Entry with Amount Expression ---

    def test_create_transaction_with_expression_stores_expression_and_amount(
        self,
        transaction_service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Creating transaction with expression stores both expression and calculated amount."""
        # User entered "50+40+10" in the frontend, which calculated to 100
        transaction = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Split bills",
                amount=Decimal("100.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
                amount_expression="50+40+10",
            ),
        )

        # Verify expression stored for audit trail
        assert transaction.amount_expression == "50+40+10"
        # Verify actual amount is the calculated value
        assert transaction.amount == Decimal("100.00")

    def test_create_transaction_with_complex_expression(
        self,
        transaction_service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Creating transaction with multiplication expression stores correctly."""
        # User entered "25*4" which equals 100
        transaction = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Weekly transport",
                amount=Decimal("100.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
                amount_expression="25*4",
            ),
        )

        assert transaction.amount_expression == "25*4"
        assert transaction.amount == Decimal("100.00")

    # --- Full Transaction Entry Flow ---

    def test_full_transaction_entry_flow_with_all_fields(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Complete transaction entry flow with all new fields."""
        initial_cash = account_service.calculate_balance(cash_account_id)
        initial_expense = account_service.calculate_balance(expense_account_id)

        # Create transaction with notes and expression
        transaction = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date(2024, 1, 15),
                description="Restaurant dinner",
                amount=Decimal("85.50"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
                notes="Birthday dinner with family at Italian restaurant",
                amount_expression="50+25.50+10",
            ),
        )

        # Verify all fields stored
        assert transaction.id is not None
        assert transaction.date == date(2024, 1, 15)
        assert transaction.description == "Restaurant dinner"
        assert transaction.amount == Decimal("85.50")
        assert transaction.notes == "Birthday dinner with family at Italian restaurant"
        assert transaction.amount_expression == "50+25.50+10"

        # Verify balances updated correctly
        final_cash = account_service.calculate_balance(cash_account_id)
        final_expense = account_service.calculate_balance(expense_account_id)

        assert final_cash == initial_cash - Decimal("85.50")
        assert final_expense == initial_expense + Decimal("85.50")

    def test_retrieve_transaction_includes_notes_and_expression(
        self,
        transaction_service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Retrieved transaction includes notes and amount_expression."""
        # Create transaction
        created = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Test retrieval",
                amount=Decimal("75.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
                notes="Test note for retrieval",
                amount_expression="50+25",
            ),
        )

        # Retrieve transaction
        retrieved = transaction_service.get_transaction(created.id, ledger_id)

        assert retrieved is not None
        assert retrieved.notes == "Test note for retrieval"
        assert retrieved.amount_expression == "50+25"

    # --- Account Pre-selection Validation ---

    def test_expense_requires_asset_or_liability_as_from_account(
        self,
        transaction_service: TransactionService,
        ledger_id: uuid.UUID,
        expense_account_id: uuid.UUID,
        income_account_id: uuid.UUID,
    ) -> None:
        """EXPENSE transaction must have Asset/Liability as from_account."""
        with pytest.raises(ValueError, match="EXPENSE.*from_account must be Asset or Liability"):
            transaction_service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=date.today(),
                    description="Invalid expense",
                    amount=Decimal("50.00"),
                    from_account_id=income_account_id,  # Invalid: Income as from
                    to_account_id=expense_account_id,
                    transaction_type=TransactionType.EXPENSE,
                ),
            )

    def test_different_accounts_required(
        self,
        transaction_service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
    ) -> None:
        """Transaction must have different from and to accounts."""
        with pytest.raises(ValueError, match="same account"):
            transaction_service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=date.today(),
                    description="Same account",
                    amount=Decimal("50.00"),
                    from_account_id=cash_account_id,
                    to_account_id=cash_account_id,  # Same as from
                    transaction_type=TransactionType.TRANSFER,
                ),
            )

    # --- Notes Validation ---

    def test_notes_max_length_is_500(
        self,
        transaction_service: TransactionService,
        ledger_id: uuid.UUID,
        cash_account_id: uuid.UUID,
        expense_account_id: uuid.UUID,
    ) -> None:
        """Notes field accepts up to 500 characters."""
        long_notes = "A" * 500  # Exactly 500 characters

        transaction = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Long notes test",
                amount=Decimal("50.00"),
                from_account_id=cash_account_id,
                to_account_id=expense_account_id,
                transaction_type=TransactionType.EXPENSE,
                notes=long_notes,
            ),
        )

        assert len(transaction.notes) == 500
