"""Chat API schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request schema for chat messages."""

    message: str = Field(..., min_length=1, max_length=2000)
    ledger_id: UUID | None = None


class ToolCallResult(BaseModel):
    """Result of a tool call made during chat."""

    tool_name: str
    result: dict[str, Any]


class ChatResponse(BaseModel):
    """Response schema for chat messages."""

    id: str
    message: str
    tool_calls: list[ToolCallResult] = Field(default_factory=list)
    created_at: datetime


class ChatErrorResponse(BaseModel):
    """Error response for chat API."""

    error: dict[str, str]
