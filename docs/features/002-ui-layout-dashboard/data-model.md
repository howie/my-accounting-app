# Data Model: UI Layout Dashboard

**Date**: 2026-01-06
**Feature**: 002-ui-layout-dashboard
**Source**: [spec.md](./spec.md)

This document defines the view models and response schemas for the dashboard feature. No new database entities are created; this feature uses existing entities from 001-core-accounting.

## Existing Entities (Reference)

From 001-core-accounting data-model.md:

- **User**: Owner of ledgers
- **Ledger**: Container for accounts and transactions
- **Account**: Financial account with type (ASSET, LIABILITY, INCOME, EXPENSE)
- **Transaction**: Double-entry record with from/to accounts

---

## View Models (Frontend)

### 1. SidebarAccountItem

Represents an account in the sidebar navigation.

```typescript
interface SidebarAccountItem {
  id: string; // UUID
  name: string; // Account name (truncated to 20 chars in UI)
  type: AccountType; // ASSET | LIABILITY | INCOME | EXPENSE
  balance: number; // Cached balance for display
}
```

### 2. SidebarCategory

Groups accounts by type for sidebar display.

```typescript
interface SidebarCategory {
  type: AccountType;
  label: string; // Display name (Assets, Loans, Income, Expenses)
  icon: string; // Icon identifier
  accounts: SidebarAccountItem[];
  isExpanded: boolean; // UI state
}
```

### 3. DashboardSummary

Main dashboard data structure.

```typescript
interface DashboardSummary {
  totalAssets: number; // Sum of all ASSET account balances
  currentMonth: {
    income: number; // Sum of INCOME transactions this month
    expenses: number; // Sum of EXPENSE transactions this month
    netCashFlow: number; // income - expenses
  };
  trends: MonthlyTrend[]; // Last 6 months
}
```

### 4. MonthlyTrend

Single month's income/expense data for trend charts.

```typescript
interface MonthlyTrend {
  month: string; // Format: "Jan", "Feb", etc.
  year: number; // 4-digit year
  income: number; // Total income for month
  expenses: number; // Total expenses for month
}
```

### 5. TransactionListItem

Simplified transaction for list display.

```typescript
interface TransactionListItem {
  id: string;
  date: string; // ISO date string
  description: string;
  amount: number;
  type: TransactionType; // EXPENSE | INCOME | TRANSFER
  otherAccount: string; // Name of the counterpart account
}
```

---

## API Response Schemas (Backend)

### DashboardResponse

```python
class MonthlyTrendResponse(BaseModel):
    month: str           # "Jan", "Feb", etc.
    year: int
    income: Decimal
    expenses: Decimal

class CurrentMonthResponse(BaseModel):
    income: Decimal
    expenses: Decimal
    net_cash_flow: Decimal

class DashboardResponse(BaseModel):
    total_assets: Decimal
    current_month: CurrentMonthResponse
    trends: list[MonthlyTrendResponse]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "total_assets": "21847.00",
                "current_month": {
                    "income": "2992.00",
                    "expenses": "1419.00",
                    "net_cash_flow": "1573.00"
                },
                "trends": [
                    {"month": "Aug", "year": 2025, "income": "2500.00", "expenses": "1200.00"},
                    {"month": "Sep", "year": 2025, "income": "2800.00", "expenses": "1400.00"}
                ]
            }
        }
    )
```

### AccountsByCategoryResponse

```python
class AccountSummary(BaseModel):
    id: UUID
    name: str
    balance: Decimal

class CategoryAccounts(BaseModel):
    type: AccountType
    accounts: list[AccountSummary]

class AccountsByCategoryResponse(BaseModel):
    categories: list[CategoryAccounts]
```

### AccountTransactionsResponse

```python
class TransactionListItem(BaseModel):
    id: UUID
    date: date
    description: str
    amount: Decimal
    type: TransactionType
    other_account_name: str  # The account on the other side

class AccountTransactionsResponse(BaseModel):
    account_id: UUID
    account_name: str
    transactions: list[TransactionListItem]
    total_count: int
    page: int
    page_size: int
    has_more: bool
```

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐  │
│  │  Sidebar    │    │  Dashboard  │    │  Transaction List   │  │
│  │  Component  │    │  Component  │    │  Component          │  │
│  └──────┬──────┘    └──────┬──────┘    └──────────┬──────────┘  │
│         │                  │                       │            │
│         ▼                  ▼                       ▼            │
│  useSidebarAccounts()  useDashboard()     useAccountTransactions()│
│         │                  │                       │            │
└─────────┼──────────────────┼───────────────────────┼────────────┘
          │                  │                       │
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Endpoints                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  GET /ledgers/{id}/        GET /ledgers/{id}/   GET /accounts/{id}/│
│      accounts/by-category      dashboard           transactions  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
          │                  │                       │
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Dashboard Service                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  • get_accounts_by_category()                                    │
│  • get_dashboard_summary()                                       │
│  • get_account_transactions()                                    │
│                                                                 │
│  Aggregation queries:                                           │
│  - SUM balances by account type                                 │
│  - SUM transactions by month for last 6 months                  │
│  - Filter transactions by date range                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
          │                  │                       │
          ▼                  ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                   PostgreSQL (Existing)                          │
├─────────────────────────────────────────────────────────────────┤
│  accounts, transactions, ledgers (from 001-core-accounting)     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Aggregation Queries

### Total Assets Query

```sql
SELECT COALESCE(SUM(balance), 0) as total_assets
FROM accounts
WHERE ledger_id = :ledger_id
  AND type = 'ASSET';
```

### Current Month Income/Expenses

```sql
-- Income this month
SELECT COALESCE(SUM(amount), 0) as income
FROM transactions
WHERE ledger_id = :ledger_id
  AND transaction_type = 'INCOME'
  AND date >= :first_day_of_month
  AND date <= :last_day_of_month;

-- Expenses this month
SELECT COALESCE(SUM(amount), 0) as expenses
FROM transactions
WHERE ledger_id = :ledger_id
  AND transaction_type = 'EXPENSE'
  AND date >= :first_day_of_month
  AND date <= :last_day_of_month;
```

### 6-Month Trend Query

```sql
SELECT
  TO_CHAR(date, 'Mon') as month,
  EXTRACT(YEAR FROM date) as year,
  SUM(CASE WHEN transaction_type = 'INCOME' THEN amount ELSE 0 END) as income,
  SUM(CASE WHEN transaction_type = 'EXPENSE' THEN amount ELSE 0 END) as expenses
FROM transactions
WHERE ledger_id = :ledger_id
  AND date >= :six_months_ago
GROUP BY EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date), TO_CHAR(date, 'Mon')
ORDER BY EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date);
```

---

## Indexes (Already Exist)

From 001-core-accounting:

```sql
CREATE INDEX idx_transactions_ledger_date ON transactions(ledger_id, date DESC);
CREATE INDEX idx_accounts_ledger ON accounts(ledger_id);
```

No additional indexes needed for this feature.
