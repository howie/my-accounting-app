"""Schemas for Gmail credit card statement import API.

Based on contracts/gmail-import-api.yaml for 011-gmail-cc-statement-import feature.
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# Enums (match models)
class GmailConnectionStatus(str, Enum):
    CONNECTED = "CONNECTED"
    EXPIRED = "EXPIRED"
    DISCONNECTED = "DISCONNECTED"


class ScanJobStatus(str, Enum):
    PENDING = "PENDING"
    SCANNING = "SCANNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ScanTriggerType(str, Enum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"


class StatementParseStatus(str, Enum):
    PENDING = "PENDING"
    PARSED = "PARSED"
    PARSE_FAILED = "PARSE_FAILED"
    LLM_PARSED = "LLM_PARSED"


class StatementImportStatus(str, Enum):
    NOT_IMPORTED = "NOT_IMPORTED"
    IMPORTED = "IMPORTED"
    SKIPPED = "SKIPPED"


class ScheduleFrequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"


# Response schemas
class GmailConnectionResponse(BaseModel):
    id: UUID
    email_address: str
    status: GmailConnectionStatus
    last_scan_at: datetime | None
    scan_start_date: date
    created_at: datetime


class GmailBankInfo(BaseModel):
    code: str
    name: str
    email_query: str
    password_hint: str


class UserBankSettingResponse(BaseModel):
    bank_code: str
    bank_name: str
    is_enabled: bool
    has_password: bool  # Never expose actual password
    credit_card_account_id: UUID | None
    credit_card_account_name: str | None


class ScanJobResponse(BaseModel):
    id: UUID
    trigger_type: ScanTriggerType
    status: ScanJobStatus
    banks_scanned: list[str]
    statements_found: int
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None


class DiscoveredStatementResponse(BaseModel):
    id: UUID
    bank_code: str
    bank_name: str
    billing_period_start: date | None
    billing_period_end: date | None
    email_subject: str
    email_date: datetime
    pdf_filename: str
    parse_status: StatementParseStatus
    parse_confidence: float | None
    transaction_count: int
    total_amount: Decimal | None
    import_status: StatementImportStatus


class StatementTransaction(BaseModel):
    index: int
    date: date
    merchant_name: str
    amount: Decimal
    currency: str = "TWD"
    suggested_category: str | None
    category_confidence: float
    is_foreign: bool = False
    original_description: str


class DuplicateWarning(BaseModel):
    transaction_index: int
    existing_transaction_ids: list[UUID]
    reason: str


class BillingPeriod(BaseModel):
    start: date
    end: date


class StatementPreviewResponse(BaseModel):
    statement_id: UUID
    bank_name: str
    billing_period: BillingPeriod
    transactions: list[StatementTransaction]
    total_amount: Decimal
    duplicate_warnings: list[DuplicateWarning]
    parse_confidence: float


class CreatedAccount(BaseModel):
    id: UUID
    name: str
    type: str


class ImportStatementResponse(BaseModel):
    success: bool
    import_session_id: UUID
    imported_count: int
    skipped_count: int
    created_accounts: list[CreatedAccount] = Field(default_factory=list)


class ScheduleSettingsResponse(BaseModel):
    frequency: ScheduleFrequency | None
    hour: int | None
    day_of_week: int | None  # 0=Monday
    next_scan_at: datetime | None


# Request schemas
class UpdateBankSettingsRequest(BaseModel):
    bank_code: str
    is_enabled: bool | None = None
    pdf_password: str | None = None  # Set to update, null to keep existing
    credit_card_account_id: UUID | None = None


class TriggerScanRequest(BaseModel):
    bank_codes: list[str] | None = None  # None = scan all enabled banks


class CategoryOverride(BaseModel):
    transaction_index: int
    category_name: str
    account_id: UUID | None = None


class ImportStatementRequest(BaseModel):
    statement_id: UUID
    category_overrides: list[CategoryOverride] = Field(default_factory=list)
    skip_transaction_indices: list[int] = Field(default_factory=list)


class UpdateScheduleRequest(BaseModel):
    frequency: ScheduleFrequency | None  # None to disable
    hour: int | None = Field(default=None, ge=0, le=23)
    day_of_week: int | None = Field(default=None, ge=0, le=6)  # Required for WEEKLY


# Auth responses
class GmailAuthUrlResponse(BaseModel):
    auth_url: str


class GmailDisconnectResponse(BaseModel):
    message: str


# List responses
class BanksListResponse(BaseModel):
    banks: list[GmailBankInfo]


class BankSettingsListResponse(BaseModel):
    settings: list[UserBankSettingResponse]


class StatementsListResponse(BaseModel):
    statements: list[DiscoveredStatementResponse]


class ScanHistoryResponse(BaseModel):
    items: list[ScanJobResponse]
    total: int
