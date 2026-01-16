# Quickstart: Data Export

This guide verifies the Data Export functionality manually.

## Prerequisites

1. App running (`make dev-run`).
2. Logged in user.
3. At least 5 transactions in the current ledger (Expenses, Incomes, Transfers).

## Scenarios

### 1. Full CSV Export

1. Navigate to **Settings** (or Sidebar if "Export" is top-level).
2. Click **Export Data**.
3. Select **Format: CSV**.
4. Leave Date Range empty (All Time).
5. Click **Export**.
6. **Verify**:
   - File `export_YYYYMMDD.csv` downloads.
   - Open in Excel/Numbers.
   - Characters (Chinese) display correctly (no garbled text).
   - Columns match: `Date, Type, Expense Account...`

### 2. HTML Report Export

1. Open Export Modal.
2. Select **Format: HTML**.
3. Select **Date Range**: "This Month".
4. Click **Export**.
5. **Verify**:
   - File opens or downloads.
   - Layout looks like a simple table.
   - Press `Ctrl+P` (Print) -> Check print preview layout.

### 3. Single Account Export

1. Go to **Accounts** -> Select "Cash".
2. Look for **Export** button (if implemented on page) OR go to Main Export and select "Cash".
3. Export as CSV.
4. **Verify**: CSV only contains rows where "From Account" or "To Account" is "Cash".
