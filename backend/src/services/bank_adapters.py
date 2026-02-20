"""Bank record CSV adapters using the Adapter pattern.

This module provides a flexible way to add support for different bank CSV formats.
Each bank has its own adapter class that handles the specific parsing logic.

To add a new bank:
1. Create a new adapter class extending BankRecordAdapter
2. Implement the required properties and parse method
3. Register the adapter in BANK_ADAPTERS dict

Example:
    class NewBankAdapter(BankRecordAdapter):
        @property
        def bank_code(self) -> str:
            return "NEW_BANK"

        @property
        def bank_name(self) -> str:
            return "新銀行"

        def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
            # Custom parsing logic
            ...

    # Register in BANK_ADAPTERS
    BANK_ADAPTERS["NEW_BANK"] = NewBankAdapter
"""

from __future__ import annotations

import csv
import datetime
import io
from abc import ABC, abstractmethod
from decimal import Decimal, InvalidOperation
from typing import TYPE_CHECKING, BinaryIO

from src.schemas.data_import import ParsedTransaction, ValidationError, ValidationErrorType
from src.schemas.transaction import TransactionType
from src.services.category_suggester import CategorySuggester
from src.services.csv_parser import CsvParser

if TYPE_CHECKING:
    pass


class BankRecordAdapter(ABC):
    """Abstract base adapter for bank account CSV parsing.

    Each bank adapter handles the specific format quirks of that bank's CSV export.
    """

    @property
    @abstractmethod
    def bank_code(self) -> str:
        """Unique bank code identifier (e.g., CTBC_BANK)."""
        ...

    @property
    @abstractmethod
    def bank_name(self) -> str:
        """Display name for the bank (e.g., 中國信託銀行)."""
        ...

    @property
    def bank_account_name(self) -> str:
        """Name for the bank account in transactions."""
        return f"銀行帳戶-{self.bank_name}"

    @property
    @abstractmethod
    def skip_rows(self) -> int:
        """Number of header rows to skip before data rows."""
        ...

    @property
    @abstractmethod
    def encoding(self) -> str:
        """File encoding (e.g., 'big5', 'utf-8')."""
        ...

    @abstractmethod
    def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
        """Parse the CSV file and return transactions and errors."""
        ...

    def _detect_encoding(self, file: BinaryIO) -> str:
        """Detect file encoding, falling back to adapter's default."""
        detected = CsvParser.detect_encoding(file)
        # If detection fails or returns ascii, use adapter's encoding
        if detected in ("ascii", "utf-8") and self.encoding != "utf-8":
            return self.encoding
        return detected

    def _clean_amount(self, s: str) -> Decimal | None:
        """Clean and parse amount string to Decimal.

        Handles:
        - Comma thousand separators
        - Currency symbols ($, NT)
        - Unicode MINUS SIGN (U+2212) used by some banks
        - Empty strings
        """
        s = s.strip().replace(",", "").replace("$", "").replace("NT", "")
        # Handle Unicode MINUS SIGN and regular minus as empty
        if not s or s == "−" or s == "-":
            return None
        try:
            return Decimal(s)
        except InvalidOperation:
            return None


class CtbcBankAdapter(BankRecordAdapter):
    """Adapter for 中國信託銀行 bank account CSV.

    Format verified: 2026-02-19
    Header: 活存明細查詢 + timestamp (2 lines) + column headers
    Columns: 日期,摘要,支出,存入,結餘,備註,轉出入帳號,註記
    Encoding: Big5
    """

    @property
    def bank_code(self) -> str:
        return "CTBC_BANK"

    @property
    def bank_name(self) -> str:
        return "中國信託銀行"

    @property
    def skip_rows(self) -> int:
        return 3  # 2 header lines + 1 column header

    @property
    def encoding(self) -> str:
        return "big5"

    def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
        result: list[ParsedTransaction] = []
        errors: list[ValidationError] = []
        suggester = CategorySuggester()

        # Detect encoding
        encoding = self._detect_encoding(file)
        content = file.read().decode(encoding, errors="replace")
        reader = csv.reader(io.StringIO(content))

        # Skip header rows
        for _ in range(self.skip_rows):
            try:
                next(reader)
            except StopIteration:
                break

        for i, row in enumerate(reader, start=self.skip_rows + 1):
            if len(row) < 5:
                continue

            try:
                # Column indices: 日期(0), 摘要(1), 支出(2), 存入(3), 餘額(4), 備註(5)
                date_str = row[0].strip()
                if not date_str:
                    continue

                # Parse date
                try:
                    parsed_date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
                except ValueError:
                    continue  # Skip rows with invalid dates (e.g., footer)

                # Parse description and memo
                description = row[1].strip()
                memo = row[5].strip() if len(row) > 5 else ""
                full_description = f"{description} - {memo}" if memo else description

                # Parse amounts
                withdrawal = self._clean_amount(row[2])
                deposit = self._clean_amount(row[3])

                if withdrawal and withdrawal > 0:
                    # Expense: from bank account to expense category
                    suggestion = suggester.suggest(full_description)
                    tx = ParsedTransaction(
                        row_number=i,
                        date=parsed_date,
                        transaction_type=TransactionType.EXPENSE,
                        from_account_name=self.bank_account_name,
                        to_account_name=suggestion.suggested_account_name,
                        amount=withdrawal,
                        description=full_description,
                        category_suggestion=suggestion,
                    )
                    result.append(tx)
                elif deposit and deposit > 0:
                    # Income: from income source to bank account
                    suggestion = suggester.suggest_income(full_description)
                    tx = ParsedTransaction(
                        row_number=i,
                        date=parsed_date,
                        transaction_type=TransactionType.INCOME,
                        from_account_name=suggestion.suggested_account_name,
                        to_account_name=self.bank_account_name,
                        amount=deposit,
                        description=full_description,
                        category_suggestion=suggestion,
                    )
                    result.append(tx)

            except Exception as e:
                errors.append(
                    ValidationError(
                        row_number=i,
                        error_type=ValidationErrorType.INVALID_FORMAT,
                        message=f"Error parsing row {i}: {e}",
                        value=str(row),
                    )
                )

        return result, errors


class CathayBankAdapter(BankRecordAdapter):
    """Adapter for 國泰世華銀行 bank account CSV.

    Format verified: 2026-02-20
    Header: Account info (5 lines) + column headers (1 line)
    Columns: "交易日期","帳務日期","說明","提出","存入","餘額","交易資訊","備註"
    Notes:
    - Uses 帳務日期 (col 1) instead of 交易日期 (col 0) because col 0 has multiline time
    - Uses "−" (U+2212 MINUS SIGN) for empty amounts
    - Has footer rows with totals
    - All fields are quoted
    Encoding: UTF-8
    """

    @property
    def bank_code(self) -> str:
        return "CATHAY_BANK"

    @property
    def bank_name(self) -> str:
        return "國泰世華銀行"

    @property
    def skip_rows(self) -> int:
        return 6  # 5 header lines + 1 column header

    @property
    def encoding(self) -> str:
        return "utf-8"

    def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
        result: list[ParsedTransaction] = []
        errors: list[ValidationError] = []
        suggester = CategorySuggester()

        # Detect encoding
        encoding = self._detect_encoding(file)
        content = file.read().decode(encoding, errors="replace")
        reader = csv.reader(io.StringIO(content))

        # Skip header rows
        for _ in range(self.skip_rows):
            try:
                next(reader)
            except StopIteration:
                break

        for i, row in enumerate(reader, start=self.skip_rows + 1):
            if len(row) < 6:
                continue

            try:
                # Column indices: 交易日期(0), 帳務日期(1), 說明(2), 提出(3), 存入(4), 餘額(5), 交易資訊(6), 備註(7)
                # Use 帳務日期 (col 1) because 交易日期 (col 0) has multiline time
                date_str = row[1].strip()
                if not date_str:
                    continue

                # Parse date
                try:
                    parsed_date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
                except ValueError:
                    continue  # Skip rows with invalid dates (e.g., footer)

                # Parse description and memo
                description = row[2].strip()
                memo = row[7].strip() if len(row) > 7 else ""
                # Skip if memo is just "−"
                if memo == "−":
                    memo = ""
                full_description = f"{description} - {memo}" if memo else description

                # Parse amounts (uses "−" for empty)
                withdrawal = self._clean_amount(row[3])
                deposit = self._clean_amount(row[4])

                if withdrawal and withdrawal > 0:
                    # Expense: from bank account to expense category
                    suggestion = suggester.suggest(full_description)
                    tx = ParsedTransaction(
                        row_number=i,
                        date=parsed_date,
                        transaction_type=TransactionType.EXPENSE,
                        from_account_name=self.bank_account_name,
                        to_account_name=suggestion.suggested_account_name,
                        amount=withdrawal,
                        description=full_description,
                        category_suggestion=suggestion,
                    )
                    result.append(tx)
                elif deposit and deposit > 0:
                    # Income: from income source to bank account
                    suggestion = suggester.suggest_income(full_description)
                    tx = ParsedTransaction(
                        row_number=i,
                        date=parsed_date,
                        transaction_type=TransactionType.INCOME,
                        from_account_name=suggestion.suggested_account_name,
                        to_account_name=self.bank_account_name,
                        amount=deposit,
                        description=full_description,
                        category_suggestion=suggestion,
                    )
                    result.append(tx)

            except Exception as e:
                errors.append(
                    ValidationError(
                        row_number=i,
                        error_type=ValidationErrorType.INVALID_FORMAT,
                        message=f"Error parsing row {i}: {e}",
                        value=str(row),
                    )
                )

        return result, errors


# ============================================================================
# Adapter Registry
# ============================================================================

# Register all available bank adapters
BANK_ADAPTERS: dict[str, type[BankRecordAdapter]] = {
    "CTBC_BANK": CtbcBankAdapter,
    "CATHAY_BANK": CathayBankAdapter,
}


def get_bank_adapter(bank_code: str) -> BankRecordAdapter:
    """Get a bank adapter instance by bank code.

    Args:
        bank_code: The bank code (e.g., "CTBC_BANK", "CATHAY_BANK")

    Returns:
        An instance of the appropriate BankRecordAdapter

    Raises:
        ValueError: If the bank code is not supported
    """
    adapter_cls = BANK_ADAPTERS.get(bank_code)
    if not adapter_cls:
        supported = ", ".join(BANK_ADAPTERS.keys())
        raise ValueError(f"Unsupported bank: {bank_code}. Supported banks: {supported}")
    return adapter_cls()


def get_supported_bank_adapters() -> list[BankRecordAdapter]:
    """Get list of all supported bank adapter instances."""
    return [cls() for cls in BANK_ADAPTERS.values()]
