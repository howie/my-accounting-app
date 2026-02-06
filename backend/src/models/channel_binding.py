"""ChannelBinding model for multi-channel integration.

Based on data-model.md for 012-ai-multi-channel feature.
Records the mapping between a system user and an external channel account.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, Index
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.channel_message_log import ChannelMessageLog
    from src.models.user import User


class ChannelType(str, Enum):
    """Supported channel types."""

    TELEGRAM = "TELEGRAM"
    LINE = "LINE"
    SLACK = "SLACK"


class ChannelBinding(SQLModel, table=True):
    """Maps a system user account to an external channel account.

    Supports soft delete via is_active flag and unbound_at timestamp.
    A single external_user_id + channel_type can only have one active binding.
    """

    __tablename__ = "channel_bindings"
    __table_args__ = (
        # Duplicate active binding prevention is enforced at service layer.
        # PostgreSQL partial unique index is defined in Alembic migration:
        #   CREATE UNIQUE INDEX ... WHERE is_active = true
        Index("idx_channel_binding_user", "user_id"),
        Index("idx_channel_binding_lookup", "channel_type", "external_user_id"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="users.id", index=True)
    channel_type: ChannelType = Field(sa_column=Column(SAEnum(ChannelType), nullable=False))
    external_user_id: str = Field(max_length=255)
    display_name: str | None = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    default_ledger_id: uuid.UUID | None = Field(
        default=None, foreign_key="ledgers.id", nullable=True
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_used_at: datetime | None = Field(default=None)
    unbound_at: datetime | None = Field(default=None)

    # Relationships
    user: "User" = Relationship(back_populates="channel_bindings")
    message_logs: list["ChannelMessageLog"] = Relationship(back_populates="channel_binding")
