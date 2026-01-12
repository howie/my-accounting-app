"""Pydantic schemas for API Token endpoints."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TokenCreate(BaseModel):
    """Schema for creating a new API token."""

    name: str = Field(..., min_length=1, max_length=100, description="Human-readable label")


class TokenResponse(BaseModel):
    """Schema for token creation response (includes raw token once)."""

    id: UUID
    name: str
    token: str = Field(..., description="Full token (only shown once)")
    token_prefix: str = Field(..., description="First 8 chars for display")
    created_at: datetime
    message: str = "Token created. Copy it now - it won't be shown again."


class TokenListItem(BaseModel):
    """Schema for token in list response (no raw token)."""

    id: UUID
    name: str
    token_prefix: str
    created_at: datetime
    last_used_at: datetime | None = None
    is_revoked: bool = False


class TokenListResponse(BaseModel):
    """Schema for list tokens response."""

    tokens: list[TokenListItem]


class TokenRevokeResponse(BaseModel):
    """Schema for token revocation response."""

    id: UUID
    name: str
    revoked_at: datetime
    message: str = "Token revoked successfully"
