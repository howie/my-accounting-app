import pytest
from myab.services.user_account_service import UserAccountService
from myab.persistence.repositories.user_account_repository import UserAccountRepository

def test_create_user(test_db):
    repo = UserAccountRepository(test_db.get_connection())
    service = UserAccountService(repo)
    user_id = service.create_user("testuser", "password123")
    assert isinstance(user_id, int)

def test_authenticate_user(test_db):
    repo = UserAccountRepository(test_db.get_connection())
    service = UserAccountService(repo)
    service.create_user("authuser", "password123")
    user = service.authenticate_user("authuser", "password123")
    assert user is not None
    assert user.username == "authuser"

def test_authenticate_failure(test_db):
    repo = UserAccountRepository(test_db.get_connection())
    service = UserAccountService(repo)
    user = service.authenticate_user("nonexistent", "pass")
    assert user is None