from __future__ import annotations

import csv
import io
from typing import TYPE_CHECKING, BinaryIO

import charset_normalizer

if TYPE_CHECKING:
    from src.services.bank_configs import BankRecordCsvConfig


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


from datetime import date, datetime
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

    def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
        """
        Parse credit card CSV file.

        Args:
            file: Binary file object containing CSV data

        Returns:
            Tuple of (List of ParsedTransaction objects, List of ValidationError objects)
        """
        from src.services.category_suggester import CategorySuggester

        # Ensure config is present (init validatio should guarantee this, but for types)
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

        # Skip header rows
        data_rows = rows[self.config.skip_rows :]

        # Initialize category suggester
        suggester = CategorySuggester()

        result = []
        errors = []

        for i, row in enumerate(data_rows, start=1):
            try:
                # Validate row has enough columns
                max_col = max(
                    self.config.date_column,
                    self.config.description_column,
                    self.config.amount_column,
                )
                if len(row) <= max_col:
                    errors.append(
                        ValidationError(
                            row_number=i,
                            error_type=ValidationErrorType.MISSING_COLUMN,
                            message=f"Row {i} has insufficient columns",
                            value=str(row),
                        )
                    )
                    continue

                # Parse date
                date_str = row[self.config.date_column].strip()
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

                # Parse description
                description = row[self.config.description_column].strip()

                # Parse amount
                amount_str = row[self.config.amount_column].strip()
                try:
                    # Remove thousand separators and handle negative amounts
                    amount_str = amount_str.replace(",", "").replace("$", "").replace("NT", "")
                    amount = abs(Decimal(amount_str))
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

                # Get category suggestion
                suggestion = suggester.suggest(description)

                # Create transaction
                # For credit card: from_account = credit card (LIABILITY)
                # to_account = expense category (EXPENSE)
                tx = ParsedTransaction(
                    row_number=i,
                    date=parsed_date,
                    transaction_type=TransactionType.EXPENSE,
                    from_account_name=f"信用卡-{self.config.name}",  # Will be mapped later
                    to_account_name=suggestion.suggested_account_name,
                    amount=amount,
                    description=description,
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


class BankRecordCsvParser(CsvParser):
    """Parser for bank account transaction CSV files.

    Handles two amount formats:
    - Dual-column: separate withdrawal (提出) and deposit (存入) columns
    - Single-column: signed amount (negative = withdrawal, positive = deposit)
    """

    def __init__(self, bank_code: str):
        """
        Initialize parser with bank record configuration.

        Args:
            bank_code: Bank code (e.g., CATHAY_BANK, CTBC_BANK)

        Raises:
            ValueError: If bank is not supported
        """
        from src.services.bank_configs import get_bank_record_config

        self.config: BankRecordCsvConfig | None = get_bank_record_config(bank_code)
        if self.config is None:
            raise ValueError(f"Unsupported bank for bank record import: {bank_code}")

    def parse(self, file: BinaryIO) -> tuple[list[ParsedTransaction], list[ValidationError]]:
        """
        Parse bank record CSV file.

        Args:
            file: Binary file object containing CSV data

        Returns:
            Tuple of (List of ParsedTransaction objects, List of ValidationError objects)
        """
        from src.services.category_suggester import CategorySuggester

        config = self.config
        if config is None:
            raise ValueError("Parser not initialized with valid bank config")

        # Use configured encoding or detect
        encoding = config.encoding or self.detect_encoding(file)
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

        # Skip header rows
        data_rows = rows[config.skip_rows :]

        # Initialize category suggester
        suggester = CategorySuggester()

        result = []
        errors = []
        bank_account_name = f"銀行帳戶-{config.name}"

        for i, row in enumerate(data_rows, start=1):
            try:
                # Determine required max column
                required_cols = [config.date_column, config.description_column]
                if config.withdrawal_column is not None:
                    required_cols.append(config.withdrawal_column)
                if config.deposit_column is not None:
                    required_cols.append(config.deposit_column)
                if config.amount_column is not None:
                    required_cols.append(config.amount_column)
                max_col = max(required_cols)

                if len(row) <= max_col:
                    # Skip empty/short rows silently (common in bank CSVs)
                    continue

                # Parse date
                date_str = row[config.date_column].strip()
                if not date_str:
                    continue  # Skip rows with empty dates (summary rows)

                try:
                    parsed_date = datetime.strptime(date_str, config.date_format).date()
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

                # Parse description
                description = row[config.description_column].strip()

                # Parse memo if available
                memo = ""
                if config.memo_column is not None and len(row) > config.memo_column:
                    memo = row[config.memo_column].strip()

                full_description = f"{description} - {memo}" if memo else description

                # Parse amount and determine transaction type
                tx_type, amount = self._parse_amount(row, config)

                if amount is None or amount == Decimal("0"):
                    continue  # Skip zero-amount rows

                # Build transaction based on type
                if tx_type == TransactionType.EXPENSE:
                    # Withdrawal: from bank account to expense category
                    suggestion = suggester.suggest(full_description)
                    tx = ParsedTransaction(
                        row_number=i,
                        date=parsed_date,
                        transaction_type=TransactionType.EXPENSE,
                        from_account_name=bank_account_name,
                        to_account_name=suggestion.suggested_account_name,
                        amount=amount,
                        description=full_description,
                        category_suggestion=suggestion,
                    )
                elif tx_type == TransactionType.INCOME:
                    # Deposit: from income source to bank account
                    suggestion = suggester.suggest_income(full_description)
                    tx = ParsedTransaction(
                        row_number=i,
                        date=parsed_date,
                        transaction_type=TransactionType.INCOME,
                        from_account_name=suggestion.suggested_account_name,
                        to_account_name=bank_account_name,
                        amount=amount,
                        description=full_description,
                        category_suggestion=suggestion,
                    )
                else:
                    continue  # Should not happen

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

    @staticmethod
    def _parse_amount(
        row: list[str], config: BankRecordCsvConfig
    ) -> tuple[TransactionType | None, Decimal | None]:
        """Parse amount from row, returning (transaction_type, abs_amount).

        Handles two modes:
        - Dual column: withdrawal_column and deposit_column
        - Single column: amount_column (negative=withdrawal, positive=deposit)
        """

        def clean_amount(s: str) -> Decimal | None:
            s = s.strip().replace(",", "").replace("$", "").replace("NT", "")
            # Handle Unicode MINUS SIGN (U+2212) used by some banks (e.g., Cathay) for empty
            if not s or s == "−" or s == "-":
                return None
            try:
                return Decimal(s)
            except InvalidOperation:
                return None

        if config.withdrawal_column is not None and config.deposit_column is not None:
            # Mode A: dual columns
            withdrawal = clean_amount(row[config.withdrawal_column])
            deposit = clean_amount(row[config.deposit_column])

            if withdrawal and withdrawal > 0:
                return TransactionType.EXPENSE, withdrawal
            elif deposit and deposit > 0:
                return TransactionType.INCOME, deposit
            else:
                return None, None

        elif config.amount_column is not None:
            # Mode B: single signed column
            amount = clean_amount(row[config.amount_column])
            if amount is None:
                return None, None
            if amount < 0:
                return TransactionType.EXPENSE, abs(amount)
            elif amount > 0:
                return TransactionType.INCOME, amount
            else:
                return None, None

        return None, None
