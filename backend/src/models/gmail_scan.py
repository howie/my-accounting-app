"""Gmail scan models for tracking scan jobs and discovered statements.

Based on data-model.md for 011-gmail-cc-statement-import feature.
"""

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Column, Text, UniqueConstraint
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from src.models.gmail_connection import GmailConnection
    from src.models.import_session import ImportSession


class ScanTriggerType(str, Enum):
    """How the scan was triggered."""

    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"


class ScanJobStatus(str, Enum):
    """Status of a scan job."""

    PENDING = "PENDING"
    SCANNING = "SCANNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class StatementParseStatus(str, Enum):
    """Status of PDF parsing for a statement."""

    PENDING = "PENDING"
    PARSED = "PARSED"
    PARSE_FAILED = "PARSE_FAILED"
    LLM_PARSED = "LLM_PARSED"


class StatementImportStatus(str, Enum):
    """Import status of a discovered statement."""

    NOT_IMPORTED = "NOT_IMPORTED"
    IMPORTED = "IMPORTED"
    SKIPPED = "SKIPPED"


class StatementScanJob(SQLModel, table=True):
    """Tracks each scan execution (manual or scheduled).

    Records which banks were scanned, how many statements were found,
    and the overall status of the scan.
    """

    __tablename__ = "statement_scan_jobs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    gmail_connection_id: uuid.UUID = Field(
        foreign_key="gmail_connections.id",
        index=True,
    )

    # Trigger info
    trigger_type: ScanTriggerType = Field(
        sa_column=Column(SAEnum(ScanTriggerType)),
    )

    # Status
    status: ScanJobStatus = Field(
        default=ScanJobStatus.PENDING,
        sa_column=Column(SAEnum(ScanJobStatus)),
    )

    # Scan details (JSON list of bank codes)
    banks_scanned: str = Field(default="[]")  # JSON array of bank codes

    # Results
    statements_found: int = Field(default=0)
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Timestamps
    started_at: datetime | None = Field(default=None)
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    gmail_connection: "GmailConnection" = Relationship()
    discovered_statements: list["DiscoveredStatement"] = Relationship(
        back_populates="scan_job",
    )


class DiscoveredStatement(SQLModel, table=True):
    """Represents a credit card statement found during scanning.

    Tracks the PDF attachment, parse status, and import status.
    Unique constraint on (bank_code, billing_period_start, billing_period_end)
    prevents duplicate statement processing.
    """

    __tablename__ = "discovered_statements"
    __table_args__ = (
        UniqueConstraint(
            "bank_code",
            "billing_period_start",
            "billing_period_end",
            name="uq_statement_period",
        ),
    )

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    scan_job_id: uuid.UUID = Field(
        foreign_key="statement_scan_jobs.id",
        index=True,
    )

    # Bank info
    bank_code: str = Field(max_length=20)
    bank_name: str = Field(max_length=100)

    # Billing period (null if parse failed)
    billing_period_start: date | None = Field(default=None)
    billing_period_end: date | None = Field(default=None)

    # Email info (for traceability)
    email_message_id: str = Field(max_length=255, index=True)
    email_subject: str = Field(max_length=500)
    email_date: datetime

    # PDF attachment info
    pdf_attachment_id: str = Field(max_length=255)
    pdf_filename: str = Field(max_length=255)

    # Parse status
    parse_status: StatementParseStatus = Field(
        default=StatementParseStatus.PENDING,
        sa_column=Column(SAEnum(StatementParseStatus)),
    )
    parse_confidence: float | None = Field(default=None, ge=0.0, le=1.0)

    # Parsed results
    transaction_count: int = Field(default=0)
    total_amount: Decimal | None = Field(default=None, decimal_places=2)

    # Import status
    import_status: StatementImportStatus = Field(
        default=StatementImportStatus.NOT_IMPORTED,
        sa_column=Column(SAEnum(StatementImportStatus)),
    )
    import_session_id: uuid.UUID | None = Field(
        default=None,
        foreign_key="import_sessions.id",
    )

    # Error message (if parse failed)
    error_message: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Relationships
    scan_job: "StatementScanJob" = Relationship(back_populates="discovered_statements")
    import_session: "ImportSession | None" = Relationship()
