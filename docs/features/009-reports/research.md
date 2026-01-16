# Phase 0: Research Findings

**Feature**: 009-reports
**Date**: 2026-01-16

## 1. Requirements Analysis

The feature requires two core reports:

1.  **Balance Sheet**: A snapshot of Assets, Liabilities, and Equity at a specific date.
2.  **Income Statement**: A summary of Income and Expenses over a specific period.

Both reports require aggregating transaction data. No new database tables are strictly required as all data exists in `accounts` and `transactions`.

## 2. Technical Approach

### Backend (FastAPI)

We will add a new `reports` router with two endpoints:

- `GET /reports/balance-sheet?date=YYYY-MM-DD`
- `GET /reports/income-statement?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`

**Calculation Logic**:

- **Balance Sheet**:
  - Since we need "As of Date", we cannot rely solely on the current `Account.balance` field if we want historical reports.
  - However, for V1, if "As of Date" is "Today", `Account.balance` is sufficient.
  - To support any date `D`:
    - Start with 0 for all accounts.
    - Sum all transactions where `date <= D`.
    - Group by Account.
    - Logic:
      - **Asset/Expense** (Debit Normal): `Balance = Sum(to_amount) - Sum(from_amount)`
      - **Liability/Income/Equity** (Credit Normal): `Balance = Sum(from_amount) - Sum(to_amount)`
  - Optimization: For "Today", use `Account.balance`. For historical, use the transaction sum method. Given the 30k transaction limit, summing on the fly is acceptable (SQLite is fast).

- **Income Statement**:
  - Query transactions where `start_date <= date <= end_date`.
  - Filter for accounts with type `INCOME` or `EXPENSE`.
  - Group by Account.
  - Logic:
    - **Income** (Credit Normal): `Amount = Sum(from_amount) - Sum(to_amount)`
    - **Expense** (Debit Normal): `Amount = Sum(to_amount) - Sum(from_amount)`

### Frontend (Next.js)

- **Library**: Use `@tremor/react` for charts (e.g., Donut chart for breakdown, Bar chart for comparisons) to match existing dashboard style.
- **Components**:
  - `DateRangePicker` (or separate Start/End date inputs).
  - `ReportTable`: A reusable table component to show the hierarchical data (Category -> Subcategory -> Account).
- **Pages**:
  - `/reports/balance-sheet`
  - `/reports/income-statement`

## 3. Decisions & Rationale

- **Decision**: Calculate report data on-the-fly using Transaction aggregations.
  - **Rationale**: Ensures accuracy for historical dates. The dataset size (max 30k) allows for sub-second aggregations in SQLite without complex pre-aggregation or caching.
- **Decision**: Use `@tremor/react` for visualizations.
  - **Rationale**: Consistency with existing Dashboard.
- **Decision**: Implement strict "Debit/Credit" logic based on Account Type.
  - **Rationale**: Ensures accounting accuracy (Constitution Principle I & III).

## 4. Alternatives Considered

- **Pre-calculated Daily Balances**:
  - Create a table `daily_balances` to store account balance at end of every day.
  - _Rejected_: Adds complexity to `Transaction` create/update/delete logic (need to update all future daily balances). Overkill for 30k transactions.
- **Frontend Aggregation**:
  - Fetch all transactions and aggregate in browser.
  - _Rejected_: Performance risk if dataset grows. Business logic should reside in Backend (Single Source of Truth).
