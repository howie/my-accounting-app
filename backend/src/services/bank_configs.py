"""Bank CSV configuration definitions for credit card and bank record import."""

from dataclasses import dataclass


@dataclass
class BankCsvConfig:
    """Configuration for parsing bank credit card CSV files."""

    code: str  # Bank code (e.g., CATHAY, CTBC)
    name: str  # Bank display name (e.g., 國泰世華)
    date_column: int  # Date column index (0-based)
    date_format: str  # Date format string (e.g., %Y/%m/%d)
    description_column: int  # Merchant/description column index
    amount_column: int  # Amount column index
    skip_rows: int = 1  # Number of header rows to skip
    encoding: str = "utf-8"  # File encoding


# Bank configurations
# Note: These are initial configurations and may need adjustment based on actual bank CSV samples

BANK_CONFIGS: dict[str, BankCsvConfig] = {
    "CATHAY": BankCsvConfig(
        code="CATHAY",
        name="國泰世華",
        date_column=0,
        date_format="%Y/%m/%d",
        description_column=2,
        amount_column=3,
        skip_rows=1,
        encoding="utf-8",
    ),
    "CTBC": BankCsvConfig(
        code="CTBC",
        name="中國信託",
        date_column=0,
        date_format="%Y-%m-%d",
        description_column=1,
        amount_column=2,
        skip_rows=1,
        encoding="utf-8",
    ),
    "ESUN": BankCsvConfig(
        code="ESUN",
        name="玉山銀行",
        date_column=0,
        date_format="%Y/%m/%d",
        description_column=1,
        amount_column=2,
        skip_rows=1,
        encoding="utf-8",
    ),
    "TAISHIN": BankCsvConfig(
        code="TAISHIN",
        name="台新銀行",
        date_column=0,
        date_format="%Y/%m/%d",
        description_column=2,
        amount_column=3,
        skip_rows=1,
        encoding="big5",
    ),
    "FUBON": BankCsvConfig(
        code="FUBON",
        name="富邦銀行",
        date_column=0,
        date_format="%Y-%m-%d",
        description_column=1,
        amount_column=2,
        skip_rows=1,
        encoding="utf-8",
    ),
}


def get_supported_banks() -> list[BankCsvConfig]:
    """Get list of all supported bank configurations."""
    return list(BANK_CONFIGS.values())


def get_bank_config(bank_code: str) -> BankCsvConfig | None:
    """Get bank configuration by code."""
    return BANK_CONFIGS.get(bank_code)


# ============================================================================
# Bank Record (Account Transaction) CSV Configurations
# ============================================================================


@dataclass
class BankRecordCsvConfig:
    """Configuration for parsing bank account transaction CSV files.

    Supports two amount modes:
    - Dual columns: separate withdrawal_column (提出) and deposit_column (存入)
    - Single column: amount_column with signed values (negative=withdrawal, positive=deposit)
    """

    code: str  # Bank code (e.g., CATHAY_BANK, CTBC_BANK)
    name: str  # Bank display name (e.g., 國泰世華銀行)
    date_column: int  # Date column index (0-based)
    date_format: str  # Date format string (e.g., %Y/%m/%d)
    description_column: int  # 摘要/說明 column index
    # Amount columns - dual column mode (most Taiwan banks)
    withdrawal_column: int | None = None  # 提出/支出 column index
    deposit_column: int | None = None  # 存入 column index
    # Amount columns - single column mode (alternative)
    amount_column: int | None = None  # Signed amount column
    # Optional columns
    balance_column: int | None = None  # 餘額 column (ignored during import)
    memo_column: int | None = None  # 備註 column
    skip_rows: int = 1  # Number of header rows to skip
    encoding: str = "big5"  # File encoding (default Big5 for Taiwan banks)


# Bank record configurations for major Taiwan banks
# Only add configs that have been verified with actual CSV samples
BANK_RECORD_CONFIGS: dict[str, BankRecordCsvConfig] = {
    # Verified with actual CSV sample (2026-02-19)
    # Format: 活存明細查詢 + timestamp header (2 lines), then column headers
    # Columns: 日期,摘要,支出,存入,結餘,備註,轉出入帳號,註記
    "CTBC_BANK": BankRecordCsvConfig(
        code="CTBC_BANK",
        name="中國信託銀行",
        date_column=0,
        date_format="%Y/%m/%d",
        description_column=1,
        withdrawal_column=2,
        deposit_column=3,
        balance_column=4,
        memo_column=5,
        skip_rows=3,  # 2 header lines + 1 column header line
        encoding="big5",
    ),
}


def get_supported_bank_records() -> list[BankRecordCsvConfig]:
    """Get list of all supported bank record configurations."""
    return list(BANK_RECORD_CONFIGS.values())


def get_bank_record_config(bank_code: str) -> BankRecordCsvConfig | None:
    """Get bank record configuration by code."""
    return BANK_RECORD_CONFIGS.get(bank_code)
