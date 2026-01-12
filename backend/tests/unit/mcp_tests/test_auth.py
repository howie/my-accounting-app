"""Unit tests for MCP authentication middleware.

Tests token validation and user extraction for MCP requests.
"""

import pytest
from sqlmodel import Session

from src.api.mcp.auth import MCPAuthError, extract_bearer_token, get_mcp_user
from src.models.user import User
from src.services.api_token_service import ApiTokenService


class TestExtractBearerToken:
    """Test bearer token extraction from Authorization header."""

    def test_extract_valid_bearer_token(self):
        """Should extract token from valid Bearer header."""
        token = extract_bearer_token("Bearer ldo_abc123def456")
        assert token == "ldo_abc123def456"

    def test_extract_bearer_token_case_insensitive(self):
        """Should handle Bearer in any case."""
        token = extract_bearer_token("bearer ldo_abc123def456")
        assert token == "ldo_abc123def456"

        token = extract_bearer_token("BEARER ldo_abc123def456")
        assert token == "ldo_abc123def456"

    def test_extract_bearer_token_with_extra_spaces(self):
        """Should handle extra spaces in header."""
        token = extract_bearer_token("Bearer  ldo_abc123def456")
        assert token == "ldo_abc123def456"

    def test_extract_bearer_token_missing_header(self):
        """Should raise error for missing header."""
        with pytest.raises(MCPAuthError, match="Missing Authorization header"):
            extract_bearer_token(None)

    def test_extract_bearer_token_empty_header(self):
        """Should raise error for empty header."""
        with pytest.raises(MCPAuthError, match="Missing Authorization header"):
            extract_bearer_token("")

    def test_extract_bearer_token_wrong_scheme(self):
        """Should raise error for non-Bearer scheme."""
        with pytest.raises(MCPAuthError, match="Invalid authorization scheme"):
            extract_bearer_token("Basic abc123")

    def test_extract_bearer_token_no_token(self):
        """Should raise error when token is missing after Bearer."""
        with pytest.raises(MCPAuthError, match="Missing token"):
            extract_bearer_token("Bearer")

        with pytest.raises(MCPAuthError, match="Missing token"):
            extract_bearer_token("Bearer ")


class TestGetMcpUser:
    """Test MCP user retrieval from token."""

    def test_get_mcp_user_valid_token(self, session: Session):
        """Should return user for valid token."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Test Token")

        mcp_user = get_mcp_user(result.raw_token, session)

        assert mcp_user is not None
        assert mcp_user.id == user.id
        assert mcp_user.email == "test@example.com"

    def test_get_mcp_user_invalid_token(self, session: Session):
        """Should raise error for invalid token."""
        with pytest.raises(MCPAuthError, match="Invalid or expired token"):
            get_mcp_user("ldo_invalid_token", session)

    def test_get_mcp_user_revoked_token(self, session: Session):
        """Should raise error for revoked token."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Test Token")
        service.revoke_token(result.token.id, user.id)

        with pytest.raises(MCPAuthError, match="Invalid or expired token"):
            get_mcp_user(result.raw_token, session)

    def test_get_mcp_user_updates_last_used(self, session: Session):
        """Should update last_used_at when validating token."""
        user = User(email="test@example.com", display_name="Test User")
        session.add(user)
        session.commit()
        session.refresh(user)

        service = ApiTokenService(session)
        result = service.create_token(user.id, "Test Token")

        # Token last_used_at should be None initially
        assert result.token.last_used_at is None

        get_mcp_user(result.raw_token, session)

        # Refresh token from database
        session.refresh(result.token)
        assert result.token.last_used_at is not None


class TestMCPAuthError:
    """Test MCPAuthError exception."""

    def test_auth_error_has_code_and_message(self):
        """MCPAuthError should have code and message."""
        error = MCPAuthError(code="UNAUTHORIZED", message="Token expired")

        assert error.code == "UNAUTHORIZED"
        assert error.message == "Token expired"
        assert str(error) == "Token expired"

    def test_auth_error_unauthorized(self):
        """Should create UNAUTHORIZED error correctly."""
        error = MCPAuthError.unauthorized()

        assert error.code == "UNAUTHORIZED"
        assert "Invalid" in error.message or "Missing" in error.message

    def test_auth_error_token_revoked(self):
        """Should create TOKEN_REVOKED error correctly."""
        error = MCPAuthError.token_revoked()

        assert error.code == "TOKEN_REVOKED"
        assert "revoked" in error.message.lower()
