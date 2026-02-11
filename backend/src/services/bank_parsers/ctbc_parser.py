"""CTBC Bank (中國信託) credit card statement parser.

Password format: Last 4 digits of ID + birth MMDD (e.g., 12340520)
Email sender: noreply@ctbcbank.com
Subject contains: 信用卡電子帳單
"""

import re
from datetime import date
from decimal import Decimal

from src.services.bank_parsers import register_parser
from src.services.bank_parsers.base import BankStatementParser, ParsedStatementTransaction
from src.services.pdf_parser import PdfContent


@register_parser
class CtbcParser(BankStatementParser):
    """Parser for CTBC Bank credit card statements."""

    bank_code = "CTBC"
    bank_name = "中國信託"
    email_query = "from:noreply@ctbcbank.com subject:信用卡電子帳單"
    password_hint = "身分證末4碼 + 生日MMDD（例：12340520）"

    def parse_statement(self, pdf_content: PdfContent) -> list[ParsedStatementTransaction]:
        """Parse CTBC credit card statement.

        CTBC statements typically have:
        - Transaction date, posting date
        - Merchant name
        - Amount (positive for charges, negative for credits)
        - Currency for foreign transactions
        """
        transactions = []

        # Try to extract from tables first
        for table in pdf_content.all_tables:
            transactions.extend(self._parse_table(table))

        # If no transactions from tables, try text parsing
        if not transactions:
            transactions = self._parse_text(pdf_content.full_text)

        return transactions

    def _parse_table(self, table: list[list[str]]) -> list[ParsedStatementTransaction]:
        """Parse transactions from a table."""
        transactions = []

        # Find header row to determine column positions
        header_row = -1
        date_col = -1
        desc_col = -1
        amount_col = -1

        for i, row in enumerate(table):
            row_text = " ".join(str(cell).lower() for cell in row)
            if "交易日" in row_text or "消費日" in row_text:
                header_row = i
                for j, cell in enumerate(row):
                    cell_text = str(cell).strip()
                    if "交易日" in cell_text or "消費日" in cell_text:
                        date_col = j
                    elif "說明" in cell_text or "摘要" in cell_text or "交易" in cell_text:
                        desc_col = j
                    elif "金額" in cell_text or "臺幣" in cell_text or "台幣" in cell_text:
                        amount_col = j
                break

        if header_row == -1 or date_col == -1 or amount_col == -1:
            return []

        # Parse data rows
        for row in table[header_row + 1 :]:
            if len(row) <= max(date_col, desc_col if desc_col >= 0 else 0, amount_col):
                continue

            try:
                # Parse date
                date_str = str(row[date_col]).strip()
                tx_date = self._parse_date(date_str)
                if not tx_date:
                    continue

                # Parse description
                description = ""
                if desc_col >= 0:
                    description = str(row[desc_col]).strip()
                else:
                    # Try to find description in other columns
                    for j, cell in enumerate(row):
                        if j not in (date_col, amount_col):
                            cell_text = str(cell).strip()
                            if len(cell_text) > len(description):
                                description = cell_text

                if not description:
                    continue

                # Parse amount
                amount_str = str(row[amount_col]).strip()
                amount = self._parse_amount(amount_str)
                if amount is None:
                    continue

                transactions.append(
                    ParsedStatementTransaction(
                        date=tx_date,
                        merchant_name=description,
                        amount=amount,
                        currency="TWD",
                        category_suggestion=self._suggest_category(description),
                        confidence=0.8,
                    )
                )
            except (ValueError, IndexError):
                continue

        return transactions

    def _parse_text(self, text: str) -> list[ParsedStatementTransaction]:
        """Parse transactions from raw text using regex."""
        transactions = []

        # Pattern for CTBC statement lines:
        # Date (MM/DD or YYYY/MM/DD) | Description | Amount
        patterns = [
            # MM/DD format with amount
            r"(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+(?:\.\d{2})?)\s*$",
            # YYYY/MM/DD format
            r"(\d{4}/\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+(?:\.\d{2})?)\s*$",
        ]

        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue

            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    date_str = match.group(1)
                    description = match.group(2).strip()
                    amount_str = match.group(3)

                    tx_date = self._parse_date(date_str)
                    amount = self._parse_amount(amount_str)

                    if tx_date and amount is not None and description:
                        transactions.append(
                            ParsedStatementTransaction(
                                date=tx_date,
                                merchant_name=description,
                                amount=amount,
                                currency="TWD",
                                category_suggestion=self._suggest_category(description),
                                confidence=0.6,
                            )
                        )
                    break

        return transactions

    def _parse_date(self, date_str: str) -> date | None:
        """Parse date string to date object."""
        date_str = date_str.strip()

        # Try MM/DD format (assume current year)
        match = re.match(r"^(\d{1,2})/(\d{1,2})$", date_str)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            try:
                return date(date.today().year, month, day)
            except ValueError:
                return None

        # Try YYYY/MM/DD format
        match = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", date_str)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day)
            except ValueError:
                return None

        # Try ROC year format (民國年)
        match = re.match(r"^(\d{2,3})/(\d{1,2})/(\d{1,2})$", date_str)
        if match:
            roc_year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            year = roc_year + 1911  # Convert ROC year to AD
            try:
                return date(year, month, day)
            except ValueError:
                return None

        return None

    def _parse_amount(self, amount_str: str) -> Decimal | None:
        """Parse amount string to Decimal."""
        # Remove currency symbols, commas, and whitespace
        cleaned = re.sub(r"[NT$,\s]", "", amount_str)

        # Handle negative amounts (credits)
        is_negative = "-" in cleaned or "CR" in amount_str.upper()
        cleaned = cleaned.replace("-", "")

        try:
            amount = Decimal(cleaned)
            return -amount if is_negative else amount
        except Exception:
            return None

    def _suggest_category(self, description: str) -> str | None:
        """Suggest expense category based on merchant description."""
        desc_lower = description.lower()

        # Food & Dining
        if any(
            kw in desc_lower
            for kw in ["餐", "食", "cafe", "coffee", "starbucks", "麥當勞", "全聯", "超市", "7-11"]
        ):
            return "餐飲"

        # Transportation
        if any(
            kw in desc_lower for kw in ["台鐵", "高鐵", "捷運", "uber", "計程車", "停車", "加油"]
        ):
            return "交通"

        # Shopping
        if any(kw in desc_lower for kw in ["百貨", "購物", "蝦皮", "momo", "pchome", "amazon"]):
            return "購物"

        # Entertainment
        if any(kw in desc_lower for kw in ["電影", "ktv", "遊戲", "netflix", "spotify"]):
            return "娛樂"

        # Utilities
        if any(kw in desc_lower for kw in ["電費", "水費", "瓦斯", "電信", "網路"]):
            return "水電瓦斯"

        return None

    def extract_billing_period(self, pdf_content: PdfContent) -> tuple[date | None, date | None]:
        """Extract billing period from statement."""
        text = pdf_content.full_text

        # Look for billing period patterns
        patterns = [
            r"帳單週期[：:]\s*(\d{4}/\d{1,2}/\d{1,2})\s*[~至-]\s*(\d{4}/\d{1,2}/\d{1,2})",
            r"(\d{4}/\d{1,2}/\d{1,2})\s*[~至-]\s*(\d{4}/\d{1,2}/\d{1,2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                start = self._parse_date(match.group(1))
                end = self._parse_date(match.group(2))
                if start and end:
                    return start, end

        return None, None
