import uuid
from datetime import date
from decimal import Decimal

from src.models.transaction import Transaction
from src.schemas.data_import import ParsedTransaction, TransactionType
from src.services.import_service import ImportService


class TestImportService:
    def test_find_duplicates_match(self):
        # Existing transaction
        acc_from = uuid.uuid4()
        acc_to = uuid.uuid4()

        existing_tx = Transaction(
            id=uuid.uuid4(),
            ledger_id=uuid.uuid4(),
            date=date(2024, 1, 1),
            amount=Decimal("100"),
            description="Lunch",
            from_account_id=acc_from,
            to_account_id=acc_to,
            owner_id=uuid.uuid4(),
        )

        # New transaction (ParsedTransaction) with same details
        new_tx = ParsedTransaction(
            row_number=1,
            date=date(2024, 1, 1),
            amount=Decimal("100.00"),
            description="Lunch with Bob",  # Note: description different but ignored
            transaction_type=TransactionType.EXPENSE,
            from_account_name="A-Cash",
            to_account_name="E-Food",
            from_account_id=acc_from,
            to_account_id=acc_to,
        )

        result = ImportService.find_duplicates([new_tx], [existing_tx])
        assert len(result) == 1
        assert result[0].row_number == 1
        assert str(existing_tx.id) in [str(id) for id in result[0].existing_transaction_ids]

    def test_find_duplicates_no_match_amount(self):
        acc_from = uuid.uuid4()
        acc_to = uuid.uuid4()

        existing_tx = Transaction(
            id=uuid.uuid4(),
            ledger_id=uuid.uuid4(),
            date=date(2024, 1, 1),
            amount=Decimal("100"),
            description="Lunch",
            from_account_id=acc_from,
            to_account_id=acc_to,
            owner_id=uuid.uuid4(),
        )

        new_tx = ParsedTransaction(
            row_number=1,
            date=date(2024, 1, 1),
            amount=Decimal("101.00"),  # Different amount
            description="Lunch",
            transaction_type=TransactionType.EXPENSE,
            from_account_name="A-Cash",
            to_account_name="E-Food",
            from_account_id=acc_from,
            to_account_id=acc_to,
        )

        result = ImportService.find_duplicates([new_tx], [existing_tx])
        assert len(result) == 0

    def test_find_duplicates_no_match_date(self):
        acc_from = uuid.uuid4()
        acc_to = uuid.uuid4()

        existing_tx = Transaction(
            id=uuid.uuid4(),
            ledger_id=uuid.uuid4(),
            date=date(2024, 1, 1),
            amount=Decimal("100"),
            description="Lunch",
            from_account_id=acc_from,
            to_account_id=acc_to,
            owner_id=uuid.uuid4(),
        )

        new_tx = ParsedTransaction(
            row_number=1,
            date=date(2024, 1, 2),  # Different date
            amount=Decimal("100"),
            description="Lunch",
            transaction_type=TransactionType.EXPENSE,
            from_account_name="A-Cash",
            to_account_name="E-Food",
            from_account_id=acc_from,
            to_account_id=acc_to,
        )

        result = ImportService.find_duplicates([new_tx], [existing_tx])
        assert len(result) == 0
