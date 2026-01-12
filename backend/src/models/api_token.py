"""API Token model for MCP authentication.

Based on data-model.md from 007-api-for-mcp feature.
"""

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Index, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.user import User


class ApiToken(SQLModel, table=True):
    """Represents a long-lived API token for MCP authentication.

    Tokens are used by AI assistants (Claude, ChatGPT) to authenticate
    with the MCP server. The raw token is only shown once at creation;
    only the hash is stored.
    """

    __tablename__ = "api_tokens"
    __table_args__ = (
        Index("idx_api_tokens_user_id", "user_id"),
        Index(
            "idx_api_tokens_token_hash_active",
            "token_hash",
            postgresql_where="revoked_at IS NULL",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    name: str = Field(max_length=100)
    token_hash: str = Field(max_length=64)  # SHA-256 hash
    token_prefix: str = Field(max_length=8)  # First 8 chars for display
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = Field(default=None)
    revoked_at: datetime | None = Field(default=None)

    # Relationships
    user: "User" = Relationship(back_populates="api_tokens")

    @property
    def is_active(self) -> bool:
        """Check if token is active (not revoked)."""
        return self.revoked_at is None

    def revoke(self) -> None:
        """Revoke this token."""
        self.revoked_at = datetime.now(UTC)

    def update_last_used(self) -> None:
        """Update the last used timestamp."""
        self.last_used_at = datetime.now(UTC)
