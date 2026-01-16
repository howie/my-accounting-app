import csv
import io
import os
from collections.abc import Generator
from datetime import datetime
from enum import Enum
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.models.account import Account
from src.models.transaction import Transaction, TransactionType


class ExportFormat(str, Enum):
    CSV = "csv"
    HTML = "html"


class ExportService:
    def __init__(self, session: Any):
        self.session = session
        # Setup Jinja2 env - assume templates folder is relative to this file or project root
        # Ideally passed in via config, but we'll infer for now: src/templates
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_dir = os.path.join(base_dir, "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir), autoescape=select_autoescape(["html", "xml"])
        )

    def generate_csv_content(
        self,
        transactions: list[Transaction],
    ) -> Generator[str, None, None]:
        """Generate CSV content from transactions."""
        # Yield BOM for Excel compatibility
        yield "\ufeff"

        # CSV Header
        header = [
            "日期",
            "交易類型",
            "支出科目",
            "收入科目",
            "從科目",
            "到科目",
            "金額",
            "明細",
            "發票號碼",
        ]

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(header)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        for txn in transactions:
            row = self._map_transaction_to_csv_row(txn)
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    def _map_transaction_to_csv_row(self, txn: Transaction) -> list[str]:
        # Helper to safely get account name
        def get_account_name(account: Account | None) -> str:
            return account.name if account else ""

        date_str = txn.date.isoformat()
        amount_str = str(txn.amount)
        description = txn.description or ""
        invoice_no = (
            ""  # Invoice No not yet in Transaction model, leave empty or assume future field
        )

        # Initialize columns
        txn_type = ""
        expense_acc = ""
        income_acc = ""
        from_acc = ""
        to_acc = ""

        # Map types based on research.md spec
        # Assuming txn.from_account and txn.to_account are loaded/joined (lazy loading might trigger here)
        # In a real service we need to ensure these are available.
        # For this implementation we assume they are accessible properties.

        if txn.transaction_type == TransactionType.EXPENSE:
            txn_type = "支出"
            # Expense: From Asset -> To Expense
            expense_acc = get_account_name(txn.to_account)
            from_acc = get_account_name(txn.from_account)

        elif txn.transaction_type == TransactionType.INCOME:
            txn_type = "收入"
            # Income: From Income -> To Asset
            income_acc = get_account_name(txn.from_account)
            to_acc = get_account_name(txn.to_account)

        elif txn.transaction_type == TransactionType.TRANSFER:
            txn_type = "轉帳"
            # Transfer: From Asset -> To Asset
            from_acc = get_account_name(txn.from_account)
            to_acc = get_account_name(txn.to_account)

        return [
            date_str,
            txn_type,
            expense_acc,
            income_acc,
            from_acc,
            to_acc,
            amount_str,
            description,
            invoice_no,
        ]

    def generate_html_content(
        self, transactions: list[Transaction], date_range_str: str, account_name: str | None = None
    ) -> str:
        """Generate HTML content from transactions."""
        template = self.jinja_env.get_template("export_report.html")

        # Prepare view models
        txn_views = []
        for txn in transactions:
            type_label = "Unknown"
            if txn.transaction_type == TransactionType.EXPENSE:
                type_label = "Expense"
            elif txn.transaction_type == TransactionType.INCOME:
                type_label = "Income"
            elif txn.transaction_type == TransactionType.TRANSFER:
                type_label = "Transfer"

            txn_views.append(
                {
                    "date": txn.date.isoformat(),
                    "type_raw": txn.transaction_type.value if txn.transaction_type else "EXPENSE",
                    "type_label": type_label,
                    "source_label": txn.from_account.name if txn.from_account else "-",
                    "target_label": txn.to_account.name if txn.to_account else "-",
                    "description": txn.description or "",
                    "amount": f"{txn.amount:,.2f}",
                }
            )

        return template.render(
            date_range=date_range_str,
            account_filter=account_name,
            generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            transactions=txn_views,
        )
