import pytest
from unittest.mock import Mock, ANY
from src.myab.models.account import Account
from src.myab.models.transaction import Transaction

# Placeholder for TransactionValidator
class TransactionValidator:
    def __init__(self, account_repository):
        self.account_repository = account_repository

    def validate_transaction(self, ledger_id: int, date: str, type: str, amount: int,
                             debit_account_id: int, credit_account_id: int) -> bool:
        
        # Unbalanced transaction (FR-006): This validation assumes a context of debits and credits
        # that would need to balance. For now, we'll focus on the simple rules.
        if amount <= 0: # Zero amount check from spec clarification
            return False # Will be changed to allow with warning, but for unit test, block for now

        if debit_account_id == credit_account_id: # Transfer between same accounts
            return False

        # Mock account retrieval for type checking (FR-006)
        debit_account = self.account_repository.get_by_id(debit_account_id)
        credit_account = self.account_repository.get_by_id(credit_account_id)

        if not debit_account or not credit_account:
            return False # Accounts must exist
        
        # FR-006: Transaction rules
        if type == "EXPENSE":
            if not (debit_account.type == "EXPENSE" and credit_account.type in ["ASSET", "LIABILITY"]):
                return False
        elif type == "INCOME":
            if not (debit_account.type in ["ASSET", "LIABILITY"] and credit_account.type == "INCOME"):
                return False
        elif type == "TRANSFER":
            if not (debit_account.type in ["ASSET", "LIABILITY"] and credit_account.type in ["ASSET", "LIABILITY"]):
                return False
        else:
            return False # Unknown transaction type

        return True

@pytest.fixture
def mock_account_repository():
    mock_repo = Mock()
    mock_repo.get_by_id.side_effect = lambda acc_id: Account(id=acc_id, ledger_id=1, name="Acc Name", type="ASSET")
    return mock_repo

def test_zero_amount_transaction_blocked_by_default(mock_account_repository):
    """
    Test that a zero-amount transaction is blocked by default validation.
    As per spec clarification, it will later be allowed with a warning,
    but the core validation should initially block it.
    """
    validator = TransactionValidator(mock_account_repository)
    result = validator.validate_transaction(1, "2023-01-01", "EXPENSE", 0, 1, 2)
    assert result is False

def test_negative_amount_transaction_blocked_by_default(mock_account_repository):
    """
    Test that a negative-amount transaction is blocked by default validation.
    As per spec, negative amounts are for special cases like refunds (FR-013),
    but the core validation should handle them carefully.
    """
    validator = TransactionValidator(mock_account_repository)
    result = validator.validate_transaction(1, "2023-01-01", "EXPENSE", -100, 1, 2)
    assert result is False

def test_transfer_to_same_account_blocked(mock_account_repository):
    """Test that transferring funds to the same account is blocked."""
    validator = TransactionValidator(mock_account_repository)
    result = validator.validate_transaction(1, "2023-01-01", "TRANSFER", 100, 1, 1)
    assert result is False

def test_expense_transaction_rules_valid(mock_account_repository):
    """Test valid expense transaction rules."""
    validator = TransactionValidator(mock_account_repository)
    mock_account_repository.get_by_id.side_effect = lambda acc_id: {
        1: Account(id=1, ledger_id=1, name="E-Food", type="EXPENSE"),
        2: Account(id=2, ledger_id=1, name="A-Cash", type="ASSET")
    }.get(acc_id)
    result = validator.validate_transaction(1, "2023-01-01", "EXPENSE", 100, 1, 2)
    assert result is True

def test_expense_transaction_rules_invalid(mock_account_repository):
    """Test invalid expense transaction rules (e.g., Asset to Asset)."""
    validator = TransactionValidator(mock_account_repository)
    mock_account_repository.get_by_id.side_effect = lambda acc_id: {
        1: Account(id=1, ledger_id=1, name="A-Bank", type="ASSET"),
        2: Account(id=2, ledger_id=1, name="A-Cash", type="ASSET")
    }.get(acc_id)
    result = validator.validate_transaction(1, "2023-01-01", "EXPENSE", 100, 1, 2)
    assert result is False

def test_income_transaction_rules_valid(mock_account_repository):
    """Test valid income transaction rules."""
    validator = TransactionValidator(mock_account_repository)
    mock_account_repository.get_by_id.side_effect = lambda acc_id: {
        1: Account(id=1, ledger_id=1, name="A-Cash", type="ASSET"),
        2: Account(id=2, ledger_id=1, name="I-Salary", type="INCOME")
    }.get(acc_id)
    result = validator.validate_transaction(1, "2023-01-01", "INCOME", 100, 1, 2)
    assert result is True

def test_income_transaction_rules_invalid(mock_account_repository):
    """Test invalid income transaction rules (e.g., Income to Expense)."""
    validator = TransactionValidator(mock_account_repository)
    mock_account_repository.get_by_id.side_effect = lambda acc_id: {
        1: Account(id=1, ledger_id=1, name="I-Salary", type="INCOME"),
        2: Account(id=2, ledger_id=1, name="E-Food", type="EXPENSE")
    }.get(acc_id)
    result = validator.validate_transaction(1, "2023-01-01", "INCOME", 100, 1, 2)
    assert result is False

def test_transfer_transaction_rules_valid(mock_account_repository):
    """Test valid transfer transaction rules (Asset to Asset)."""
    validator = TransactionValidator(mock_account_repository)
    mock_account_repository.get_by_id.side_effect = lambda acc_id: {
        1: Account(id=1, ledger_id=1, name="A-Cash", type="ASSET"),
        2: Account(id=2, ledger_id=1, name="A-Bank", type="ASSET")
    }.get(acc_id)
    result = validator.validate_transaction(1, "2023-01-01", "TRANSFER", 100, 1, 2)
    assert result is True

def test_transfer_transaction_rules_invalid(mock_account_repository):
    """Test invalid transfer transaction rules (Asset to Income)."""
    validator = TransactionValidator(mock_account_repository)
    mock_account_repository.get_by_id.side_effect = lambda acc_id: {
        1: Account(id=1, ledger_id=1, name="A-Cash", type="ASSET"),
        2: Account(id=2, ledger_id=1, name="I-Salary", type="INCOME")
    }.get(acc_id)
    result = validator.validate_transaction(1, "2023-01-01", "TRANSFER", 100, 1, 2)
    assert result is False
