# Data Model: Reports

**Feature**: 009-reports
**Version**: 1.0

## Virtual Models (API Responses)

These models are for API responses and do not correspond to database tables.

### Shared Structures

```python
class ReportEntry(BaseModel):
    """A single line item in a report."""
    account_id: UUID | None  # None for calculated totals like "Total Assets"
    name: str
    amount: Decimal
    level: int  # Indentation level (0=Root, 1=Category, 2=Account)
    children: list["ReportEntry"] = []
```

### Balance Sheet

```python
class BalanceSheet(BaseModel):
    """Snapshot of financial position."""
    date: date
    assets: list[ReportEntry]  # Tree of asset accounts
    liabilities: list[ReportEntry]  # Tree of liability accounts
    equity: list[ReportEntry] # Tree of equity accounts + Net Income (Current Year)

    # Summary
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
```

### Income Statement

```python
class IncomeStatement(BaseModel):
    """Summary of financial performance."""
    start_date: date
    end_date: date
    income: list[ReportEntry]  # Tree of income accounts
    expenses: list[ReportEntry]  # Tree of expense accounts

    # Summary
    total_income: Decimal
    total_expenses: Decimal
    net_income: Decimal
```

## Database Schema (No Changes)

Uses existing `accounts` and `transactions` tables.

### Logic Mapping

- **Assets**: `AccountType.ASSET`
- **Liabilities**: `AccountType.LIABILITY`
- **Income**: `AccountType.INCOME`
- **Expenses**: `AccountType.EXPENSE`
- **Equity**: `Total Assets - Total Liabilities` (Calculated)
