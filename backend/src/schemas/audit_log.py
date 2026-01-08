"""AuditLog-related schemas for request/response validation."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlmodel import SQLModel

from src.models.audit_log import AuditAction


class AuditLogRead(SQLModel):
    """Schema for reading an audit log entry."""

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: AuditAction
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    extra_data: dict[str, Any] | None
    timestamp: datetime
    ledger_id: uuid.UUID


class AuditLogListItem(SQLModel):
    """Schema for audit log list items (summary)."""

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    action: AuditAction
    timestamp: datetime
