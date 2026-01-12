"""Unit tests for ApiToken model.

Tests the ApiToken model structure, validation rules, and state transitions.
"""

import uuid
from datetime import UTC, datetime

from src.models.api_token import ApiToken


class TestApiTokenModel:
    """Test ApiToken model structure and validation."""

    def test_create_api_token_with_required_fields(self):
        """ApiToken can be created with required fields."""
        user_id = uuid.uuid4()
        token = ApiToken(
            user_id=user_id,
            name="Claude Desktop",
            token_hash="a" * 64,  # SHA-256 hash is 64 hex chars
            token_prefix="ldo_abcd",
        )

        assert token.user_id == user_id
        assert token.name == "Claude Desktop"
        assert token.token_hash == "a" * 64
        assert token.token_prefix == "ldo_abcd"
        assert token.revoked_at is None
        assert token.last_used_at is None

    def test_api_token_has_uuid_id(self):
        """ApiToken id should be a UUID."""
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="Test Token",
            token_hash="b" * 64,
            token_prefix="ldo_test",
        )

        assert token.id is not None
        assert isinstance(token.id, uuid.UUID)

    def test_api_token_created_at_defaults_to_now(self):
        """ApiToken created_at should default to current time."""
        before = datetime.now(UTC)
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="Test Token",
            token_hash="c" * 64,
            token_prefix="ldo_test",
        )
        after = datetime.now(UTC)

        assert token.created_at is not None
        assert before <= token.created_at <= after

    def test_api_token_is_active_when_not_revoked(self):
        """ApiToken should be active when revoked_at is None."""
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="Test Token",
            token_hash="d" * 64,
            token_prefix="ldo_test",
        )

        assert token.is_active is True

    def test_api_token_is_not_active_when_revoked(self):
        """ApiToken should not be active when revoked_at is set."""
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="Test Token",
            token_hash="e" * 64,
            token_prefix="ldo_test",
            revoked_at=datetime.now(UTC),
        )

        assert token.is_active is False


class TestApiTokenStateTransitions:
    """Test ApiToken state transitions."""

    def test_revoke_sets_revoked_at(self):
        """Revoking a token should set revoked_at timestamp."""
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="Test Token",
            token_hash="f" * 64,
            token_prefix="ldo_test",
        )

        assert token.revoked_at is None
        token.revoke()
        assert token.revoked_at is not None
        assert token.is_active is False

    def test_update_last_used_sets_timestamp(self):
        """Updating last_used should set the timestamp."""
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="Test Token",
            token_hash="0" * 64,
            token_prefix="ldo_test",
        )

        assert token.last_used_at is None
        token.update_last_used()
        assert token.last_used_at is not None


class TestApiTokenValidation:
    """Test ApiToken field validation."""

    def test_name_max_length_100(self):
        """Token name should have max length of 100 characters."""
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="a" * 100,  # Max length
            token_hash="1" * 64,
            token_prefix="ldo_test",
        )

        assert len(token.name) == 100

    def test_token_hash_must_be_64_chars(self):
        """Token hash should be exactly 64 hex characters (SHA-256)."""
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="Test Token",
            token_hash="2" * 64,
            token_prefix="ldo_test",
        )

        assert len(token.token_hash) == 64

    def test_token_prefix_is_8_chars(self):
        """Token prefix should be 8 characters for display."""
        token = ApiToken(
            user_id=uuid.uuid4(),
            name="Test Token",
            token_hash="3" * 64,
            token_prefix="ldo_abcd",
        )

        assert len(token.token_prefix) == 8
