"""AuditLog model for tracking entity changes.

Tracks changes to entities (accounts, etc.) for audit trail compliance.
"""

import uuid
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import Column, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel


class AuditAction(str, Enum):
    """Enum for audit log action types."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    REASSIGN = "REASSIGN"


class AuditLog(SQLModel, table=True):
    """Audit trail for entity changes.

    Stores a history of all create, update, delete, and reassign operations
    for entities within a ledger. Used for compliance and debugging.
    """

    __tablename__ = "audit_logs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    entity_type: str = Field(max_length=50, index=True)  # e.g., "Account"
    entity_id: uuid.UUID = Field(index=True)  # ID of the affected entity
    action: AuditAction = Field(sa_column=Column(Text))  # CREATE, UPDATE, DELETE, REASSIGN
    old_value: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB)
    )  # Previous state
    new_value: dict[str, Any] | None = Field(default=None, sa_column=Column(JSONB))  # New state
    extra_data: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSONB)
    )  # Additional context (e.g., reassignment details)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), index=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", index=True)
