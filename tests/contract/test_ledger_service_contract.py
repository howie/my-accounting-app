from typing import Optional, List
import pytest
from unittest.mock import Mock, ANY
from src.myab.models.ledger import Ledger
from src.myab.models.account import Account

# Mock out the repository and account service dependencies
@pytest.fixture
def mock_ledger_repository():
    mock_repo = Mock()
    # Configure the 'add' method of the mock to return a Ledger instance with an ID
    def mock_add_side_effect(ledger_obj: Ledger):
        if ledger_obj.id is None:
            ledger_obj.id = 1 # Assign a dummy ID
        return ledger_obj
    mock_repo.add.side_effect = mock_add_side_effect
    return mock_repo

@pytest.fixture
def mock_account_repository():
    return Mock()

@pytest.fixture
def mock_account_service(mock_account_repository):
    # Mocking AccountService to avoid circular dependencies and focus on LedgerService
    mock_service = Mock()
    mock_service.create_initial_accounts.return_value = ([
        Account(id=1, ledger_id=ANY, name='A-Cash', type='ASSET', is_predefined=1),
        Account(id=2, ledger_id=ANY, name='Equity', type='EQUITY', is_predefined=1)
    ])
    return mock_service

# Placeholder for LedgerService - will be replaced by actual implementation
class LedgerService:
    def __init__(self, ledger_repository, account_service):
        self.ledger_repository = ledger_repository
        self.account_service = account_service

    def create_ledger(self, user_account_id: int, name: str, initial_cash: float) -> Ledger:
        new_ledger_obj = Ledger(user_account_id=user_account_id, name=name, creation_date=ANY) # creation_date can be ANY
        created_ledger_from_repo = self.ledger_repository.add(new_ledger_obj) # This will return the mock's return_value

        self.account_service.create_initial_accounts(created_ledger_from_repo.id, initial_cash)

        return created_ledger_from_repo

    def list_ledgers(self, user_account_id: int) -> List[Ledger]:
        return self.ledger_repository.get_by_user_account_id(user_account_id)

    def get_ledger(self, ledger_id: int) -> Optional[Ledger]:
        return self.ledger_repository.get_by_id(ledger_id)

    def delete_ledger(self, ledger_id: int) -> bool:
        return self.ledger_repository.delete(ledger_id)


def test_create_ledger_contract(mock_ledger_repository, mock_account_service):
    """
    Contract test for LedgerService.create_ledger.
    Ensures the method calls the repository and account service correctly.
    """
    service = LedgerService(mock_ledger_repository, mock_account_service)
    user_id = 1
    ledger_name = "Test Ledger"
    initial_cash = 1000.0

    # Ensure repository.add is called with correct parameters
    # The Ledger model's creation_date is set within the model, so we don't assert it here
    mock_ledger_repository.add.return_value = Ledger(
        id=1,
        user_account_id=user_id,
        name=ledger_name,
        creation_date="2023-01-01T00:00:00" # Dummy date for mock return
    )

    created_ledger = service.create_ledger(user_id, ledger_name, initial_cash)

    assert created_ledger is not None
    assert created_ledger.name == ledger_name
    assert created_ledger.user_account_id == user_id
    mock_ledger_repository.add.assert_called_once()
    mock_account_service.create_initial_accounts.assert_called_once_with(
        created_ledger.id, initial_cash
    )

def test_list_ledgers_contract(mock_ledger_repository, mock_account_service):
    """
    Contract test for LedgerService.list_ledgers.
    Ensures the method calls the repository correctly and returns data.
    """
    service = LedgerService(mock_ledger_repository, mock_account_service)
    user_id = 1
    mock_ledger_repository.get_by_user_account_id.return_value = [
        Ledger(id=1, user_account_id=user_id, name="Ledger 1", creation_date=ANY),
        Ledger(id=2, user_account_id=user_id, name="Ledger 2", creation_date=ANY),
    ]

    ledgers = service.list_ledgers(user_id)
    assert len(ledgers) == 2
    mock_ledger_repository.get_by_user_account_id.assert_called_once_with(user_id)

def test_get_ledger_contract(mock_ledger_repository, mock_account_service):
    """
    Contract test for LedgerService.get_ledger.
    Ensures the method calls the repository correctly and returns data.
    """
    service = LedgerService(mock_ledger_repository, mock_account_service)
    ledger_id = 1
    mock_ledger_repository.get_by_id.return_value = Ledger(
        id=ledger_id, user_account_id=1, name="Single Ledger", creation_date=ANY
    )

    ledger = service.get_ledger(ledger_id)
    assert ledger is not None
    assert ledger.id == ledger_id
    mock_ledger_repository.get_by_id.assert_called_once_with(ledger_id)

def test_delete_ledger_contract(mock_ledger_repository, mock_account_service):
    """
    Contract test for LedgerService.delete_ledger.
    Ensures the method calls the repository correctly and returns a boolean.
    """
    service = LedgerService(mock_ledger_repository, mock_account_service)
    ledger_id = 1
    mock_ledger_repository.delete.return_value = True

    result = service.delete_ledger(ledger_id)
    assert result is True
    mock_ledger_repository.delete.assert_called_once_with(ledger_id)