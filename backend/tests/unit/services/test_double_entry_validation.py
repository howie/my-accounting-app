"""Tests for double-entry bookkeeping validation.

Ensures that all transactions maintain accounting integrity with
proper debit/credit relationships between account types.
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


class TestDoubleEntryValidation:
    """Tests for double-entry bookkeeping rules."""

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
    def bank_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Bank", type=AccountType.ASSET)
        )
        return account.id

    @pytest.fixture
    def credit_card_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Credit Card", type=AccountType.LIABILITY)
        )
        return account.id

    @pytest.fixture
    def salary_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Salary", type=AccountType.INCOME)
        )
        return account.id

    @pytest.fixture
    def rent_id(
        self, account_service: AccountService, ledger_id: uuid.UUID
    ) -> uuid.UUID:
        account = account_service.create_account(
            ledger_id, AccountCreate(name="Rent", type=AccountType.EXPENSE)
        )
        return account.id

    # --- EXPENSE transaction type rules ---

    def test_expense_asset_to_expense_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        rent_id: uuid.UUID,
    ) -> None:
        """EXPENSE: Asset → Expense is valid (paying with cash)."""
        data = TransactionCreate(
            date=date.today(),
            description="Pay rent with cash",
            amount=Decimal("1000.00"),
            from_account_id=cash_id,
            to_account_id=rent_id,
            transaction_type=TransactionType.EXPENSE,
        )
        result = service.create_transaction(ledger_id, data)
        assert result is not None

    def test_expense_liability_to_expense_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        credit_card_id: uuid.UUID,
        rent_id: uuid.UUID,
    ) -> None:
        """EXPENSE: Liability → Expense is valid (paying with credit card)."""
        data = TransactionCreate(
            date=date.today(),
            description="Pay rent with credit card",
            amount=Decimal("1000.00"),
            from_account_id=credit_card_id,
            to_account_id=rent_id,
            transaction_type=TransactionType.EXPENSE,
        )
        result = service.create_transaction(ledger_id, data)
        assert result is not None

    # --- INCOME transaction type rules ---

    def test_income_income_to_asset_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        salary_id: uuid.UUID,
        cash_id: uuid.UUID,
    ) -> None:
        """INCOME: Income → Asset is valid (receiving salary in cash)."""
        data = TransactionCreate(
            date=date.today(),
            description="Receive salary",
            amount=Decimal("5000.00"),
            from_account_id=salary_id,
            to_account_id=cash_id,
            transaction_type=TransactionType.INCOME,
        )
        result = service.create_transaction(ledger_id, data)
        assert result is not None

    def test_income_income_to_liability_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        salary_id: uuid.UUID,
        credit_card_id: uuid.UUID,
    ) -> None:
        """INCOME: Income → Liability is valid (paying off credit card with income)."""
        data = TransactionCreate(
            date=date.today(),
            description="Pay off credit card",
            amount=Decimal("500.00"),
            from_account_id=salary_id,
            to_account_id=credit_card_id,
            transaction_type=TransactionType.INCOME,
        )
        result = service.create_transaction(ledger_id, data)
        assert result is not None

    # --- TRANSFER transaction type rules ---

    def test_transfer_asset_to_asset_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        bank_id: uuid.UUID,
    ) -> None:
        """TRANSFER: Asset → Asset is valid (deposit cash to bank)."""
        data = TransactionCreate(
            date=date.today(),
            description="Deposit to bank",
            amount=Decimal("500.00"),
            from_account_id=cash_id,
            to_account_id=bank_id,
            transaction_type=TransactionType.TRANSFER,
        )
        result = service.create_transaction(ledger_id, data)
        assert result is not None

    def test_transfer_asset_to_liability_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        credit_card_id: uuid.UUID,
    ) -> None:
        """TRANSFER: Asset → Liability is valid (pay credit card with cash)."""
        data = TransactionCreate(
            date=date.today(),
            description="Pay credit card",
            amount=Decimal("200.00"),
            from_account_id=cash_id,
            to_account_id=credit_card_id,
            transaction_type=TransactionType.TRANSFER,
        )
        result = service.create_transaction(ledger_id, data)
        assert result is not None

    def test_transfer_liability_to_asset_valid(
        self,
        service: TransactionService,
        ledger_id: uuid.UUID,
        credit_card_id: uuid.UUID,
        cash_id: uuid.UUID,
    ) -> None:
        """TRANSFER: Liability → Asset is valid (cash advance from credit card)."""
        data = TransactionCreate(
            date=date.today(),
            description="Cash advance",
            amount=Decimal("100.00"),
            from_account_id=credit_card_id,
            to_account_id=cash_id,
            transaction_type=TransactionType.TRANSFER,
        )
        result = service.create_transaction(ledger_id, data)
        assert result is not None

    def test_transfer_liability_to_liability_valid(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        credit_card_id: uuid.UUID,
    ) -> None:
        """TRANSFER: Liability → Liability is valid (balance transfer)."""
        other_card = account_service.create_account(
            ledger_id, AccountCreate(name="Other Card", type=AccountType.LIABILITY)
        )

        data = TransactionCreate(
            date=date.today(),
            description="Balance transfer",
            amount=Decimal("300.00"),
            from_account_id=credit_card_id,
            to_account_id=other_card.id,
            transaction_type=TransactionType.TRANSFER,
        )
        result = service.create_transaction(ledger_id, data)
        assert result is not None

    # --- Balance calculation after transactions ---

    def test_expense_decreases_asset_increases_expense(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        rent_id: uuid.UUID,
    ) -> None:
        """EXPENSE: decreases Asset balance, increases Expense balance."""
        initial_cash = account_service.calculate_balance(cash_id)
        initial_rent = account_service.calculate_balance(rent_id)

        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Pay rent",
                amount=Decimal("500.00"),
                from_account_id=cash_id,
                to_account_id=rent_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        assert account_service.calculate_balance(cash_id) == initial_cash - Decimal("500.00")
        assert account_service.calculate_balance(rent_id) == initial_rent + Decimal("500.00")

    def test_income_increases_asset_increases_income(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        salary_id: uuid.UUID,
    ) -> None:
        """INCOME: increases Asset balance, increases Income balance."""
        initial_cash = account_service.calculate_balance(cash_id)
        initial_salary = account_service.calculate_balance(salary_id)

        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Receive salary",
                amount=Decimal("3000.00"),
                from_account_id=salary_id,
                to_account_id=cash_id,
                transaction_type=TransactionType.INCOME,
            ),
        )

        assert account_service.calculate_balance(cash_id) == initial_cash + Decimal("3000.00")
        assert account_service.calculate_balance(salary_id) == initial_salary + Decimal("3000.00")

    def test_transfer_decreases_source_increases_destination(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        bank_id: uuid.UUID,
    ) -> None:
        """TRANSFER: decreases source Asset, increases destination Asset."""
        initial_cash = account_service.calculate_balance(cash_id)
        initial_bank = account_service.calculate_balance(bank_id)

        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Deposit",
                amount=Decimal("200.00"),
                from_account_id=cash_id,
                to_account_id=bank_id,
                transaction_type=TransactionType.TRANSFER,
            ),
        )

        assert account_service.calculate_balance(cash_id) == initial_cash - Decimal("200.00")
        assert account_service.calculate_balance(bank_id) == initial_bank + Decimal("200.00")

    def test_expense_from_liability_increases_liability(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        credit_card_id: uuid.UUID,
        rent_id: uuid.UUID,
    ) -> None:
        """EXPENSE from Liability: increases Liability balance (you owe more)."""
        initial_card = account_service.calculate_balance(credit_card_id)
        initial_rent = account_service.calculate_balance(rent_id)

        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Pay rent with card",
                amount=Decimal("1000.00"),
                from_account_id=credit_card_id,
                to_account_id=rent_id,
                transaction_type=TransactionType.EXPENSE,
            ),
        )

        # Liability increases when you spend on credit
        assert account_service.calculate_balance(credit_card_id) == initial_card + Decimal("1000.00")
        assert account_service.calculate_balance(rent_id) == initial_rent + Decimal("1000.00")

    def test_transfer_to_liability_decreases_liability(
        self,
        service: TransactionService,
        account_service: AccountService,
        ledger_id: uuid.UUID,
        cash_id: uuid.UUID,
        credit_card_id: uuid.UUID,
    ) -> None:
        """TRANSFER Asset → Liability: decreases Liability (paying off debt)."""
        # First incur some debt
        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Initial debt",
                amount=Decimal("500.00"),
                from_account_id=credit_card_id,
                to_account_id=cash_id,
                transaction_type=TransactionType.TRANSFER,
            ),
        )

        card_balance = account_service.calculate_balance(credit_card_id)
        assert card_balance == Decimal("500.00")  # Liability is positive

        # Now pay it off
        service.create_transaction(
            ledger_id,
            TransactionCreate(
                date=date.today(),
                description="Pay off card",
                amount=Decimal("300.00"),
                from_account_id=cash_id,
                to_account_id=credit_card_id,
                transaction_type=TransactionType.TRANSFER,
            ),
        )

        # Liability decreases when you pay
        assert account_service.calculate_balance(credit_card_id) == Decimal("200.00")
