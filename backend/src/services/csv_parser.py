import csv
import io
from typing import BinaryIO


class CsvParser:
    @staticmethod
    def detect_encoding(file: BinaryIO) -> str:
        """
        Detect encoding of the file.
        Prioritizes UTF-8, then Big5 (common in TW).
        """
        start_pos = file.tell()
        content = file.read(4096)
        file.seek(start_pos)

        # Try UTF-8
        try:
            content.decode("utf-8")
            return "utf-8"
        except UnicodeDecodeError:
            pass

        # Try Big5
        try:
            content.decode("big5")
            return "big5"
        except UnicodeDecodeError:
            pass

        # Default fallback
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

from src.schemas.data_import import AccountType, ParsedTransaction, TransactionType


class MyAbCsvParser(CsvParser):
    def parse(self, file: BinaryIO) -> list[ParsedTransaction]:
        rows = self.read_csv(file)
        result = []

        for i, row in enumerate(rows, start=1):  # 1-based row number
            try:
                # Validate required columns presence using first row logic check?
                # or just get and fail if None later.

                date_str = row.get("日期")
                type_str = row.get("交易類型")
                amount_str = row.get("金額")

                if not date_str or not type_str or not amount_str:
                    # Should verify if this is an empty line or handle error
                    # For now raise error
                    raise ValueError(f"Missing required fields in row {i}")

                # Parse Date
                parsed_date = self._parse_date(date_str)

                # Parse Amount
                try:
                    amount = Decimal(amount_str.replace(",", ""))
                except InvalidOperation as e:
                    raise ValueError(f"Invalid amount format: {amount_str}") from e

                # Determine Transaction Type and Accounts
                tx_type_enum = None
                from_acc = None
                to_acc = None

                if type_str == "支出":
                    tx_type_enum = TransactionType.EXPENSE
                    from_acc = row.get("從科目")
                    to_acc = row.get("支出科目")
                elif type_str == "收入":
                    tx_type_enum = TransactionType.INCOME
                    from_acc = row.get("收入科目")
                    to_acc = row.get("到科目")
                elif type_str == "轉帳":
                    tx_type_enum = TransactionType.TRANSFER
                    from_acc = row.get("從科目")
                    to_acc = row.get("到科目")
                else:
                    # Fallback or error?
                    # Let's assume Transfer if unknown, or raise error.
                    # Spec doesn't specify other types.
                    pass

                if not tx_type_enum:
                    raise ValueError(f"Unknown transaction type: {type_str}")

                if not from_acc:
                    raise ValueError("Missing from_account")
                if not to_acc:
                    raise ValueError("Missing to_account")

                tx = ParsedTransaction(
                    row_number=i,
                    date=parsed_date,
                    transaction_type=tx_type_enum,
                    from_account_name=from_acc,
                    to_account_name=to_acc,
                    amount=amount,
                    description=row.get("明細", ""),
                    invoice_number=row.get("發票號碼"),
                )
                result.append(tx)

            except ValueError as e:
                # In a real app, we might collect errors and return them in result
                # But here we raise them as per current test expectation validation
                raise e
            except Exception as e:
                raise ValueError(f"Error parsing row {i}: {e}") from e

        return result

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

    def parse(self, file: BinaryIO) -> list[ParsedTransaction]:
        """
        Parse credit card CSV file.

        Args:
            file: Binary file object containing CSV data

        Returns:
            List of ParsedTransaction objects
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
        for i, row in enumerate(data_rows, start=1):
            try:
                # Validate row has enough columns
                max_col = max(
                    self.config.date_column,
                    self.config.description_column,
                    self.config.amount_column,
                )
                if len(row) <= max_col:
                    raise ValueError(f"Row {i} has insufficient columns")

                # Parse date
                date_str = row[self.config.date_column].strip()
                try:
                    parsed_date = datetime.strptime(date_str, self.config.date_format).date()
                except ValueError as e:
                    raise ValueError(f"Invalid date format in row {i}: {date_str}") from e

                # Parse description
                description = row[self.config.description_column].strip()

                # Parse amount
                amount_str = row[self.config.amount_column].strip()
                try:
                    # Remove thousand separators and handle negative amounts
                    amount_str = amount_str.replace(",", "").replace("$", "").replace("NT", "")
                    amount = abs(Decimal(amount_str))
                except InvalidOperation as e:
                    raise ValueError(f"Invalid amount format in row {i}: {amount_str}") from e

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

            except ValueError:
                raise
            except Exception as e:
                raise ValueError(f"Error parsing row {i}: {e}") from e

        return result
