"""EmailAuthorization model for multi-channel integration.

Based on data-model.md for 012-ai-multi-channel feature.
Records user email access authorizations (Gmail OAuth2).
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, Index, Text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.email_import_batch import EmailImportBatch
    from src.models.user import User


class EmailProvider(str, Enum):
    """Supported email providers."""

    GMAIL = "GMAIL"


class EmailAuthorization(SQLModel, table=True):
    """Records user email access authorization.

    Stores encrypted OAuth2 refresh tokens for Gmail API access.
    Supports soft revocation via is_active flag and revoked_at timestamp.
    """

    __tablename__ = "email_authorizations"
    __table_args__ = (
        Index("idx_email_auth_user", "user_id"),
        Index("idx_email_auth_active", "user_id", postgresql_where="is_active = true"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    email_address: str = Field(max_length=255)
    provider: EmailProvider = Field(sa_column=Column(SAEnum(EmailProvider), nullable=False))
    encrypted_refresh_token: str | None = Field(default=None, sa_column=Column(Text))
    scopes: str = Field(max_length=500)
    is_active: bool = Field(default=True)
    last_sync_at: datetime | None = Field(default=None)
    token_expires_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    revoked_at: datetime | None = Field(default=None)

    # Relationships
    user: "User" = Relationship(back_populates="email_authorizations")
    import_batches: list["EmailImportBatch"] = Relationship(back_populates="email_authorization")
