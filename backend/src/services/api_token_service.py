"""API Token service for managing MCP authentication tokens.

Based on contracts/api-tokens.md from 007-api-for-mcp feature.
"""

import hashlib
import secrets
import uuid
from dataclasses import dataclass

from sqlmodel import Session, select

from src.models.api_token import ApiToken
from src.models.user import User

# Token format: ldo_ + 48 alphanumeric characters
TOKEN_PREFIX = "ldo_"  # nosec B105 - This is a prefix identifier, not a password
TOKEN_BODY_LENGTH = 48
MAX_TOKENS_PER_USER = 10


@dataclass
class TokenCreateResult:
    """Result of token creation with raw token included."""

    token: ApiToken
    raw_token: str


class ApiTokenService:
    """Service for managing API tokens.

    Handles token creation, validation, revocation, and listing.
    """

    def __init__(self, session: Session) -> None:
        """Initialize service with database session."""
        self.session = session

    def create_token(self, user_id: uuid.UUID, name: str) -> TokenCreateResult:
        """Create a new API token for a user.

        Args:
            user_id: The user ID who owns the token
            name: Human-readable label for the token

        Returns:
            TokenCreateResult with the ApiToken and raw token string

        Raises:
            ValueError: If user has reached max tokens
        """
        # Check token limit
        existing_count = self._count_active_tokens(user_id)
        if existing_count >= MAX_TOKENS_PER_USER:
            raise ValueError(f"Maximum tokens ({MAX_TOKENS_PER_USER}) reached for user")

        # Generate raw token
        raw_token = self._generate_raw_token()

        # Hash the token for storage
        token_hash = self._hash_token(raw_token)

        # Create token record
        token = ApiToken(
            user_id=user_id,
            name=name,
            token_hash=token_hash,
            token_prefix=raw_token[:8],
        )

        self.session.add(token)
        self.session.commit()
        self.session.refresh(token)

        return TokenCreateResult(token=token, raw_token=raw_token)

    def validate_token(self, raw_token: str) -> ApiToken | None:
        """Validate a raw token and return the ApiToken if valid.

        Args:
            raw_token: The full token string to validate

        Returns:
            The ApiToken if valid and active, None otherwise
        """
        if not raw_token or not raw_token.startswith(TOKEN_PREFIX):
            return None

        token_hash = self._hash_token(raw_token)

        statement = select(ApiToken).where(
            ApiToken.token_hash == token_hash,
            ApiToken.revoked_at.is_(None),
        )
        token = self.session.exec(statement).first()

        if token:
            # Update last used timestamp
            token.update_last_used()
            self.session.add(token)
            self.session.commit()
            self.session.refresh(token)

        return token

    def get_user_for_token(self, raw_token: str) -> User | None:
        """Get the user associated with a token.

        Args:
            raw_token: The full token string

        Returns:
            The User if token is valid, None otherwise
        """
        token = self.validate_token(raw_token)
        if not token:
            return None

        return self.session.get(User, token.user_id)

    def revoke_token(self, token_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Revoke a token.

        Args:
            token_id: The token ID to revoke
            user_id: The user ID (for authorization)

        Returns:
            True if revoked, False if not found or unauthorized
        """
        statement = select(ApiToken).where(
            ApiToken.id == token_id,
            ApiToken.user_id == user_id,
            ApiToken.revoked_at.is_(None),
        )
        token = self.session.exec(statement).first()

        if not token:
            return False

        token.revoke()
        self.session.add(token)
        self.session.commit()

        return True

    def list_tokens(self, user_id: uuid.UUID, include_revoked: bool = False) -> list[ApiToken]:
        """List all tokens for a user.

        Args:
            user_id: The user ID
            include_revoked: Whether to include revoked tokens

        Returns:
            List of ApiToken objects
        """
        statement = select(ApiToken).where(ApiToken.user_id == user_id)

        if not include_revoked:
            statement = statement.where(ApiToken.revoked_at.is_(None))

        statement = statement.order_by(ApiToken.created_at.desc())

        return list(self.session.exec(statement).all())

    def get_token(self, token_id: uuid.UUID, user_id: uuid.UUID) -> ApiToken | None:
        """Get a specific token by ID.

        Args:
            token_id: The token ID
            user_id: The user ID (for authorization)

        Returns:
            The ApiToken if found and owned by user, None otherwise
        """
        statement = select(ApiToken).where(
            ApiToken.id == token_id,
            ApiToken.user_id == user_id,
        )
        return self.session.exec(statement).first()

    def _count_active_tokens(self, user_id: uuid.UUID) -> int:
        """Count active (non-revoked) tokens for a user."""
        statement = select(ApiToken).where(
            ApiToken.user_id == user_id,
            ApiToken.revoked_at.is_(None),
        )
        return len(list(self.session.exec(statement).all()))

    def _generate_raw_token(self) -> str:
        """Generate a new raw token string."""
        body = secrets.token_urlsafe(TOKEN_BODY_LENGTH)[:TOKEN_BODY_LENGTH]
        return f"{TOKEN_PREFIX}{body}"

    def _hash_token(self, raw_token: str) -> str:
        """Hash a raw token for storage."""
        return hashlib.sha256(raw_token.encode()).hexdigest()
