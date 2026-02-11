"""GmailConnection model for storing Gmail OAuth2 connection state.

Based on data-model.md for 011-gmail-cc-statement-import feature.
Stores encrypted OAuth2 credentials and scheduling configuration.
"""

import uuid
from datetime import UTC, date, datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, Text
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.ledger import Ledger


class GmailConnectionStatus(str, Enum):
    """Status of Gmail OAuth2 connection."""

    CONNECTED = "CONNECTED"
    EXPIRED = "EXPIRED"
    DISCONNECTED = "DISCONNECTED"


class ScheduleFrequency(str, Enum):
    """Frequency for scheduled scans."""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


class GmailConnection(SQLModel, table=True):
    """Stores a ledger's Gmail OAuth2 connection state and credentials.

    OAuth2 credentials are encrypted using Fernet symmetric encryption.
    One connection per ledger is allowed.
    """

    __tablename__ = "gmail_connections"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", unique=True, index=True)

    # Gmail account info
    email_address: str = Field(max_length=255)

    # Encrypted OAuth2 tokens (Fernet encrypted)
    encrypted_access_token: str = Field(sa_column=Column(Text, nullable=False))
    encrypted_refresh_token: str = Field(sa_column=Column(Text, nullable=False))
    token_expiry: datetime | None = Field(default=None)

    # Connection status
    status: GmailConnectionStatus = Field(
        default=GmailConnectionStatus.CONNECTED,
        sa_column=Column(SAEnum(GmailConnectionStatus)),
    )

    # Scan configuration
    scan_start_date: date = Field(
        default_factory=lambda: date.today().replace(month=max(1, date.today().month - 6))
    )

    # Schedule configuration (null = disabled)
    schedule_frequency: ScheduleFrequency | None = Field(
        default=None,
        sa_column=Column(SAEnum(ScheduleFrequency), nullable=True),
    )
    schedule_hour: int | None = Field(default=None, ge=0, le=23)
    schedule_day_of_week: int | None = Field(default=None, ge=0, le=6)  # 0=Monday

    # Last scan timestamp
    last_scan_at: datetime | None = Field(default=None)

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    ledger: "Ledger" = Relationship(back_populates="gmail_connection")
