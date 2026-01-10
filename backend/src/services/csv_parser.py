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


from datetime import datetime
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

    def _parse_date(self, date_str: str) -> datetime.date:
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
