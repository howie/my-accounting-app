import csv
import io
import re
from datetime import date
from typing import BinaryIO

import charset_normalizer


class CsvParser:
    @staticmethod
    def detect_encoding(file: BinaryIO) -> str:
        """
        Detect encoding of the file.
        Prioritizes UTF-8, then Big5 (common in TW).
        """
        detect_size = 32 * 1024  # 32KB to cover long headers
        start_pos = file.tell()
        content = file.read(detect_size)
        file.seek(start_pos)

        # Use charset_normalizer
        matches = charset_normalizer.from_bytes(content)
        best = matches.best()

        if best and best.encoding:
            # Normalize encoding name (e.g. 'utf_8' -> 'utf-8')
            return best.encoding

        # Fallback
        return "utf-8"

    @staticmethod
    def read_csv(file: BinaryIO, encoding: str | None = None) -> list[dict[str, str]]:
        """
        Read CSV file and return list of dictionaries.
        """
        if encoding is None:
            encoding = CsvParser.detect_encoding(file)

        # Reset file pointer just in case
        file.seek(0)

        try:
            content = file.read().decode(encoding)
        except UnicodeDecodeError as e:
            # If explicit encoding failed or detection was wrong
            raise ValueError(f"Failed to decode file with encoding {encoding}: {e}") from e

        # Remove BOM if present (utf-8-sig)
        if content.startswith("\ufeff"):
            content = content[1:]

        f = io.StringIO(content)
        reader = csv.DictReader(f)

        return list(reader)


from datetime import datetime
from decimal import Decimal, InvalidOperation

from src.schemas.data_import import (
    AccountType,
    ParsedAccountPath,
    ParsedTransaction,
    TransactionType,
    ValidationError,
    ValidationErrorType,
)


class MyAbCsvParser(CsvParser):
    """
    Parser for MyAB CSV export files.

    Supports two CSV formats:
    1. Full format (跨科目時期匯出): 日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
    2. Simple format (單一科目匯出): 日期,分類,科目,金額,明細,備註,發票
    """

    def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
        rows = self.read_csv(file)
        result = []
        errors = []

        if not rows:
            return result, errors

        # Detect format by checking column headers
        first_row_keys = set(rows[0].keys())
        is_simple_format = "分類" in first_row_keys and "科目" in first_row_keys

        for i, row in enumerate(rows, start=1):  # 1-based row number
            try:
                if is_simple_format:
                    tx, error = self._parse_simple_format(i, row)
                else:
                    tx, error = self._parse_full_format(i, row)

                if error:
                    errors.append(error)
                    continue
                if tx:
                    result.append(tx)

            except Exception as e:
                errors.append(
                    ValidationError(
                        row_number=i,
                        error_type=ValidationErrorType.INVALID_FORMAT,
                        message=f"Unexpected error: {str(e)}",
                        value=str(row),
                    )
                )

        return result, errors

    def _parse_simple_format(
        self, row_number: int, row: dict[str, str]
    ) -> tuple[ParsedTransaction | None, ValidationError | None]:
        """
        Parse simple format: 日期,分類,科目,金額,明細,備註,發票

        In this format:
        - 分類 (category): destination account with type prefix (E-/I-/A-/L-)
        - 科目 (account): source account with type prefix
        - Transaction type is inferred from the 分類 prefix
        """
        date_str = row.get("日期")
        category = row.get("分類")  # to_account (destination)
        account = row.get("科目")  # from_account (source)
        amount_str = row.get("金額")

        if not date_str or not category or not account or not amount_str:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.MISSING_COLUMN,
                message="Missing required fields (日期, 分類, 科目, or 金額)",
                value=str(row),
            )

        # Parse date
        try:
            parsed_date = self._parse_date(date_str)
        except ValueError as e:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.INVALID_DATE,
                message=str(e),
                value=date_str,
            )

        # Parse amount
        try:
            amount = Decimal(amount_str.replace(",", ""))
        except InvalidOperation:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.INVALID_AMOUNT,
                message=f"Invalid amount format: {amount_str}",
                value=amount_str,
            )

        # Parse hierarchical account paths
        category_path = self.parse_hierarchical_account(category)
        account_path = self.parse_hierarchical_account(account)

        if category_path.account_type == AccountType.EXPENSE:
            # E- category means expense: money flows from account to expense category
            tx_type = TransactionType.EXPENSE
            from_acc = account
            to_acc = category
            from_path = account_path
            to_path = category_path
        elif category_path.account_type == AccountType.INCOME:
            # I- category means income: money flows from income source to account
            tx_type = TransactionType.INCOME
            from_acc = category
            to_acc = account
            from_path = category_path
            to_path = account_path
        elif category_path.account_type in (AccountType.ASSET, AccountType.LIABILITY):
            # A-/L- category means transfer between asset/liability accounts
            tx_type = TransactionType.TRANSFER
            from_acc = account
            to_acc = category
            from_path = account_path
            to_path = category_path
        else:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.UNKNOWN_ACCOUNT_TYPE,
                message=f"Cannot determine transaction type from category: {category}",
                value=category,
            )

        tx = ParsedTransaction(
            row_number=row_number,
            date=parsed_date,
            transaction_type=tx_type,
            from_account_name=from_acc,
            to_account_name=to_acc,
            amount=amount,
            description=row.get("明細", ""),
            invoice_number=row.get("發票") or row.get("發票號碼"),
            from_account_path=from_path,
            to_account_path=to_path,
        )
        return tx, None

    def _parse_full_format(
        self, row_number: int, row: dict[str, str]
    ) -> tuple[ParsedTransaction | None, ValidationError | None]:
        """
        Parse full format: 日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
        """
        date_str = row.get("日期")
        type_str = row.get("交易類型")
        amount_str = row.get("金額")

        if not date_str or not type_str or not amount_str:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.MISSING_COLUMN,
                message="Missing required fields (日期, 交易類型, or 金額)",
                value=str(row),
            )

        # Parse Date
        try:
            parsed_date = self._parse_date(date_str)
        except ValueError as e:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.INVALID_DATE,
                message=str(e),
                value=date_str,
            )

        # Parse Amount
        try:
            amount = Decimal(amount_str.replace(",", ""))
        except InvalidOperation:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.INVALID_AMOUNT,
                message=f"Invalid amount format: {amount_str}",
                value=amount_str,
            )

        # Determine Transaction Type and Accounts
        tx_type_enum = None
        from_acc = None
        to_acc = None

        # Support English and Chinese types
        type_str_lower = type_str.lower() if type_str else ""

        if type_str == "支出" or type_str_lower == "expense":
            tx_type_enum = TransactionType.EXPENSE
            from_acc = row.get("從科目")
            to_acc = row.get("支出科目")
        elif type_str == "收入" or type_str_lower == "income":
            tx_type_enum = TransactionType.INCOME
            from_acc = row.get("收入科目")
            to_acc = row.get("到科目")
        elif type_str == "轉帳" or type_str_lower == "transfer":
            tx_type_enum = TransactionType.TRANSFER
            from_acc = row.get("從科目")
            to_acc = row.get("到科目")

        if not tx_type_enum:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.INVALID_FORMAT,
                message=f"Unknown transaction type: {type_str}",
                value=type_str,
            )

        if not from_acc:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.MISSING_COLUMN,
                message="Missing source account",
                value="from_account",
            )
        if not to_acc:
            return None, ValidationError(
                row_number=row_number,
                error_type=ValidationErrorType.MISSING_COLUMN,
                message="Missing destination account",
                value="to_account",
            )

        # Parse hierarchical account paths
        from_path = self.parse_hierarchical_account(from_acc)
        to_path = self.parse_hierarchical_account(to_acc)

        tx = ParsedTransaction(
            row_number=row_number,
            date=parsed_date,
            transaction_type=tx_type_enum,
            from_account_name=from_acc,
            to_account_name=to_acc,
            amount=amount,
            description=row.get("明細", ""),
            invoice_number=row.get("發票號碼"),
            from_account_path=from_path,
            to_account_path=to_path,
        )
        return tx, None

    def _parse_date(self, date_str: str) -> date:
        formats = ["%Y/%m/%d", "%Y-%m-%d", "%m/%d/%Y"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Invalid date format: {date_str}")

    @staticmethod
    def parse_account_prefix(account_name: str) -> AccountType | None:
        """
        Parse account type from prefix (A-, L-, I-, E-).
        """
        if account_name.startswith("A-"):
            return AccountType.ASSET
        if account_name.startswith("L-"):
            return AccountType.LIABILITY
        if account_name.startswith("I-"):
            return AccountType.INCOME
        if account_name.startswith("E-"):
            return AccountType.EXPENSE
        return None

    @staticmethod
    def parse_hierarchical_account(account_name: str) -> ParsedAccountPath:
        """
        Parse hierarchical account name into structured path.

        Example: "L-信用卡.國泰世華信用卡.Cube卡" -> ParsedAccountPath(
            account_type=LIABILITY,
            path_segments=["信用卡", "國泰世華信用卡", "Cube卡"],
            raw_name="L-信用卡.國泰世華信用卡.Cube卡"
        )
        """
        account_type = MyAbCsvParser.parse_account_prefix(account_name)

        # Remove prefix (e.g. "L-", "E-")
        name_without_prefix = account_name
        if "-" in account_name and len(account_name) > 2:
            prefix_end = account_name.index("-")
            if prefix_end <= 2:  # Only handle single/double char prefixes like "L-", "E-"
                name_without_prefix = account_name[prefix_end + 1 :]

        # Split by "." to get hierarchy
        path_segments = name_without_prefix.split(".")

        # Filter out empty segments
        path_segments = [seg.strip() for seg in path_segments if seg.strip()]

        return ParsedAccountPath(
            account_type=account_type or AccountType.ASSET,
            path_segments=path_segments,
            raw_name=account_name,
        )


class CreditCardCsvParser(CsvParser):
    """Parser for bank credit card CSV files."""

    # Date values that indicate non-transaction rows (dash variants)
    _SKIP_DATE_VALUES = {"−", "-", "—", "－"}

    def __init__(self, bank_code: str):
        """
        Initialize parser with bank configuration.

        Args:
            bank_code: Bank code (e.g., CATHAY, CTBC)

        Raises:
            ValueError: If bank is not supported
        """
        from src.services.bank_configs import get_bank_config

        self.config = get_bank_config(bank_code)
        if self.config is None:
            raise ValueError(f"Unsupported bank: {bank_code}")

    def _find_data_start_row(self, rows: list[list[str]], config) -> tuple[int, int, int]:
        """
        Locate data start row using header_marker, and extract bill year/month from first row.

        Returns:
            (data_start_idx, bill_year, bill_month)
        """
        today = date.today()
        bill_year = today.year
        bill_month = today.month

        # Try to extract year/month from the first non-empty row
        if config.date_year_pattern and rows:
            first_line = ",".join(rows[0])
            m = re.search(config.date_year_pattern, first_line)
            if m:
                bill_year = int(m.group(1))
                bill_month = int(m.group(2))

        # Dynamically find header row by marker
        if config.header_marker:
            for idx, row in enumerate(rows):
                if any(config.header_marker in cell for cell in row):
                    return idx + 1, bill_year, bill_month

        # Fallback to static skip_rows
        return config.skip_rows, bill_year, bill_month

    def _resolve_year_for_mmdd(self, tx_month: int, bill_year: int, bill_month: int) -> int:
        """
        Infer the full year for a MM/DD date.

        If tx_month > bill_month the transaction occurred in the previous year (cross-year billing).
        """
        if tx_month <= bill_month:
            return bill_year
        return bill_year - 1

    def _is_skip_row(self, row: list[str]) -> bool:
        """Return True if the row should be silently skipped (empty or too short to be data)."""
        return not row or all(cell.strip() == "" for cell in row)

    def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
        """
        Parse credit card CSV file.

        Args:
            file: Binary file object containing CSV data

        Returns:
            Tuple of (List of ParsedTransaction objects, List of ValidationError objects)
        """
        from src.services.category_suggester import CategorySuggester

        if self.config is None:
            raise ValueError("Parser not initialized with valid bank config")

        # Read raw CSV rows
        encoding = self.config.encoding or self.detect_encoding(file)
        file.seek(0)

        try:
            content = file.read().decode(encoding)
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode file with encoding {encoding}: {e}") from e

        # Remove BOM if present
        if content.startswith("\ufeff"):
            content = content[1:]

        f = io.StringIO(content)
        reader = csv.reader(f)
        rows = list(reader)

        # Dynamically locate the data start row (supports real-format bank CSVs)
        data_start, bill_year, bill_month = self._find_data_start_row(rows, self.config)
        data_rows = rows[data_start:]

        needs_year_inference = "%Y" not in self.config.date_format

        # Initialize category suggester
        suggester = CategorySuggester()

        result = []
        errors = []

        for i, row in enumerate(data_rows, start=1):
            try:
                # Skip blank / footer rows silently
                if self._is_skip_row(row):
                    continue

                # Validate row has enough columns
                max_col = max(
                    self.config.date_column,
                    self.config.description_column,
                    self.config.amount_column,
                )
                if len(row) <= max_col:
                    # Rows with insufficient columns are silently skipped (e.g. footer summaries)
                    continue

                date_str = row[self.config.date_column].strip()

                # Skip non-transaction rows where date is a dash variant (e.g. "−", "-")
                if date_str in self._SKIP_DATE_VALUES:
                    continue

                # Parse date
                try:
                    if needs_year_inference:
                        # Parse MM/DD manually to avoid Python 3.15 strptime deprecation
                        # (strptime with year-less format defaults to year 1900)
                        sep = "/" if "/" in date_str else "-"
                        parts = date_str.split(sep)
                        if len(parts) != 2:
                            raise ValueError(f"Expected MM{sep}DD, got: {date_str}")
                        tx_month, tx_day = int(parts[0]), int(parts[1])
                        inferred_year = self._resolve_year_for_mmdd(tx_month, bill_year, bill_month)
                        parsed_date = date(inferred_year, tx_month, tx_day)
                    else:
                        parsed_date = datetime.strptime(date_str, self.config.date_format).date()
                except ValueError:
                    errors.append(
                        ValidationError(
                            row_number=i,
                            error_type=ValidationErrorType.INVALID_DATE,
                            message=f"Invalid date format: {date_str}",
                            value=date_str,
                        )
                    )
                    continue

                # Parse amount
                amount_str = row[self.config.amount_column].strip()
                try:
                    cleaned = amount_str.replace(",", "").replace("$", "").replace("NT", "")
                    amount_decimal = Decimal(cleaned)
                except InvalidOperation:
                    errors.append(
                        ValidationError(
                            row_number=i,
                            error_type=ValidationErrorType.INVALID_AMOUNT,
                            message=f"Invalid amount format: {amount_str}",
                            value=amount_str,
                        )
                    )
                    continue

                # Skip negative amounts (payment / refund rows) if configured
                if self.config.skip_negative_amounts and amount_decimal < 0:
                    continue

                amount = abs(amount_decimal)

                # Parse description
                description = row[self.config.description_column].strip()

                # Get category suggestion
                suggestion = suggester.suggest(description)

                tx = ParsedTransaction(
                    row_number=i,
                    date=parsed_date,
                    transaction_type=TransactionType.EXPENSE,
                    from_account_name=f"信用卡-{self.config.name}",
                    to_account_name=suggestion.suggested_account_name,
                    amount=amount,
                    description=description,
                    category_suggestion=suggestion,
                    from_account_path=ParsedAccountPath(
                        account_type=AccountType.LIABILITY,
                        path_segments=["信用卡", self.config.name],
                        raw_name=f"信用卡-{self.config.name}",
                    ),
                    to_account_path=ParsedAccountPath(
                        account_type=AccountType.EXPENSE,
                        path_segments=[suggestion.suggested_account_name],
                        raw_name=suggestion.suggested_account_name,
                    ),
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


class BankStatementCsvParser(CsvParser):
    """Parser for bank savings/checking account statement CSV files."""

    def __init__(self, bank_code: str):
        """
        Initialize parser with bank statement configuration.

        Args:
            bank_code: Bank code (e.g., CATHAY, CTBC)

        Raises:
            ValueError: If bank is not supported
        """
        from src.services.bank_configs import get_bank_statement_config

        self.config = get_bank_statement_config(bank_code)
        if self.config is None:
            raise ValueError(f"Unsupported bank for statement import: {bank_code}")

    def _find_data_start_row(self, rows: list[list[str]]) -> int:
        """Locate data start row using header_marker, or fall back to skip_rows."""
        if self.config.header_marker:
            for idx, row in enumerate(rows):
                if any(self.config.header_marker in cell for cell in row):
                    return idx + 1
        return self.config.skip_rows

    def _parse_amount(self, raw: str) -> Decimal | None:
        """Parse a raw amount string. Returns None if empty or invalid."""
        cleaned = raw.strip().replace(",", "").replace("$", "").replace("NT", "")
        if not cleaned:
            return None
        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
        """
        Parse bank statement CSV file.

        Returns:
            Tuple of (List of ParsedTransaction objects, List of ValidationError objects)
        """
        from src.services.category_suggester import CategorySuggester

        encoding = self.config.encoding or self.detect_encoding(file)
        file.seek(0)

        try:
            content = file.read().decode(encoding)
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode file with encoding {encoding}: {e}") from e

        if content.startswith("\ufeff"):
            content = content[1:]

        f = io.StringIO(content)
        reader = csv.reader(f)
        rows = list(reader)

        data_start = self._find_data_start_row(rows)
        data_rows = rows[data_start:]

        suggester = CategorySuggester()
        result = []
        errors = []

        for i, row in enumerate(data_rows, start=1):
            try:
                # Skip blank rows
                if not row or all(cell.strip() == "" for cell in row):
                    continue

                # Validate minimum columns
                required_cols = [self.config.date_column, self.config.description_column]
                if self.config.amount_column is not None:
                    required_cols.append(self.config.amount_column)
                elif self.config.debit_column is not None and self.config.credit_column is not None:
                    required_cols += [self.config.debit_column, self.config.credit_column]

                if len(row) <= max(required_cols):
                    continue

                # Parse date
                date_str = row[self.config.date_column].strip()
                if not date_str:
                    continue
                try:
                    parsed_date = datetime.strptime(date_str, self.config.date_format).date()
                except ValueError:
                    errors.append(
                        ValidationError(
                            row_number=i,
                            error_type=ValidationErrorType.INVALID_DATE,
                            message=f"Invalid date format: {date_str}",
                            value=date_str,
                        )
                    )
                    continue

                description = row[self.config.description_column].strip()

                # Determine debit / credit amounts
                if self.config.amount_column is not None:
                    # Signed single-column mode
                    amount_val = self._parse_amount(row[self.config.amount_column])
                    if amount_val is None:
                        continue
                    if amount_val < 0:
                        debit_amount = abs(amount_val)
                        credit_amount = Decimal("0")
                    else:
                        debit_amount = Decimal("0")
                        credit_amount = amount_val
                else:
                    # Dual-column mode: debit + credit
                    debit_raw = (
                        row[self.config.debit_column].strip()
                        if self.config.debit_column is not None
                        else ""
                    )
                    credit_raw = (
                        row[self.config.credit_column].strip()
                        if self.config.credit_column is not None
                        else ""
                    )
                    debit_amount = self._parse_amount(debit_raw) or Decimal("0")
                    credit_amount = self._parse_amount(credit_raw) or Decimal("0")

                # Skip rows with no movement (e.g., balance summary rows)
                if debit_amount == 0 and credit_amount == 0:
                    continue

                bank_account_path = ParsedAccountPath(
                    account_type=AccountType.ASSET,
                    path_segments=self.config.bank_account_name.split("."),
                    raw_name=self.config.bank_account_name,
                )

                if debit_amount > 0:
                    # Out-flow: EXPENSE — from bank account → expense category
                    suggestion = suggester.suggest(description)
                    tx = ParsedTransaction(
                        row_number=i,
                        date=parsed_date,
                        transaction_type=TransactionType.EXPENSE,
                        from_account_name=self.config.bank_account_name,
                        to_account_name=suggestion.suggested_account_name,
                        amount=debit_amount,
                        description=description,
                        category_suggestion=suggestion,
                        from_account_path=bank_account_path,
                        to_account_path=ParsedAccountPath(
                            account_type=AccountType.EXPENSE,
                            path_segments=[suggestion.suggested_account_name],
                            raw_name=suggestion.suggested_account_name,
                        ),
                    )
                    result.append(tx)

                if credit_amount > 0:
                    # In-flow: INCOME — from income category → bank account
                    tx = ParsedTransaction(
                        row_number=i,
                        date=parsed_date,
                        transaction_type=TransactionType.INCOME,
                        from_account_name="其他收入",
                        to_account_name=self.config.bank_account_name,
                        amount=credit_amount,
                        description=description,
                        from_account_path=ParsedAccountPath(
                            account_type=AccountType.INCOME,
                            path_segments=["其他收入"],
                            raw_name="其他收入",
                        ),
                        to_account_path=bank_account_path,
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
