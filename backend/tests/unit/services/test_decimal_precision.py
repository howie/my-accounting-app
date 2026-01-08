"""Tests for decimal precision and banker's rounding.

Ensures proper handling of monetary amounts with correct precision
and banker's rounding (round half to even) for financial calculations.
"""

import uuid
from datetime import date
from decimal import ROUND_HALF_EVEN, Decimal

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


class TestDecimalPrecision:
    """Tests for decimal precision in monetary amounts."""

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
            user_id, LedgerCreate(name="Test", initial_balance=Decimal("1000.00"))
        )
        return ledger.id

    @pytest.fixture
    def cash_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        accounts = account_service.get_accounts(ledger_id)
        return next(a.id for a in accounts if a.name == "Cash")

    @pytest.fixture
    def food_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Food", type=AccountType.EXPENSE)
        )
        return account.id

    # --- Decimal precision storage ---

    def test_amount_stored_with_two_decimal_places(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Amount is stored with exactly two decimal places."""
        data = TransactionCreate(
            date=date.today(),
            description="Precise amount",
            amount=Decimal("12.34"),
            from_account_id=cash_id,
            to_account_id=food_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)
        assert result.amount == Decimal("12.34")

    def test_amount_preserves_trailing_zeros(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Amount preserves trailing zeros (12.00 not 12)."""
        data = TransactionCreate(
            date=date.today(),
            description="Round amount",
            amount=Decimal("12.00"),
            from_account_id=cash_id,
            to_account_id=food_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)
        assert result.amount == Decimal("12.00")

    def test_amount_single_decimal_stored_correctly(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Amount with single decimal is stored correctly (12.5 → 12.50)."""
        data = TransactionCreate(
            date=date.today(),
            description="Single decimal",
            amount=Decimal("12.5"),
            from_account_id=cash_id,
            to_account_id=food_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)
        # Should be equivalent to 12.50
        assert result.amount == Decimal("12.50")

    # --- Balance calculations with precision ---

    def test_balance_accumulates_precisely(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Multiple small amounts accumulate without floating point errors."""
        # Create 10 transactions of $0.10 each
        for i in range(10):
            service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=date.today(),
                    description=f"Small amount {i+1}",
                    amount=Decimal("0.10"),
                    from_account_id=cash_id,
                    to_account_id=food_id,
                    transaction_type=TransactionType.EXPENSE,
                ),
            )

        # Should be exactly $1.00, not 0.99999... or 1.00000001
        balance = account_service.calculate_balance(food_id)
        assert balance == Decimal("1.00")

    def test_balance_with_cents(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Balance calculation handles cents correctly."""
        amounts = [
            Decimal("10.99"),
            Decimal("5.01"),
            Decimal("3.50"),
        ]

        for i, amount in enumerate(amounts):
            service.create_transaction(
                ledger_id,
                TransactionCreate(
                    date=date.today(),
                    description=f"Amount {i+1}",
                    amount=amount,
                    from_account_id=cash_id,
                    to_account_id=food_id,
                    transaction_type=TransactionType.EXPENSE,
                ),
            )

        # 10.99 + 5.01 + 3.50 = 19.50
        balance = account_service.calculate_balance(food_id)
        assert balance == Decimal("19.50")

    # --- Banker's rounding tests ---

    def test_bankers_rounding_half_to_even_down(self) -> None:
        """Banker's rounding: 2.225 → 2.22 (half rounds to even, down)."""
        value = Decimal("2.225")
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        assert rounded == Decimal("2.22")

    def test_bankers_rounding_half_to_even_up(self) -> None:
        """Banker's rounding: 2.235 → 2.24 (half rounds to even, up)."""
        value = Decimal("2.235")
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        assert rounded == Decimal("2.24")

    def test_bankers_rounding_standard_up(self) -> None:
        """Banker's rounding: 2.236 → 2.24 (standard round up)."""
        value = Decimal("2.236")
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        assert rounded == Decimal("2.24")

    def test_bankers_rounding_standard_down(self) -> None:
        """Banker's rounding: 2.234 → 2.23 (standard round down)."""
        value = Decimal("2.234")
        rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
        assert rounded == Decimal("2.23")

    # --- Large amount precision ---

    def test_large_amount_precision(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Large amounts maintain precision."""
        data = TransactionCreate(
            date=date.today(),
            description="Large amount",
            amount=Decimal("123456789.99"),
            from_account_id=cash_id,
            to_account_id=food_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)
        assert result.amount == Decimal("123456789.99")

    def test_large_balance_calculation(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Balance calculation works with large amounts."""
        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Large 1",
                amount=Decimal("999999999.99"),
                from_account_id=cash_id,
                to_account_id=food_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )
        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Large 2",
                amount=Decimal("0.01"),
                from_account_id=cash_id,
                to_account_id=food_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        balance = account_service.calculate_balance(food_id)
        assert balance == Decimal("1000000000.00")

    # --- Edge cases ---

    def test_minimum_cent_transaction(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Minimum valid transaction is one cent."""
        data = TransactionCreate(
            date=date.today(),
            description="One cent",
            amount=Decimal("0.01"),
            from_account_id=cash_id,
            to_account_id=food_id,
            transaction_type=TransactionType.EXPENSE,
        )

        result = service.create_transaction(ledger_id, data)
        assert result.amount == Decimal("0.01")

    def test_fractional_cents_rejected(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        food_id: uuid.UUID,
    ) -> None:
        """Amounts with more than 2 decimal places are rejected by schema validation."""
        from pydantic import ValidationError

        # Pydantic schema rejects amounts with more than 2 decimal places
        with pytest.raises(ValidationError):
            TransactionCreate(
                date=date.today(),
                description="Fractional cents",
                amount=Decimal("10.999"),
                from_account_id=cash_id,
                to_account_id=food_id,
                transaction_type=TransactionType.EXPENSE,
            )
