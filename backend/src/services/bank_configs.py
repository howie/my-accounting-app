"""Bank CSV configuration definitions for credit card and bank statement import."""

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
    skip_rows: int = 1  # Number of header rows to skip (used when header_marker is absent)
    encoding: str = "utf-8"  # File encoding
    header_marker: str | None = None  # Search for this string to dynamically locate header row
    skip_negative_amounts: bool = False  # Skip rows with negative amounts (e.g., payment records)
    date_year_pattern: str | None = None  # Regex to extract (year, month) from first row


# Bank configurations
# Note: These are initial configurations and may need adjustment based on actual bank CSV samples

BANK_CONFIGS: dict[str, BankCsvConfig] = {
    "CATHAY": BankCsvConfig(
        code="CATHAY",
        name="國泰世華",
        date_column=0,
        date_format="%m/%d",  # Real format: MM/DD without year
        description_column=1,  # 交易說明
        amount_column=2,  # 新臺幣金額
        skip_rows=1,
        encoding="utf-8",
        header_marker="消費日",  # Dynamically locate header row
        skip_negative_amounts=True,  # Skip payment records (negative amounts)
        date_year_pattern=r"(\d{4})/(\d{2})信用卡對帳單",  # Extract year/month from first row
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


@dataclass
class BankStatementConfig:
    """Per-bank adapter configuration for savings/checking account statements."""

    code: str  # Bank code (e.g., CATHAY, CTBC)
    name: str  # Bank display name
    bank_account_name: str  # Default account name, e.g., "國泰世華.活期存款"
    date_column: int  # Date column index (0-based)
    date_format: str  # Date format string
    description_column: int  # Transaction description column index
    debit_column: int | None  # Withdrawal column (出帳), use with credit_column
    credit_column: int | None  # Deposit column (入帳), use with debit_column
    amount_column: int | None  # Signed amount column (negative=debit, positive=credit)
    balance_column: int | None = None  # Balance column (optional, not imported)
    skip_rows: int = 1  # Number of header rows to skip
    encoding: str = "utf-8"  # File encoding
    header_marker: str | None = None  # Dynamically locate header row by this string


# Bank statement configurations (savings/checking accounts)
# NOTE: These are initial estimates. Update after confirming with actual CSV samples.
BANK_STATEMENT_CONFIGS: dict[str, BankStatementConfig] = {
    "CATHAY": BankStatementConfig(
        code="CATHAY",
        name="國泰世華",
        bank_account_name="國泰世華.活期存款",
        date_column=0,
        date_format="%Y/%m/%d",
        description_column=1,
        debit_column=2,
        credit_column=3,
        amount_column=None,
        balance_column=4,
        skip_rows=1,
        encoding="utf-8",
    ),
    "CTBC": BankStatementConfig(
        code="CTBC",
        name="中國信託",
        bank_account_name="中國信託.活期存款",
        date_column=0,
        date_format="%Y/%m/%d",
        description_column=1,
        debit_column=2,
        credit_column=3,
        amount_column=None,
        balance_column=4,
        skip_rows=1,
        encoding="utf-8",
    ),
    "ESUN": BankStatementConfig(
        code="ESUN",
        name="玉山銀行",
        bank_account_name="玉山銀行.活期存款",
        date_column=0,
        date_format="%Y/%m/%d",
        description_column=1,
        debit_column=2,
        credit_column=3,
        amount_column=None,
        balance_column=4,
        skip_rows=1,
        encoding="utf-8",
    ),
    "TAISHIN": BankStatementConfig(
        code="TAISHIN",
        name="台新銀行",
        bank_account_name="台新銀行.活期存款",
        date_column=0,
        date_format="%Y/%m/%d",
        description_column=1,
        debit_column=2,
        credit_column=3,
        amount_column=None,
        balance_column=4,
        skip_rows=1,
        encoding="big5",
    ),
    "FUBON": BankStatementConfig(
        code="FUBON",
        name="富邦銀行",
        bank_account_name="富邦銀行.活期存款",
        date_column=0,
        date_format="%Y-%m-%d",
        description_column=1,
        debit_column=2,
        credit_column=3,
        amount_column=None,
        balance_column=4,
        skip_rows=1,
        encoding="utf-8",
    ),
}


def get_supported_bank_statement_banks() -> list[BankStatementConfig]:
    """Get list of all supported bank statement configurations."""
    return list(BANK_STATEMENT_CONFIGS.values())


def get_bank_statement_config(bank_code: str) -> BankStatementConfig | None:
    """Get bank statement configuration by code."""
    return BANK_STATEMENT_CONFIGS.get(bank_code)
