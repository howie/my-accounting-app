"""Unit tests for ApiTokenService.

Tests token creation, validation, revocation, and listing.
"""

import uuid

import pytest
from sqlmodel import Session

from src.models.user import User
from src.services.api_token_service import ApiTokenService


class TestApiTokenServiceCreate:
    """Test ApiTokenService.create_token method."""

    def test_create_token_returns_raw_token_once(self, session: Session):
        """Create token should return the raw token only once."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Claude Desktop")

        assert result.raw_token is not None
        assert result.raw_token.startswith("ldo_")
        assert len(result.raw_token) == 52  # ldo_ + 48 chars
        assert result.token.name == "Claude Desktop"

    def test_create_token_stores_hash_not_raw(self, session: Session):
        """Created token should store hash, not raw token."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Claude Desktop")

        # Raw token should not be in the hash
        assert result.raw_token not in result.token.token_hash
        # Hash should be 64 hex chars (SHA-256)
        assert len(result.token.token_hash) == 64

    def test_create_token_stores_prefix(self, session: Session):
        """Created token should store display prefix."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Claude Desktop")

        # Prefix should be first 8 chars of raw token
        assert result.token.token_prefix == result.raw_token[:8]

    def test_create_token_associates_with_user(self, session: Session):
        """Created token should be associated with the user."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Claude Desktop")

        assert result.token.user_id == user.id


class TestApiTokenServiceValidate:
    """Test ApiTokenService.validate_token method."""

    def test_validate_valid_token_returns_token(self, session: Session):
        """Validating a valid token should return the token."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Claude Desktop")

        validated = service.validate_token(result.raw_token)
        assert validated is not None
        assert validated.id == result.token.id

    def test_validate_invalid_token_returns_none(self, session: Session):
        """Validating an invalid token should return None."""
        service = ApiTokenService(session)

        validated = service.validate_token("ldo_invalid_token_that_does_not_exist")
        assert validated is None

    def test_validate_revoked_token_returns_none(self, session: Session):
        """Validating a revoked token should return None."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Claude Desktop")

        # Revoke the token
        service.revoke_token(result.token.id, user.id)

        validated = service.validate_token(result.raw_token)
        assert validated is None

    def test_validate_updates_last_used(self, session: Session):
        """Validating a token should update last_used_at."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Claude Desktop")

        assert result.token.last_used_at is None

        validated = service.validate_token(result.raw_token)
        session.refresh(validated)

        assert validated.last_used_at is not None


class TestApiTokenServiceRevoke:
    """Test ApiTokenService.revoke_token method."""

    def test_revoke_token_sets_revoked_at(self, session: Session):
        """Revoking a token should set revoked_at."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Claude Desktop")

        revoked = service.revoke_token(result.token.id, user.id)

        assert revoked is True
        session.refresh(result.token)
        assert result.token.revoked_at is not None

    def test_revoke_nonexistent_token_returns_false(self, session: Session):
        """Revoking a nonexistent token should return False."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)

        revoked = service.revoke_token(uuid.uuid4(), user.id)
        assert revoked is False

    def test_revoke_other_users_token_returns_false(self, session: Session):
        """Revoking another user's token should return False."""
        user1 = User(email="user1@example.com", display_name="User 1")
        user2 = User(email="user2@example.com", display_name="User 2")
        session.add(user1)
        session.add(user2)
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        service = ApiTokenService(session)
        result = service.create_token(user1.id, "Claude Desktop")

        # User 2 tries to revoke User 1's token
        revoked = service.revoke_token(result.token.id, user2.id)
        assert revoked is False


class TestApiTokenServiceList:
    """Test ApiTokenService.list_tokens method."""

    def test_list_tokens_returns_user_tokens(self, session: Session):
        """List tokens should return only the user's tokens."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        service.create_token(user.id, "Token 1")
        service.create_token(user.id, "Token 2")

        tokens = service.list_tokens(user.id)

        assert len(tokens) == 2
        assert {t.name for t in tokens} == {"Token 1", "Token 2"}

    def test_list_tokens_excludes_revoked(self, session: Session):
        """List tokens should exclude revoked tokens by default."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result1 = service.create_token(user.id, "Token 1")
        service.create_token(user.id, "Token 2")

        service.revoke_token(result1.token.id, user.id)

        tokens = service.list_tokens(user.id)

        assert len(tokens) == 1
        assert tokens[0].name == "Token 2"

    def test_list_tokens_includes_revoked_when_requested(self, session: Session):
        """List tokens should include revoked tokens when requested."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result1 = service.create_token(user.id, "Token 1")
        service.create_token(user.id, "Token 2")

        service.revoke_token(result1.token.id, user.id)

        tokens = service.list_tokens(user.id, include_revoked=True)

        assert len(tokens) == 2

    def test_list_tokens_does_not_return_other_users_tokens(self, session: Session):
        """List tokens should not return other users' tokens."""
        user1 = User(email="user1@example.com", display_name="User 1")
        user2 = User(email="user2@example.com", display_name="User 2")
        session.add(user1)
        session.add(user2)
        session.commit()
        session.refresh(user1)
        session.refresh(user2)

        service = ApiTokenService(session)
        service.create_token(user1.id, "User 1 Token")
        service.create_token(user2.id, "User 2 Token")

        tokens1 = service.list_tokens(user1.id)
        tokens2 = service.list_tokens(user2.id)

        assert len(tokens1) == 1
        assert tokens1[0].name == "User 1 Token"
        assert len(tokens2) == 1
        assert tokens2[0].name == "User 2 Token"


class TestApiTokenServiceLimit:
    """Test ApiTokenService token limit enforcement."""

    def test_create_token_respects_limit(self, session: Session):
        """Creating tokens should fail when limit is reached."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)

        # Create max tokens (default limit is 10)
        for i in range(10):
            service.create_token(user.id, f"Token {i}")

        # 11th token should fail
        with pytest.raises(ValueError, match="Maximum tokens"):
            service.create_token(user.id, "Token 11")
