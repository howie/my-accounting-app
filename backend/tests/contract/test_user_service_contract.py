"""Contract tests for UserService.

Tests the UserService contract as defined in contracts/user_account_service.md.
These tests verify the service behaves according to the documented contract.
"""

import uuid

import pytest
from sqlmodel import Session

from src.models.user import User, UserSetup
from src.services.user_account_service import UserService


class TestUserServiceContract:
    """Contract tests for UserService."""

    @pytest.fixture
    def service(self, session: Session) -> UserService:
        """Create UserService instance."""
        return UserService(session)

    # --- get_current_user ---

    def test_get_current_user_returns_none_when_no_user(
        self, service: UserService
    ) -> None:
        """get_current_user returns None when no user exists."""
        result = service.get_current_user()
        assert result is None

    def test_get_current_user_returns_user_when_exists(
        self, service: UserService, session: Session
    ) -> None:
        """get_current_user returns the user when one exists."""
        # Create a user first
        user = User(email="test@example.com")
        session.add(user)
        session.commit()

        result = service.get_current_user()

        assert result is not None
        assert result.email == "test@example.com"

    # --- setup_user ---

    def test_setup_user_creates_user(self, service: UserService) -> None:
        """setup_user creates a new user with the given email."""
        data = UserSetup(email="newuser@example.com")

        result = service.setup_user(data)

        assert result is not None
        assert result.email == "newuser@example.com"
        assert result.id is not None

    def test_setup_user_returns_user_with_uuid_id(self, service: UserService) -> None:
        """setup_user returns a user with a valid UUID id."""
        data = UserSetup(email="test@example.com")

        result = service.setup_user(data)

        # Should not raise
        uuid.UUID(str(result.id))

    def test_setup_user_returns_user_with_created_at(
        self, service: UserService
    ) -> None:
        """setup_user returns a user with created_at timestamp."""
        data = UserSetup(email="test@example.com")

        result = service.setup_user(data)

        assert result.created_at is not None

    def test_setup_user_raises_if_user_exists(
        self, service: UserService, session: Session
    ) -> None:
        """setup_user raises ValueError if a user already exists (single-user mode)."""
        # Create existing user
        existing = User(email="existing@example.com")
        session.add(existing)
        session.commit()

        data = UserSetup(email="newuser@example.com")

        with pytest.raises(ValueError, match="already exists"):
            service.setup_user(data)

    def test_setup_user_persists_user(
        self, service: UserService, session: Session
    ) -> None:
        """setup_user persists the user to the database."""
        data = UserSetup(email="persist@example.com")

        result = service.setup_user(data)

        # Query directly to verify persistence
        from_db = session.get(User, result.id)
        assert from_db is not None
        assert from_db.email == "persist@example.com"

    # --- get_or_create_default_user ---

    def test_get_or_create_default_user_creates_when_none(
        self, service: UserService
    ) -> None:
        """get_or_create_default_user creates a default user if none exists."""
        result = service.get_or_create_default_user()

        assert result is not None
        assert result.email == "user@localhost"

    def test_get_or_create_default_user_returns_existing(
        self, service: UserService, session: Session
    ) -> None:
        """get_or_create_default_user returns existing user if one exists."""
        # Create existing user
        existing = User(email="existing@example.com")
        session.add(existing)
        session.commit()
        existing_id = existing.id

        result = service.get_or_create_default_user()

        assert result.id == existing_id
        assert result.email == "existing@example.com"

    def test_get_or_create_default_user_idempotent(
        self, service: UserService
    ) -> None:
        """get_or_create_default_user is idempotent - multiple calls return same user."""
        result1 = service.get_or_create_default_user()
        result2 = service.get_or_create_default_user()

        assert result1.id == result2.id
