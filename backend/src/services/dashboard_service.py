"""Dashboard service for aggregating financial data.

Based on contracts/dashboard_service.md for feature 002-ui-layout-dashboard.
Provides read-only aggregation endpoints for dashboard and sidebar.
"""

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlmodel import Session, func, select

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.transaction import Transaction, TransactionType


class DashboardService:
    """Service for dashboard data aggregation.

    All methods are read-only and do not modify data.
    """

    def __init__(self, session: Session) -> None:
        """Initialize service with database session."""
        self.session = session

    def get_dashboard_summary(
        self, ledger_id: uuid.UUID
    ) -> dict:
        """Get aggregated dashboard data.

        Returns:
            dict with total_assets, current_month, and trends

        Raises:
            ValueError: If ledger doesn't exist
        """
        # Verify ledger exists
        ledger = self.session.get(Ledger, ledger_id)
        if not ledger:
            raise ValueError(f"Ledger not found: {ledger_id}")

        # Calculate total assets
        total_assets = self._calculate_total_assets(ledger_id)

        # Get current month data
        current_month = self._get_current_month_summary(ledger_id)

        # Get 6-month trends
        trends = self._get_monthly_trends(ledger_id)

        return {
            "total_assets": total_assets,
            "current_month": current_month,
            "trends": trends,
        }

    def get_accounts_by_category(
        self, ledger_id: uuid.UUID
    ) -> dict:
        """Get all accounts grouped by category type with tree structure.

        Returns:
            dict with categories list, each containing type and accounts (tree)

        Raises:
            ValueError: If ledger doesn't exist
        """
        # Verify ledger exists
        ledger = self.session.get(Ledger, ledger_id)
        if not ledger:
            raise ValueError(f"Ledger not found: {ledger_id}")

        # Define category order
        category_order = [
            AccountType.ASSET,
            AccountType.LIABILITY,
            AccountType.INCOME,
            AccountType.EXPENSE,
        ]

        categories = []
        for account_type in category_order:
            # Get all accounts for this type
            accounts = self.session.exec(
                select(Account)
                .where(Account.ledger_id == ledger_id)
                .where(Account.type == account_type)
                .order_by(Account.name)
            ).all()

            # Build tree structure
            account_tree = self._build_account_tree(accounts)

            categories.append({
                "type": account_type.value,
                "accounts": account_tree,
            })

        return {"categories": categories}

    def _build_account_tree(self, accounts: list[Account]) -> list[dict]:
        """Build hierarchical tree from flat account list."""
        # Create lookup dict
        account_dict = {}
        for account in accounts:
            account_dict[account.id] = {
                "id": str(account.id),
                "name": account.name,
                "balance": float(self._calculate_account_balance(account)),
                "parent_id": str(account.parent_id) if account.parent_id else None,
                "depth": account.depth,
                "children": [],
            }

        # Build tree
        root_accounts = []
        for account in accounts:
            node = account_dict[account.id]
            if account.parent_id and account.parent_id in account_dict:
                # Add as child
                account_dict[account.parent_id]["children"].append(node)
            else:
                # Root level account
                root_accounts.append(node)

        return root_accounts

    def get_account_transactions(
        self,
        account_id: uuid.UUID,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """Get paginated transactions for an account.

        Args:
            account_id: The account UUID
            page: Page number (1-indexed)
            page_size: Items per page (max 100)

        Returns:
            dict with account info, transactions, and pagination data

        Raises:
            ValueError: If account doesn't exist or invalid pagination
        """
        # Validate pagination
        if page < 1:
            raise ValueError("Page number must be >= 1")
        if page_size < 1 or page_size > 100:
            raise ValueError("Page size must be between 1 and 100")

        # Get account
        account = self.session.get(Account, account_id)
        if not account:
            raise ValueError(f"Account not found: {account_id}")

        # Count total transactions for this account
        total_count = self.session.exec(
            select(func.count(Transaction.id)).where(
                (Transaction.from_account_id == account_id)
                | (Transaction.to_account_id == account_id)
            )
        ).one()

        # Calculate offset
        offset = (page - 1) * page_size

        # Get transactions for this page
        transactions = self.session.exec(
            select(Transaction)
            .where(
                (Transaction.from_account_id == account_id)
                | (Transaction.to_account_id == account_id)
            )
            .order_by(Transaction.date.desc(), Transaction.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).all()

        # Transform transactions with other account name
        transaction_list = []
        for txn in transactions:
            # Determine the other account
            if txn.from_account_id == account_id:
                other_account = self.session.get(Account, txn.to_account_id)
            else:
                other_account = self.session.get(Account, txn.from_account_id)

            transaction_list.append({
                "id": str(txn.id),
                "date": txn.date.isoformat(),
                "description": txn.description,
                "amount": float(txn.amount),
                "type": txn.transaction_type.value,
                "other_account_name": other_account.name if other_account else "Unknown",
            })

        has_more = (offset + len(transactions)) < total_count

        return {
            "account_id": str(account_id),
            "account_name": account.name,
            "transactions": transaction_list,
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "has_more": has_more,
        }

    def _calculate_total_assets(self, ledger_id: uuid.UUID) -> Decimal:
        """Calculate sum of all ASSET account balances."""
        # Get all asset accounts
        accounts = self.session.exec(
            select(Account)
            .where(Account.ledger_id == ledger_id)
            .where(Account.type == AccountType.ASSET)
        ).all()

        total = Decimal("0")
        for account in accounts:
            total += self._calculate_account_balance(account)

        return total

    def _calculate_account_balance(self, account: Account) -> Decimal:
        """Calculate balance for a single account from transactions.

        For Asset: SUM(incoming) - SUM(outgoing)
        For Liability: SUM(outgoing) - SUM(incoming)
        For Income: SUM(outgoing)
        For Expense: SUM(incoming)
        """
        # Get incoming sum (to this account)
        incoming_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
            .where(Transaction.to_account_id == account.id)
        ).one()
        incoming = Decimal(str(incoming_result)) if incoming_result else Decimal("0")

        # Get outgoing sum (from this account)
        outgoing_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
            .where(Transaction.from_account_id == account.id)
        ).one()
        outgoing = Decimal(str(outgoing_result)) if outgoing_result else Decimal("0")

        if account.type == AccountType.ASSET:
            return incoming - outgoing
        elif account.type == AccountType.LIABILITY:
            return outgoing - incoming
        elif account.type == AccountType.INCOME:
            return outgoing
        else:  # EXPENSE
            return incoming

    def _get_current_month_summary(self, ledger_id: uuid.UUID) -> dict:
        """Get income and expenses for current month."""
        today = date.today()
        first_day = today.replace(day=1)
        # Last day of month
        if today.month == 12:
            last_day = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            last_day = today.replace(month=today.month + 1, day=1) - timedelta(days=1)

        # Sum income transactions
        income_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
            .where(Transaction.ledger_id == ledger_id)
            .where(Transaction.transaction_type == TransactionType.INCOME)
            .where(Transaction.date >= first_day)
            .where(Transaction.date <= last_day)
        ).one()
        income = Decimal(str(income_result)) if income_result else Decimal("0")

        # Sum expense transactions
        expense_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
            .where(Transaction.ledger_id == ledger_id)
            .where(Transaction.transaction_type == TransactionType.EXPENSE)
            .where(Transaction.date >= first_day)
            .where(Transaction.date <= last_day)
        ).one()
        expenses = Decimal(str(expense_result)) if expense_result else Decimal("0")

        return {
            "income": float(income),
            "expenses": float(expenses),
            "net_cash_flow": float(income - expenses),
        }

    def _get_monthly_trends(self, ledger_id: uuid.UUID, months: int = 6) -> list[dict]:
        """Get income and expense totals for the last N months."""
        today = date.today()
        trends = []

        for i in range(months - 1, -1, -1):
            # Calculate the month to query
            year = today.year
            month = today.month - i
            while month <= 0:
                month += 12
                year -= 1

            first_day = date(year, month, 1)
            if month == 12:
                last_day = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                last_day = date(year, month + 1, 1) - timedelta(days=1)

            # Sum income
            income_result = self.session.exec(
                select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
                .where(Transaction.ledger_id == ledger_id)
                .where(Transaction.transaction_type == TransactionType.INCOME)
                .where(Transaction.date >= first_day)
                .where(Transaction.date <= last_day)
            ).one()
            income = Decimal(str(income_result)) if income_result else Decimal("0")

            # Sum expenses
            expense_result = self.session.exec(
                select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
                .where(Transaction.ledger_id == ledger_id)
                .where(Transaction.transaction_type == TransactionType.EXPENSE)
                .where(Transaction.date >= first_day)
                .where(Transaction.date <= last_day)
            ).one()
            expenses = Decimal(str(expense_result)) if expense_result else Decimal("0")

            # Month name abbreviation
            month_name = first_day.strftime("%b")

            trends.append({
                "month": month_name,
                "year": year,
                "income": float(income),
                "expenses": float(expenses),
            })

        return trends
