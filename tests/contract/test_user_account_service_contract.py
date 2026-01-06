from typing import Optional
import pytest
from unittest.mock import Mock, ANY
from src.myab.models.user_account import UserAccount

# Mock out the repository dependencies
@pytest.fixture
def mock_user_account_repository():
    mock_repo = Mock()
    def mock_add_side_effect(user_account_obj: UserAccount):
        if user_account_obj.id is None:
            user_account_obj.id = 1
        return user_account_obj
    mock_repo.add.side_effect = mock_add_side_effect
    return mock_repo

# Placeholder for UserAccountService - will be replaced by actual implementation
class UserAccountService:
    def __init__(self, user_account_repository):
        self.user_account_repository = user_account_repository

    def create_user_account(self, username: str, password_hash: str) -> Optional[UserAccount]:
        new_user = UserAccount(username=username, password_hash=password_hash)
        return self.user_account_repository.add(new_user)

    def authenticate_user(self, username: str, password_hash: str) -> Optional[UserAccount]:
        user = self.user_account_repository.get_by_username(username)
        if user and user.password_hash == password_hash:
            return user
        return None

    def get_user_account_by_id(self, user_id: int) -> Optional[UserAccount]:
        return self.user_account_repository.get_by_id(user_id)

    def get_user_account_by_username(self, username: str) -> Optional[UserAccount]:
        return self.user_account_repository.get_by_username(username)

def test_create_user_account_contract(mock_user_account_repository):
    """Ensures create_user_account behaves as expected."""
    service = UserAccountService(mock_user_account_repository)
    username = "testuser"
    password_hash = "hashed_password"

    created_user = service.create_user_account(username, password_hash)

    assert created_user is not None
    assert created_user.username == username
    assert created_user.password_hash == password_hash
    mock_user_account_repository.add.assert_called_once()

def test_authenticate_user_contract_success(mock_user_account_repository):
    """Ensures authenticate_user works for valid credentials."""
    service = UserAccountService(mock_user_account_repository)
    username = "testuser"
    password_hash = "hashed_password"
    mock_user_account_repository.get_by_username.return_value = UserAccount(
        id=1, username=username, password_hash=password_hash
    )

    authenticated_user = service.authenticate_user(username, password_hash)
    assert authenticated_user is not None
    assert authenticated_user.username == username
    mock_user_account_repository.get_by_username.assert_called_once_with(username)

def test_authenticate_user_contract_fail_wrong_password(mock_user_account_repository):
    """Ensures authenticate_user fails for wrong password."""
    service = UserAccountService(mock_user_account_repository)
    username = "testuser"
    password_hash = "wrong_password"
    mock_user_account_repository.get_by_username.return_value = UserAccount(
        id=1, username=username, password_hash="correct_hash"
    )

    authenticated_user = service.authenticate_user(username, password_hash)
    assert authenticated_user is None
    mock_user_account_repository.get_by_username.assert_called_once_with(username)

def test_authenticate_user_contract_fail_user_not_found(mock_user_account_repository):
    """Ensures authenticate_user fails for non-existent user."""
    service = UserAccountService(mock_user_account_repository)
    username = "nonexistent"
    password_hash = "some_password"
    mock_user_account_repository.get_by_username.return_value = None

    authenticated_user = service.authenticate_user(username, password_hash)
    assert authenticated_user is None
    mock_user_account_repository.get_by_username.assert_called_once_with(username)

def test_get_user_account_by_id_contract(mock_user_account_repository):
    """Ensures get_user_account_by_id behaves as expected."""
    service = UserAccountService(mock_user_account_repository)
    user_id = 1
    mock_user_account_repository.get_by_id.return_value = UserAccount(
        id=user_id, username="someuser", password_hash="somehash"
    )

    user = service.get_user_account_by_id(user_id)
    assert user is not None
    assert user.id == user_id
    mock_user_account_repository.get_by_id.assert_called_once_with(user_id)
