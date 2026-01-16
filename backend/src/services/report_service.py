"""Report service for generating financial reports."""

from collections import defaultdict
from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlmodel import Session, select

from src.models.account import Account, AccountType
from src.models.transaction import Transaction
from src.schemas.report import BalanceSheet, IncomeStatement, ReportEntry


class ReportService:
    """Service for calculating and generating financial reports."""

    def __init__(self, session: Session):
        self.session = session

    async def get_balance_sheet(self, ledger_id: UUID, as_of_date: date) -> BalanceSheet:
        """Generate a Balance Sheet for a specific date."""
        # Get all accounts
        accounts = self.session.exec(select(Account).where(Account.ledger_id == ledger_id)).all()

        # Get balances
        balances = await self.get_account_balances_at_date(ledger_id, as_of_date)

        # Build Trees
        assets = self.build_report_hierarchy(list(accounts), balances, AccountType.ASSET)
        liabilities = self.build_report_hierarchy(list(accounts), balances, AccountType.LIABILITY)

        # Calculate Equity
        # Equity = Total Assets - Total Liabilities
        total_assets = sum(node.amount for node in assets)
        total_liabilities = sum(node.amount for node in liabilities)
        total_equity = total_assets - total_liabilities

        # Create Equity Tree (Virtual)
        # In a real app, we might have Equity accounts. For now, we just show Retained Earnings/Net Worth.
        # We can look for explicit EQUITY accounts if we had them, but per spec, we calculate Net Worth.
        equity_entry = ReportEntry(name="Net Worth", amount=total_equity, level=0)

        return BalanceSheet(
            date=as_of_date,
            assets=assets,
            liabilities=liabilities,
            equity=[equity_entry],
            total_assets=total_assets,
            total_liabilities=total_liabilities,
            total_equity=total_equity,
        )

    async def get_income_statement(
        self, ledger_id: UUID, start_date: date, end_date: date
    ) -> IncomeStatement:
        """Generate an Income Statement for a specific period."""
        # Get all accounts
        accounts = self.session.exec(select(Account).where(Account.ledger_id == ledger_id)).all()

        # Calculate balances for the period
        # Logic:
        # Income = Sum(Credit) - Sum(Debit)
        # Expense = Sum(Debit) - Sum(Credit)

        transactions = self.session.exec(
            select(Transaction)
            .where(Transaction.ledger_id == ledger_id)
            .where(Transaction.date >= start_date)
            .where(Transaction.date <= end_date)
        ).all()

        account_types = {acc.id: acc.type for acc in accounts}
        balances: dict[UUID, Decimal] = defaultdict(Decimal)

        for tx in transactions:
            # TO Account (Debit)
            to_type = account_types.get(tx.to_account_id)
            if to_type == AccountType.INCOME:
                balances[tx.to_account_id] -= tx.amount
            elif to_type == AccountType.EXPENSE:
                balances[tx.to_account_id] += tx.amount

            # FROM Account (Credit)
            from_type = account_types.get(tx.from_account_id)
            if from_type == AccountType.INCOME:
                balances[tx.from_account_id] += tx.amount
            elif from_type == AccountType.EXPENSE:
                balances[tx.from_account_id] -= tx.amount

        # Build Trees
        income = self.build_report_hierarchy(list(accounts), balances, AccountType.INCOME)
        expenses = self.build_report_hierarchy(list(accounts), balances, AccountType.EXPENSE)

        total_income = sum(node.amount for node in income)
        total_expenses = sum(node.amount for node in expenses)
        net_income = total_income - total_expenses

        return IncomeStatement(
            start_date=start_date,
            end_date=end_date,
            income=income,
            expenses=expenses,
            total_income=total_income,
            total_expenses=total_expenses,
            net_income=net_income,
        )

    async def get_account_balances_at_date(
        self, ledger_id: UUID, target_date: date
    ) -> dict[UUID, Decimal]:
        """Calculate balances for all accounts at a specific date."""
        transactions = self.session.exec(
            select(Transaction)
            .where(Transaction.ledger_id == ledger_id)
            .where(Transaction.date <= target_date)
        ).all()

        # Pre-fetch account types to determine Debit/Credit normal
        accounts = self.session.exec(select(Account).where(Account.ledger_id == ledger_id)).all()
        account_types = {acc.id: acc.type for acc in accounts}

        balances: dict[UUID, Decimal] = defaultdict(Decimal)

        for tx in transactions:
            # TO Account (Debit)
            to_type = account_types.get(tx.to_account_id)
            if to_type in (AccountType.ASSET, AccountType.EXPENSE):
                balances[tx.to_account_id] += tx.amount
            else:
                balances[tx.to_account_id] -= tx.amount

            # FROM Account (Credit)
            from_type = account_types.get(tx.from_account_id)
            if from_type in (AccountType.ASSET, AccountType.EXPENSE):
                balances[tx.from_account_id] -= tx.amount
            else:
                balances[tx.from_account_id] += tx.amount

        return balances

    def build_report_hierarchy(
        self, accounts: list[Account], balances: dict[UUID, Decimal], root_type: str
    ) -> list[ReportEntry]:
        """Build a hierarchical report structure from flat account list and balances."""
        # Filter accounts by type
        relevant_accounts = [a for a in accounts if a.type == root_type]

        # Group by Parent ID
        children_map = defaultdict(list)
        for acc in relevant_accounts:
            if acc.parent_id:
                children_map[acc.parent_id].append(acc)
            # Note: Roots have parent_id=None, but we handle them separately

        def build_node(account: Account) -> ReportEntry:
            children_accounts = children_map.get(account.id, [])
            # Sort children by sort_order
            children_accounts.sort(key=lambda x: x.sort_order)

            children_nodes = [build_node(child) for child in children_accounts]

            # Calculate own amount (balance + children)
            # For this report, we show the aggregated balance at each level
            # If account has its own transactions, they are in `balances`.
            # If it's a parent folder, `balances` is likely 0, but we sum children.

            # Note on hierarchy:
            # A parent account CAN have its own balance if transactions were posted to it directly.
            # Usually, parent accounts are just containers.
            # Total = Own Balance + Sum(Children Totals)

            own_balance = balances.get(account.id, Decimal("0"))
            children_total = sum(child.amount for child in children_nodes)
            total_amount = own_balance + children_total

            return ReportEntry(
                account_id=account.id,
                name=account.name,
                amount=total_amount,
                level=account.depth
                - 1,  # API uses 0-based index? Spec says 0=Root. DB uses 1=Root.
                children=children_nodes,
            )

        # Build roots
        roots = [a for a in relevant_accounts if a.depth == 1]
        roots.sort(key=lambda x: x.sort_order)

        return [build_node(root) for root in roots]
