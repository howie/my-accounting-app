from typing import Optional, List
import pytest
from unittest.mock import Mock, ANY
from src.myab.models.account import Account

# Mock out the repository dependencies
@pytest.fixture
def mock_account_repository():
    mock_repo = Mock()
    # Configure the 'add' method of the mock to return an Account instance with an ID
    def mock_add_side_effect(account_obj: Account):
        # Assign a dummy ID for the returned object
        if account_obj.id is None:
            account_obj.id = 1
        return account_obj
    mock_repo.add.side_effect = mock_add_side_effect
    return mock_repo

# Placeholder for AccountService - will be replaced by actual implementation
class AccountService:
    def __init__(self, account_repository):
        self.account_repository = account_repository

    def create_account(self, ledger_id: int, name: str, type: str) -> Account:
        prefixed_name = f"{type[0].upper()}-{name}"
        new_account = Account(
            ledger_id=ledger_id, name=prefixed_name, type=type, is_predefined=0
        )
        # This will return the mock's return_value set in the test
        return self.account_repository.add(new_account)

    def create_initial_accounts(self, ledger_id: int, initial_cash_amount: float) -> List[Account]:
        cash_account = Account(
            ledger_id=ledger_id, name="A-Cash", type="ASSET", is_predefined=1
        )
        equity_account = Account(
            ledger_id=ledger_id, name="Equity", type="EQUITY", is_predefined=1
        )
        
        created_cash = self.account_repository.add(cash_account)
        created_equity = self.account_repository.add(equity_account)

        return [created_cash, created_equity]

    def list_accounts(self, ledger_id: int) -> List[Account]:
        return self.account_repository.get_by_ledger_id(ledger_id)

    def get_account(self, account_id: int) -> Optional[Account]:
        return self.account_repository.get_by_id(account_id)

    def update_account(self, account_id: int, new_name: Optional[str] = None, new_type: Optional[str] = None) -> bool:
        # Pass keyword arguments to the mock
        return self.account_repository.update(account_id=account_id, new_name=new_name, new_type=new_type)

    def delete_account(self, account_id: int) -> bool:
        account_to_delete = self.account_repository.get_by_id(account_id)
        if not account_to_delete:
            return False

        if account_to_delete.is_predefined:
            return False

        return self.account_repository.delete(account_id)

def test_create_account_contract(mock_account_repository):
    """Ensures create_account behaves as expected."""
    service = AccountService(mock_account_repository)
    ledger_id = 1
    name = "Bank Account"
    acc_type = "ASSET"

    created_account = service.create_account(ledger_id, name, acc_type)

    assert created_account is not None
    assert created_account.name == f"{acc_type[0].upper()}-{name}"
    assert created_account.type == acc_type
    assert created_account.ledger_id == ledger_id
    mock_account_repository.add.assert_called_once()

def test_create_initial_accounts_contract(mock_account_repository):
    """Ensures create_initial_accounts creates Cash and Equity accounts."""
    service = AccountService(mock_account_repository)
    ledger_id = 1
    initial_cash = 500.0

    initial_accounts = service.create_initial_accounts(ledger_id, initial_cash)

    assert len(initial_accounts) == 2
    assert any(acc.name == "A-Cash" and acc.type == "ASSET" for acc in initial_accounts)
    assert any(acc.name == "Equity" and acc.type == "EQUITY" for acc in initial_accounts)
    assert mock_account_repository.add.call_count == 2 # Called for Cash and Equity

def test_list_accounts_contract(mock_account_repository):
    """Ensures list_accounts calls repository and returns data."""
    service = AccountService(mock_account_repository)
    ledger_id = 1
    mock_account_repository.get_by_ledger_id.return_value = [
        Account(id=1, ledger_id=ledger_id, name="A-Cash", type="ASSET"),
        Account(id=2, ledger_id=ledger_id, name="E-Food", type="EXPENSE"),
    ]

    accounts = service.list_accounts(ledger_id)
    assert len(accounts) == 2
    mock_account_repository.get_by_ledger_id.assert_called_once_with(ledger_id)

def test_get_account_contract(mock_account_repository):
    """Ensures get_account calls repository and returns data."""
    service = AccountService(mock_account_repository)
    account_id = 1
    mock_account_repository.get_by_id.return_value = Account(
        id=account_id, ledger_id=1, name="A-Bank", type="ASSET"
    )

    account = service.get_account(account_id)
    assert account is not None
    assert account.id == account_id
    mock_account_repository.get_by_id.assert_called_once_with(account_id)

def test_update_account_contract(mock_account_repository):
    """Ensures update_account calls repository correctly."""
    service = AccountService(mock_account_repository)
    account_id = 1
    new_name = "New Bank Name"
    mock_account_repository.update.return_value = True

    result = service.update_account(account_id, new_name=new_name)
    assert result is True
    mock_account_repository.update.assert_called_once_with(account_id=account_id, new_name=new_name, new_type=None)

def test_delete_account_contract_success(mock_account_repository):
    """Ensures delete_account calls repository for non-predefined accounts."""
    service = AccountService(mock_account_repository)
    account_id = 3
    mock_account_repository.get_by_id.return_value = Account(
        id=account_id, ledger_id=1, name="E-Misc", type="EXPENSE", is_predefined=0
    )
    mock_account_repository.delete.return_value = True

    result = service.delete_account(account_id)
    assert result is True
    mock_account_repository.delete.assert_called_once_with(account_id)

def test_delete_account_contract_predefined_fail(mock_account_repository):
    """Ensures delete_account prevents deletion of predefined accounts."""
    service = AccountService(mock_account_repository)
    account_id = 1
    mock_account_repository.get_by_id.return_value = Account(
        id=account_id, ledger_id=1, name="A-Cash", type="ASSET", is_predefined=1
    )
    mock_account_repository.delete.return_value = False # Should not be called if predefined

    result = service.delete_account(account_id)
    assert result is False
    mock_account_repository.delete.assert_not_called()