"""Taipei Fubon Bank (台北富邦) credit card statement parser.

Password format: Birth date YYYYMMDD (e.g., 19900520)
Email sender: service@fubon.com
Subject contains: 信用卡電子帳單
"""

import re
from datetime import date
from decimal import Decimal

from src.services.bank_parsers import register_parser
from src.services.bank_parsers.base import BankStatementParser, ParsedStatementTransaction
from src.services.pdf_parser import PdfContent


@register_parser
class FubonParser(BankStatementParser):
    """Parser for Taipei Fubon Bank credit card statements."""

    bank_code = "FUBON"
    bank_name = "台北富邦"
    email_query = "from:service@fubon.com subject:信用卡電子帳單"
    password_hint = "出生年月日 YYYYMMDD（例：19900520）"

    def parse_statement(self, pdf_content: PdfContent) -> list[ParsedStatementTransaction]:
        """Parse Fubon credit card statement."""
        transactions = []

        for table in pdf_content.all_tables:
            transactions.extend(self._parse_table(table))

        if not transactions:
            transactions = self._parse_text(pdf_content.full_text)

        return transactions

    def _parse_table(self, table: list[list[str]]) -> list[ParsedStatementTransaction]:
        """Parse transactions from a table."""
        transactions = []

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
                    elif "說明" in cell_text or "摘要" in cell_text:
                        desc_col = j
                    elif "金額" in cell_text or "臺幣" in cell_text:
                        amount_col = j
                break

        if header_row == -1 or date_col == -1 or amount_col == -1:
            return []

        for row in table[header_row + 1 :]:
            if len(row) <= max(date_col, desc_col if desc_col >= 0 else 0, amount_col):
                continue

            try:
                date_str = str(row[date_col]).strip()
                tx_date = self._parse_date(date_str)
                if not tx_date:
                    continue

                description = ""
                if desc_col >= 0:
                    description = str(row[desc_col]).strip()
                else:
                    for j, cell in enumerate(row):
                        if j not in (date_col, amount_col):
                            cell_text = str(cell).strip()
                            if len(cell_text) > len(description):
                                description = cell_text

                if not description:
                    continue

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
        """Parse transactions from raw text."""
        transactions = []

        patterns = [
            r"(\d{1,2}/\d{1,2})\s+(.+?)\s+([\d,]+(?:\.\d{2})?)\s*$",
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

        match = re.match(r"^(\d{1,2})/(\d{1,2})$", date_str)
        if match:
            month, day = int(match.group(1)), int(match.group(2))
            try:
                return date(date.today().year, month, day)
            except ValueError:
                return None

        match = re.match(r"^(\d{4})/(\d{1,2})/(\d{1,2})$", date_str)
        if match:
            year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))
            try:
                return date(year, month, day)
            except ValueError:
                return None

        return None

    def _parse_amount(self, amount_str: str) -> Decimal | None:
        """Parse amount string to Decimal."""
        cleaned = re.sub(r"[NT$,\s]", "", amount_str)
        is_negative = "-" in cleaned or "CR" in amount_str.upper()
        cleaned = cleaned.replace("-", "")

        try:
            amount = Decimal(cleaned)
            return -amount if is_negative else amount
        except Exception:
            return None

    def _suggest_category(self, description: str) -> str | None:
        """Suggest expense category."""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["餐", "食", "cafe", "starbucks", "超市"]):
            return "餐飲"
        if any(kw in desc_lower for kw in ["高鐵", "捷運", "uber", "停車", "加油"]):
            return "交通"
        if any(kw in desc_lower for kw in ["百貨", "購物", "蝦皮", "momo"]):
            return "購物"
        if any(kw in desc_lower for kw in ["電影", "netflix", "spotify"]):
            return "娛樂"

        return None

    def extract_billing_period(self, pdf_content: PdfContent) -> tuple[date | None, date | None]:
        """Extract billing period from statement."""
        text = pdf_content.full_text

        patterns = [
            r"帳單週期[：:]\s*(\d{4}/\d{1,2}/\d{1,2})\s*[~至-]\s*(\d{4}/\d{1,2}/\d{1,2})",
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                start = self._parse_date(match.group(1))
                end = self._parse_date(match.group(2))
                if start and end:
                    return start, end

        return None, None
