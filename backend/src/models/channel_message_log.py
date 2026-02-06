"""ChannelMessageLog model for multi-channel integration.

Based on data-model.md for 012-ai-multi-channel feature.
Audit trail for all messages received through external channels.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import JSON, Column, Index, Text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.channel_binding import ChannelBinding


class MessageType(str, Enum):
    """Types of messages received from channels."""

    TEXT = "TEXT"
    VOICE = "VOICE"
    COMMAND = "COMMAND"


class ProcessingStatus(str, Enum):
    """Processing status of a channel message."""

    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ChannelMessageLog(SQLModel, table=True):
    """Audit trail for messages received through external channels.

    Records raw message content, parsed intent, processing status,
    and links to any transaction created as a result.
    """

    __tablename__ = "channel_message_logs"
    __table_args__ = (
        Index("idx_message_log_binding", "channel_binding_id"),
        Index("idx_message_log_created", "created_at"),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    channel_binding_id: uuid.UUID = Field(foreign_key="channel_bindings.id")
    channel_type: str = Field(max_length=20)
    message_type: MessageType = Field(sa_column=Column(SAEnum(MessageType), nullable=False))
    raw_content: str = Field(sa_column=Column(Text, nullable=False))
    parsed_intent: str | None = Field(default=None, max_length=50)
    parsed_data: dict[str, Any] | None = Field(default=None, sa_column=Column(JSON))
    processing_status: ProcessingStatus = Field(
        default=ProcessingStatus.RECEIVED,
        sa_column=Column(SAEnum(ProcessingStatus), nullable=False, default="RECEIVED"),
    )
    error_message: str | None = Field(default=None, max_length=500)
    response_text: str | None = Field(default=None, sa_column=Column(Text))
    transaction_id: uuid.UUID | None = Field(default=None, index=True)
    processing_time_ms: int | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    channel_binding: "ChannelBinding" = Relationship(back_populates="message_logs")
