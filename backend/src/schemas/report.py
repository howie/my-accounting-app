"""Report schemas."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class ReportEntry(BaseModel):
    """A single line item in a report."""

    account_id: UUID | None = None  # None for calculated totals like "Total Assets"
    name: str
    amount: Decimal = Field(decimal_places=2)
    level: int  # Indentation level (0=Root, 1=Category, 2=Account)
    children: list["ReportEntry"] = []


class BalanceSheet(BaseModel):
    """Snapshot of financial position."""

    date: date
    assets: list[ReportEntry]  # Tree of asset accounts
    liabilities: list[ReportEntry]  # Tree of liability accounts
    equity: list[ReportEntry]  # Tree of equity accounts + Net Income (Current Year)

    # Summary
    total_assets: Decimal = Field(decimal_places=2)
    total_liabilities: Decimal = Field(decimal_places=2)
    total_equity: Decimal = Field(decimal_places=2)


class IncomeStatement(BaseModel):
    """Summary of financial performance."""

    start_date: date
    end_date: date
    income: list[ReportEntry]  # Tree of income accounts
    expenses: list[ReportEntry]  # Tree of expense accounts

    # Summary
    total_income: Decimal = Field(decimal_places=2)
    total_expenses: Decimal = Field(decimal_places=2)
    net_income: Decimal = Field(decimal_places=2)
