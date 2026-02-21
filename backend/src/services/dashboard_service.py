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
        self,
        ledger_id: uuid.UUID,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> dict:
        """Get aggregated dashboard data.

        Args:
            ledger_id: The ledger UUID
            start_date: Optional start date for summary and trends
            end_date: Optional end date for summary, assets, and trends

        Returns:
            dict with total_assets, current_month, and trends

        Raises:
            ValueError: If ledger doesn't exist
        """
        # Verify ledger exists
        ledger = self.session.get(Ledger, ledger_id)
        if not ledger:
            raise ValueError(f"Ledger not found: {ledger_id}")

        # Validate explicitly provided date range
        if start_date and end_date and start_date > end_date:
            raise ValueError("Start date cannot be after end date")

        # Determine effective date range
        if start_date and end_date:
            # Explicit range provided
            summary_start = start_date
            effective_end_date = end_date
            trend_start = start_date
        else:
            # Default behavior: Use range of all transactions
            # Get min and max date from transactions
            date_range_query = select(func.min(Transaction.date), func.max(Transaction.date)).where(
                Transaction.ledger_id == ledger_id
            )

            min_date, max_date = self.session.exec(date_range_query).one()

            if min_date and max_date:
                # Use transaction range if available
                # For summary and trends, use the full range
                summary_start = min_date
                effective_end_date = max_date
                trend_start = min_date
            else:
                # No transactions, fallback to current month
                today = date.today()
                effective_end_date = today
                summary_start = today.replace(day=1)
                # Trend start 11 months back for empty state
                year = today.year
                month = today.month - 11
                while month <= 0:
                    month += 12
                    year -= 1
                trend_start = date(year, month, 1)

        # Calculate total assets (as of effective_end_date)
        total_assets = self._calculate_total_assets(ledger_id, effective_end_date)

        # Calculate total liabilities (as of effective_end_date)
        total_liabilities = self._calculate_total_liabilities(ledger_id, effective_end_date)

        # Get period summary (income/expenses within range)
        current_month = self._get_period_summary(ledger_id, summary_start, effective_end_date)

        # Get trends
        trends = self._get_monthly_trends(ledger_id, trend_start, effective_end_date)

        return {
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "current_month": current_month,
            "trends": trends,
            "date_range": {
                "start": summary_start.isoformat(),
                "end": effective_end_date.isoformat(),
            },
        }

    def get_accounts_by_category(self, ledger_id: uuid.UUID) -> dict:
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
            # Get all non-archived accounts for this type, sorted by sort_order then name
            accounts = self.session.exec(
                select(Account)
                .where(Account.ledger_id == ledger_id)
                .where(Account.type == account_type)
                .where(Account.is_archived.is_(False))
                .order_by(Account.sort_order, Account.name)
            ).all()

            # Build tree structure
            account_tree = self._build_account_tree(accounts)

            categories.append(
                {
                    "type": account_type.value,
                    "accounts": account_tree,
                }
            )

        return {"categories": categories}

    def _build_account_tree(self, accounts: list[Account]) -> list[dict]:
        """Build hierarchical tree from flat account list.

        Accounts are sorted by sort_order, then name within each level.
        """
        # Create lookup dict
        account_dict = {}
        for account in accounts:
            account_dict[account.id] = {
                "id": str(account.id),
                "name": account.name,
                "balance": float(self._calculate_account_balance(account)),
                "parent_id": str(account.parent_id) if account.parent_id else None,
                "depth": account.depth,
                "sort_order": account.sort_order,
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

        # Sort children at each level by sort_order, then name
        def sort_children(nodes: list[dict]) -> None:
            nodes.sort(key=lambda x: (x["sort_order"], x["name"]))
            for node in nodes:
                if node["children"]:
                    sort_children(node["children"])

        sort_children(root_accounts)

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

            transaction_list.append(
                {
                    "id": str(txn.id),
                    "date": txn.date.isoformat(),
                    "description": txn.description,
                    "amount": float(txn.amount),
                    "type": txn.transaction_type.value if txn.transaction_type else "EXPENSE",
                    "other_account_name": other_account.name if other_account else "Unknown",
                }
            )

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

    def _calculate_total_assets(self, ledger_id: uuid.UUID, end_date: date) -> Decimal:
        """Calculate sum of all ASSET account balances as of end_date."""
        # Get all asset accounts
        accounts = self.session.exec(
            select(Account)
            .where(Account.ledger_id == ledger_id)
            .where(Account.type == AccountType.ASSET)
        ).all()

        total = Decimal("0")
        for account in accounts:
            total += self._calculate_account_balance(account, end_date)

        return total

    def _calculate_total_liabilities(self, ledger_id: uuid.UUID, end_date: date) -> Decimal:
        """Calculate sum of all LIABILITY account balances as of end_date."""
        # Get all liability accounts
        accounts = self.session.exec(
            select(Account)
            .where(Account.ledger_id == ledger_id)
            .where(Account.type == AccountType.LIABILITY)
        ).all()

        total = Decimal("0")
        for account in accounts:
            total += self._calculate_account_balance(account, end_date)

        return total

    def _calculate_account_balance(self, account: Account, end_date: date | None = None) -> Decimal:
        """Calculate balance for a single account from transactions.

        If end_date is provided, only consider transactions on or before that date.

        For Asset: SUM(incoming) - SUM(outgoing)
        For Liability: SUM(outgoing) - SUM(incoming)
        For Income: SUM(outgoing)
        For Expense: SUM(incoming)
        """
        # Build date filter
        date_filter = []
        if end_date:
            date_filter.append(Transaction.date <= end_date)

        # Get incoming sum (to this account)
        incoming_query = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
            Transaction.to_account_id == account.id
        )
        for condition in date_filter:
            incoming_query = incoming_query.where(condition)

        incoming_result = self.session.exec(incoming_query).one()
        incoming = Decimal(str(incoming_result)) if incoming_result else Decimal("0")

        # Get outgoing sum (from this account)
        outgoing_query = select(func.coalesce(func.sum(Transaction.amount), Decimal("0"))).where(
            Transaction.from_account_id == account.id
        )
        for condition in date_filter:
            outgoing_query = outgoing_query.where(condition)

        outgoing_result = self.session.exec(outgoing_query).one()
        outgoing = Decimal(str(outgoing_result)) if outgoing_result else Decimal("0")

        if account.type == AccountType.ASSET:
            return incoming - outgoing
        elif account.type == AccountType.LIABILITY:
            return outgoing - incoming
        elif account.type == AccountType.INCOME:
            return outgoing
        else:  # EXPENSE
            return incoming

    def _get_period_summary(self, ledger_id: uuid.UUID, start_date: date, end_date: date) -> dict:
        """Get income and expenses for the specified period."""
        # Sum income transactions
        income_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
            .where(Transaction.ledger_id == ledger_id)
            .where(Transaction.transaction_type == TransactionType.INCOME)
            .where(Transaction.date >= start_date)
            .where(Transaction.date <= end_date)
        ).one()
        income = Decimal(str(income_result)) if income_result else Decimal("0")

        # Sum expense transactions
        expense_result = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
            .where(Transaction.ledger_id == ledger_id)
            .where(Transaction.transaction_type == TransactionType.EXPENSE)
            .where(Transaction.date >= start_date)
            .where(Transaction.date <= end_date)
        ).one()
        expenses = Decimal(str(expense_result)) if expense_result else Decimal("0")

        return {
            "income": float(income),
            "expenses": float(expenses),
            "net_cash_flow": float(income - expenses),
        }

    def _get_monthly_trends(
        self, ledger_id: uuid.UUID, start_date: date, end_date: date
    ) -> list[dict]:
        """Get income and expense totals for each month in the range."""
        trends = []

        # Start from the first day of the start_date month
        current = start_date.replace(day=1)
        # End at the last day of the end_date month
        end_limit = (
            end_date.replace(year=end_date.year + 1, month=1, day=1)
            if end_date.month == 12
            else end_date.replace(month=end_date.month + 1, day=1)
        ) - timedelta(days=1)

        while current <= end_limit:
            # Range for this month
            month_start = current
            if current.month == 12:
                month_end = current.replace(year=current.year + 1, month=1, day=1) - timedelta(
                    days=1
                )
                next_month = current.replace(year=current.year + 1, month=1, day=1)
            else:
                month_end = current.replace(month=current.month + 1, day=1) - timedelta(days=1)
                next_month = current.replace(month=current.month + 1, day=1)

            # Sum income
            income_result = self.session.exec(
                select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
                .where(Transaction.ledger_id == ledger_id)
                .where(Transaction.transaction_type == TransactionType.INCOME)
                .where(Transaction.date >= month_start)
                .where(Transaction.date <= month_end)
            ).one()
            income = Decimal(str(income_result)) if income_result else Decimal("0")

            # Sum expenses
            expense_result = self.session.exec(
                select(func.coalesce(func.sum(Transaction.amount), Decimal("0")))
                .where(Transaction.ledger_id == ledger_id)
                .where(Transaction.transaction_type == TransactionType.EXPENSE)
                .where(Transaction.date >= month_start)
                .where(Transaction.date <= month_end)
            ).one()
            expenses = Decimal(str(expense_result)) if expense_result else Decimal("0")

            trends.append(
                {
                    "month": month_start.strftime("%b"),
                    "year": month_start.year,
                    "income": float(income),
                    "expenses": float(expenses),
                }
            )

            current = next_month

        return trends
