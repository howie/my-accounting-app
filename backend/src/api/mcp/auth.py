"""MCP authentication middleware.

Handles token validation and user extraction for MCP requests.
"""

from sqlmodel import Session

from src.models.user import User
from src.services.api_token_service import ApiTokenService


class MCPAuthError(Exception):
    """Exception raised for MCP authentication errors."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)

    @classmethod
    def unauthorized(cls) -> "MCPAuthError":
        """Create an UNAUTHORIZED error."""
        return cls(code="UNAUTHORIZED", message="Invalid or expired token")

    @classmethod
    def token_revoked(cls) -> "MCPAuthError":
        """Create a TOKEN_REVOKED error."""
        return cls(code="TOKEN_REVOKED", message="API token has been revoked")

    @classmethod
    def missing_auth(cls) -> "MCPAuthError":
        """Create a missing auth error."""
        return cls(code="UNAUTHORIZED", message="Missing Authorization header")


def extract_bearer_token(authorization_header: str | None) -> str:
    """Extract bearer token from Authorization header.

    Args:
        authorization_header: The full Authorization header value

    Returns:
        The token string (without "Bearer " prefix)

    Raises:
        MCPAuthError: If header is missing, invalid scheme, or no token
    """
    if not authorization_header:
        raise MCPAuthError(code="UNAUTHORIZED", message="Missing Authorization header")

    # Split on whitespace and handle case-insensitively
    parts = authorization_header.split()

    if len(parts) == 0:
        raise MCPAuthError(code="UNAUTHORIZED", message="Missing Authorization header")

    if len(parts) == 1:
        # Only scheme, no token
        if parts[0].lower() == "bearer":
            raise MCPAuthError(code="UNAUTHORIZED", message="Missing token in Authorization header")
        raise MCPAuthError(
            code="UNAUTHORIZED", message="Invalid authorization scheme. Use 'Bearer'"
        )

    scheme = parts[0].lower()
    token = parts[1]

    if scheme != "bearer":
        raise MCPAuthError(
            code="UNAUTHORIZED", message="Invalid authorization scheme. Use 'Bearer'"
        )

    if not token:
        raise MCPAuthError(code="UNAUTHORIZED", message="Missing token in Authorization header")

    return token


def get_mcp_user(raw_token: str, session: Session) -> User:
    """Get the user associated with an MCP token.

    Args:
        raw_token: The full token string
        session: Database session

    Returns:
        The User associated with the token

    Raises:
        MCPAuthError: If token is invalid or revoked
    """
    service = ApiTokenService(session)
    user = service.get_user_for_token(raw_token)

    if not user:
        raise MCPAuthError.unauthorized()

    return user


def validate_mcp_request(authorization_header: str | None, session: Session) -> User:
    """Validate an MCP request and return the authenticated user.

    Args:
        authorization_header: The Authorization header from the request
        session: Database session

    Returns:
        The authenticated User

    Raises:
        MCPAuthError: If authentication fails
    """
    token = extract_bearer_token(authorization_header)
    return get_mcp_user(token, session)
