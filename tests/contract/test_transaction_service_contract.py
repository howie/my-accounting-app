from typing import List, Optional
import pytest
from unittest.mock import Mock, ANY
from src.myab.models.transaction import Transaction
from src.myab.models.account import Account

# Mock out the repository and validator dependencies
@pytest.fixture
def mock_transaction_repository():
    mock_repo = Mock()
    def mock_add_side_effect(transaction_obj: Transaction):
        if transaction_obj.id is None:
            transaction_obj.id = 1
        return transaction_obj
    mock_repo.add.side_effect = mock_add_side_effect
    return mock_repo

@pytest.fixture
def mock_account_repository():
    # Mock for retrieving accounts for validation or balance calculation
    mock_repo = Mock()
    mock_repo.get_by_id.side_effect = lambda acc_id: Account(id=acc_id, ledger_id=1, name="Mock Acc", type="ASSET")
    return mock_repo

@pytest.fixture
def mock_validator():
    mock_val = Mock()
    mock_val.validate_transaction.return_value = True
    return mock_val

# Placeholder for TransactionService - will be replaced by actual implementation
class TransactionService:
    def __init__(self, transaction_repository, account_repository, validator):
        self.transaction_repository = transaction_repository
        self.account_repository = account_repository
        self.validator = validator

    def create_transaction(self, ledger_id: int, date: str, type: str, amount: int,
                           debit_account_id: int, credit_account_id: int,
                           description: Optional[str] = None, invoice_number: Optional[str] = None) -> Optional[Transaction]:
        if not self.validator.validate_transaction(ledger_id, date, type, amount, debit_account_id, credit_account_id):
            return None # Return None if validation fails

        new_transaction = Transaction(
            ledger_id=ledger_id, date=date, type=type, amount=amount,
            debit_account_id=debit_account_id, credit_account_id=credit_account_id,
            description=description, invoice_number=invoice_number
        )
        return self.transaction_repository.add(new_transaction)

    def get_transaction(self, transaction_id: int) -> Optional[Transaction]:
        return self.transaction_repository.get_by_id(transaction_id)

    def update_transaction(self, transaction: Transaction) -> bool:
        return self.transaction_repository.update(transaction)

    def delete_transaction(self, transaction_id: int) -> bool:
        return self.transaction_repository.delete(transaction_id)

    def calculate_account_balance(self, account_id: int) -> int:
        # This would typically involve fetching all transactions for an account
        # and summing them up. For contract, just ensure it calls the repo/calculates.
        self.transaction_repository.get_transactions_for_account(account_id)
        return 1000 # Dummy balance

def test_create_transaction_contract(mock_transaction_repository, mock_account_repository, mock_validator):
    service = TransactionService(mock_transaction_repository, mock_account_repository, mock_validator)
    
    ledger_id = 1
    date = "2023-01-01"
    transaction_type = "EXPENSE"
    amount = 10000 # 100.00 in cents
    debit_account_id = 1
    credit_account_id = 2

    created_transaction = service.create_transaction(
        ledger_id, date, transaction_type, amount, debit_account_id, credit_account_id
    )

    assert created_transaction is not None
    assert created_transaction.ledger_id == ledger_id
    mock_validator.validate_transaction.assert_called_once()
    mock_transaction_repository.add.assert_called_once()

def test_create_transaction_validation_fail_contract(mock_transaction_repository, mock_account_repository, mock_validator):
    mock_validator.validate_transaction.return_value = False # Simulate validation failure
    service = TransactionService(mock_transaction_repository, mock_account_repository, mock_validator)

    created_transaction = service.create_transaction(1, "date", "type", 100, 1, 2)
    
    assert created_transaction is None
    mock_validator.validate_transaction.assert_called_once()
    mock_transaction_repository.add.assert_not_called()

def test_get_transaction_contract(mock_transaction_repository, mock_account_repository, mock_validator):
    service = TransactionService(mock_transaction_repository, mock_account_repository, mock_validator)
    transaction_id = 1
    mock_transaction_repository.get_by_id.return_value = Transaction(
        id=transaction_id, ledger_id=1, date="2023-01-01", type="EXPENSE", amount=10000, debit_account_id=1, credit_account_id=2
    )

    transaction = service.get_transaction(transaction_id)
    assert transaction is not None
    assert transaction.id == transaction_id
    mock_transaction_repository.get_by_id.assert_called_once_with(transaction_id)

def test_update_transaction_contract(mock_transaction_repository, mock_account_repository, mock_validator):
    service = TransactionService(mock_transaction_repository, mock_account_repository, mock_validator)
    transaction = Transaction(id=1, ledger_id=1, date="2023-01-01", type="EXPENSE", amount=10000, debit_account_id=1, credit_account_id=2)
    mock_transaction_repository.update.return_value = True

    result = service.update_transaction(transaction)
    assert result is True
    mock_transaction_repository.update.assert_called_once_with(transaction)

def test_delete_transaction_contract(mock_transaction_repository, mock_account_repository, mock_validator):
    service = TransactionService(mock_transaction_repository, mock_account_repository, mock_validator)
    transaction_id = 1
    mock_transaction_repository.delete.return_value = True

    result = service.delete_transaction(transaction_id)
    assert result is True
    mock_transaction_repository.delete.assert_called_once_with(transaction_id)

def test_calculate_account_balance_contract(mock_transaction_repository, mock_account_repository, mock_validator):
    service = TransactionService(mock_transaction_repository, mock_account_repository, mock_validator)
    account_id = 1

    balance = service.calculate_account_balance(account_id)
    assert balance == 1000 # As per dummy balance
    mock_transaction_repository.get_transactions_for_account.assert_called_once_with(account_id)
