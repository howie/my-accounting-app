"""Integration tests for transaction flow.

Tests the complete flow of creating transactions and verifying
account balances are updated correctly.
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


class TestTransactionFlow:
    """Integration tests for transaction creation and balance updates."""

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
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        return ledger.id

    def test_expense_decreases_asset_balance(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Creating an expense transaction decreases Asset balance."""
        # Get Cash account
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        # Create expense account
        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        initial_balance = account_service.calculate_balance(cash.id)
        assert initial_balance == Decimal("1000.00")

        # Create expense
        transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Lunch",
                amount=Decimal("50.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        new_balance = account_service.calculate_balance(cash.id)
        assert new_balance == Decimal("950.00")

    def test_expense_increases_expense_balance(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Creating an expense transaction increases Expense balance."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        initial_balance = account_service.calculate_balance(food.id)
        assert initial_balance == Decimal("0.00")

        transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Lunch",
                amount=Decimal("50.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        new_balance = account_service.calculate_balance(food.id)
        assert new_balance == Decimal("50.00")

    def test_income_increases_asset_balance(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Creating an income transaction increases Asset balance."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        salary = account_service.create_account(
            ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )

        initial_balance = account_service.calculate_balance(cash.id)
        assert initial_balance == Decimal("1000.00")

        transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Monthly salary",
                amount=Decimal("3000.00"),
                from_account_id=salary.id,
                to_account_id=cash.id,
                transaction_type=TransactionType.INCOME,
            ),
        )

        new_balance = account_service.calculate_balance(cash.id)
        assert new_balance == Decimal("4000.00")

    def test_income_increases_income_balance(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Creating an income transaction increases Income balance."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        salary = account_service.create_account(
            ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )

        initial_balance = account_service.calculate_balance(salary.id)
        assert initial_balance == Decimal("0.00")

        transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Monthly salary",
                amount=Decimal("3000.00"),
                from_account_id=salary.id,
                to_account_id=cash.id,
                transaction_type=TransactionType.INCOME,
            ),
        )

        new_balance = account_service.calculate_balance(salary.id)
        assert new_balance == Decimal("3000.00")

    def test_transfer_moves_between_assets(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Transfer moves money between asset accounts."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        bank = account_service.create_account(
            ledger_id, AccountCreate(name="Bank", type=AccountType.ASSET)
        )

        # Initial balances
        assert account_service.calculate_balance(cash.id) == Decimal("1000.00")
        assert account_service.calculate_balance(bank.id) == Decimal("0.00")

        # Transfer
        transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Deposit to bank",
                amount=Decimal("500.00"),
                from_account_id=cash.id,
                to_account_id=bank.id,
                transaction_type=TransactionType.TRANSFER,
            ),
        )

        # New balances
        assert account_service.calculate_balance(cash.id) == Decimal("500.00")
        assert account_service.calculate_balance(bank.id) == Decimal("500.00")

    def test_delete_transaction_reverses_balance(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Deleting a transaction reverses its effect on balances."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        # Create and then delete a transaction
        tx = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Lunch",
                amount=Decimal("50.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        # Balance after transaction
        assert account_service.calculate_balance(cash.id) == Decimal("950.00")
        assert account_service.calculate_balance(food.id) == Decimal("50.00")

        # Delete transaction
        transaction_service.delete_transaction(tx.id, ledger_id)

        # Balance restored
        assert account_service.calculate_balance(cash.id) == Decimal("1000.00")
        assert account_service.calculate_balance(food.id) == Decimal("0.00")

    def test_update_transaction_adjusts_balance(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Updating transaction amount adjusts balances correctly."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        # Create transaction
        tx = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Lunch",
                amount=Decimal("50.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        assert account_service.calculate_balance(cash.id) == Decimal("950.00")

        # Update to higher amount
        from src.schemas.transaction import TransactionUpdate

        transaction_service.update_transaction(
            tx.id,
            ledger_id,
            TransactionUpdate(
                date=date.today(),
                description="Fancy lunch",
                amount=Decimal("100.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        assert account_service.calculate_balance(cash.id) == Decimal("900.00")
        assert account_service.calculate_balance(food.id) == Decimal("100.00")

    def test_multiple_transactions_accumulate(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Multiple transactions accumulate correctly."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        # Multiple expenses
        for i in range(5):
            transaction_service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=date.today(),
                    description=f"Meal {i + 1}",
                    amount=Decimal("20.00"),
                    from_account_id=cash.id,
                    to_account_id=food.id,
                    transaction_type=TransactionType.EXPENSE,
                ),
            )

        # 5 * $20 = $100 spent
        assert account_service.calculate_balance(cash.id) == Decimal("900.00")
        assert account_service.calculate_balance(food.id) == Decimal("100.00")


class TestTransactionEntryFeatures:
    """Integration tests for transaction entry with notes and expressions (Feature 004)."""

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
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        return ledger.id

    def test_create_transaction_with_notes(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Transaction can be created with notes field."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        tx = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Business lunch",
                amount=Decimal("150.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
                notes="Meeting with client at downtown restaurant",
            ),
        )

        # Verify notes is stored
        result = transaction_service.get_transaction(tx.id, ledger_id)
        assert result is not None
        assert result.notes == "Meeting with client at downtown restaurant"

    def test_create_transaction_with_amount_expression(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Transaction can store amount_expression for audit trail."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        tx = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Split bill",
                amount=Decimal("375.00"),  # Result of 1500/4
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
                amount_expression="1500/4",
            ),
        )

        # Verify expression is stored
        result = transaction_service.get_transaction(tx.id, ledger_id)
        assert result is not None
        assert result.amount_expression == "1500/4"
        assert result.amount == Decimal("375.00")

    def test_transaction_without_optional_fields(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Transaction can be created without notes and amount_expression."""
        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        tx = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Simple expense",
                amount=Decimal("50.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        result = transaction_service.get_transaction(tx.id, ledger_id)
        assert result is not None
        assert result.notes is None
        assert result.amount_expression is None

    def test_update_transaction_preserves_notes(
        self,
        transaction_service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
    ) -> None:
        """Updating transaction preserves notes field."""
        from src.schemas.transaction import TransactionUpdate

        accounts = account_service.get_accounts(ledger_id)
        cash = next(a for a in accounts if a.name == "Cash")

        food = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )

        # Create with notes
        tx = transaction_service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Lunch",
                amount=Decimal("50.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
                notes="Original note",
            ),
        )

        # Update amount but keep notes
        updated = transaction_service.update_transaction(
            tx.id,
            ledger_id,
            TransactionUpdate(
                date=date.today(),
                description="Lunch updated",
                amount=Decimal("75.00"),
                from_account_id=cash.id,
                to_account_id=food.id,
                transaction_type=TransactionType.EXPENSE,
                notes="Updated note",
            ),
        )

        assert updated is not None
        assert updated.notes == "Updated note"
        assert updated.amount == Decimal("75.00")
