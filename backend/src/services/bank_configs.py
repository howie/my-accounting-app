"""Bank CSV configuration definitions for credit card import."""

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
