from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ImportType(str, Enum):
    MYAB_CSV = "MYAB_CSV"
    CREDIT_CARD = "CREDIT_CARD"
    GMAIL_CC = "GMAIL_CC"  # Gmail credit card statement import (011)


class TransactionType(str, Enum):
    EXPENSE = "EXPENSE"
    INCOME = "INCOME"
    TRANSFER = "TRANSFER"


class AccountType(str, Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"


class ImportErrorType(str, Enum):
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    INVALID_FORMAT = "INVALID_FORMAT"
    ENCODING_ERROR = "ENCODING_ERROR"
    MISSING_COLUMN = "MISSING_COLUMN"
    TRANSACTION_LIMIT = "TRANSACTION_LIMIT"
    PREVIEW_EXPIRED = "PREVIEW_EXPIRED"
    IMPORT_FAILED = "IMPORT_FAILED"


class ValidationErrorType(str, Enum):
    INVALID_DATE = "INVALID_DATE"
    INVALID_AMOUNT = "INVALID_AMOUNT"
    MISSING_COLUMN = "MISSING_COLUMN"
    UNKNOWN_ACCOUNT_TYPE = "UNKNOWN_ACCOUNT_TYPE"
    INVALID_FORMAT = "INVALID_FORMAT"


class CategorySuggestion(BaseModel):
    suggested_account_id: UUID | None = None
    suggested_account_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    matched_keyword: str | None = None


class ParsedAccountPath(BaseModel):
    """Parsed hierarchical account path from CSV.

    Example: "L-信用卡.國泰世華信用卡.Cube卡" parses to:
    - account_type: LIABILITY
    - path_segments: ["信用卡", "國泰世華信用卡", "Cube卡"]
    - raw_name: "L-信用卡.國泰世華信用卡.Cube卡"
    """

    account_type: AccountType
    path_segments: list[str]  # Hierarchical path, e.g. ["信用卡", "國泰世華信用卡", "Cube卡"]
    raw_name: str  # Original name from CSV

    @property
    def leaf_name(self) -> str:
        """Return the leaf (deepest) account name."""
        return self.path_segments[-1] if self.path_segments else self.raw_name

    @property
    def full_path(self) -> str:
        """Return the full path as a dot-separated string without type prefix."""
        return ".".join(self.path_segments)


class ParsedTransaction(BaseModel):
    row_number: int
    date: date
    transaction_type: TransactionType
    from_account_name: str
    to_account_name: str
    amount: Decimal
    description: str
    invoice_number: str | None = None
    category_suggestion: CategorySuggestion | None = None
    from_account_id: UUID | None = None
    to_account_id: UUID | None = None
    # Hierarchical account paths (parsed from account names)
    from_account_path: ParsedAccountPath | None = None
    to_account_path: ParsedAccountPath | None = None


class AccountMapping(BaseModel):
    csv_account_name: str
    csv_account_type: AccountType
    path_segments: list[str] = Field(default_factory=list)  # Hierarchical path
    system_account_id: UUID | None = None
    create_new: bool = False
    suggested_name: str | None = None


class DuplicateWarning(BaseModel):
    row_number: int
    existing_transaction_ids: list[UUID]
    similarity_reason: str


class ValidationError(BaseModel):
    row_number: int
    error_type: ValidationErrorType
    message: str
    value: str | None = None


class ImportPreviewResponse(BaseModel):
    session_id: UUID
    total_count: int
    date_range: dict[str, date]  # {"start": ..., "end": ...}
    transactions: list[ParsedTransaction]
    duplicates: list[DuplicateWarning]
    account_mappings: list[AccountMapping]
    validation_errors: list[ValidationError]
    is_valid: bool


class ImportExecuteRequest(BaseModel):
    session_id: UUID
    account_mappings: list[AccountMapping]
    skip_duplicate_rows: list[int] = Field(default_factory=list)


class CreatedAccount(BaseModel):
    id: UUID
    name: str
    type: AccountType


class ImportResult(BaseModel):
    success: bool
    imported_count: int
    skipped_count: int = 0
    created_accounts: list[CreatedAccount] = Field(default_factory=list)
    date_range: dict[str, date] | None = None


class ImportJobStarted(BaseModel):
    job_id: UUID
    status: str = "processing"


class ImportJobStatus(BaseModel):
    job_id: UUID
    status: str  # processing, completed, failed
    progress: dict[str, int] | None = None  # {"current": ..., "total": ...}
    result: ImportResult | None = None
    error: dict[str, Any] | None = None  # ImportError


class BankConfig(BaseModel):
    code: str
    name: str
    encoding: str | None = None


class ImportError(BaseModel):
    error_type: ImportErrorType
    message: str
    details: dict[str, Any] | None = None
