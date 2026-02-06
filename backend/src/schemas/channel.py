"""Channel binding Pydantic schemas for request/response validation.

Based on contracts/channel-binding-api.yaml for 012-ai-multi-channel feature.
"""

import uuid
from datetime import datetime

from pydantic import ConfigDict
from sqlmodel import SQLModel

from src.models.channel_binding import ChannelType


class ChannelBindingRead(SQLModel):
    """Response schema for a channel binding."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    channel_type: ChannelType
    external_user_id: str
    display_name: str | None = None
    is_active: bool
    default_ledger_id: uuid.UUID | None = None
    created_at: datetime
    last_used_at: datetime | None = None


class GenerateCodeRequest(SQLModel):
    """Request to generate a binding verification code."""

    channel_type: ChannelType
    default_ledger_id: uuid.UUID | None = None


class VerifyCodeRequest(SQLModel):
    """Request to verify a binding code (from bot side)."""

    code: str
    external_user_id: str
    display_name: str | None = None


class GenerateCodeResponse(SQLModel):
    """Response with the generated verification code."""

    code: str
    expires_in_seconds: int = 300
