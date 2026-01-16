# Feature Specification: Financial Reports (009-reports)

## Overview

As a user, I want to view my Balance Sheet and Income Statement so that I can understand my overall financial health and performance over time.

## Functional Requirements

### FR-1: Balance Sheet (資產負債表)

- **Purpose**: Show financial status at a specific point in time.
- **Components**:
  - **Assets (資產)**: Balance of all asset accounts + Subtotal.
  - **Liabilities (負債)**: Balance of all liability accounts + Subtotal.
  - **Net Worth (淨資產)**: Calculated as `Assets - Liabilities`.
- **Interaction**: User selects a "Date" to view the snapshot.

### FR-2: Income Statement (損益表)

- **Purpose**: Show financial performance over a specific period.
- **Components**:
  - **Income (收入)**: Sum of all income accounts + Subtotal.
  - **Expenses (支出)**: Sum of all expense accounts + Subtotal.
  - **Net Income (淨收益)**: Calculated as `Income - Expenses`.
- **Interaction**: User selects a "Start Date" and "End Date".

### FR-3: Data Accuracy

- Reports must be automatically calculated from all transaction records.
- Changes to transactions must immediately reflect in reports upon refresh.

### FR-4: Exporting

- Support exporting reports to HTML (for printing) and CSV (for analysis).

## User Stories

### US-1: View Balance Sheet

**As a user**, I want to pick a date and see my total assets and liabilities so I know my current net worth.
**Acceptance Criteria**:

- Display a hierarchical list of Asset accounts with their balances.
- Display a hierarchical list of Liability accounts with their balances.
- Correctly calculate and display Total Assets, Total Liabilities, and Net Worth.
- Support selecting any date from the past up to today.

### US-2: View Income Statement

**As a user**, I want to select a month or year and see my total income and expenses so I know if I saved money.
**Acceptance Criteria**:

- Display a hierarchical list of Income accounts with their totals for the period.
- Display a hierarchical list of Expense accounts with their totals for the period.
- Correctly calculate and display Total Income, Total Expenses, and Net Income.
- Support custom date ranges.

## Non-Functional Requirements

- **NFR-1**: Performance - Report generation should take less than 200ms for up to 30,000 transactions.
- **NFR-2**: Accuracy - All calculations must follow double-entry bookkeeping principles.
- **NFR-3**: Accessibility - Reports should be readable on both desktop and mobile devices.

## Business Rules

- **Snapshot Logic**: Balance Sheet reflects a snapshot at a point in time (end of the selected day).
- **Period Logic**: Income Statement reflects results over an inclusive period (`start_date <= transaction_date <= end_date`).
- **Calculations**: Must be exact to the cent (decimal arithmetic).
- **Future Dates**: Requests for a date in the future should be allowed but will only reflect transactions up to that date (effectively same as a snapshot of "Today" if no future-dated transactions exist).
- **Zero-Balance Accounts**: By default, accounts with a zero balance for the selected period/date should be included in the report to maintain hierarchical completeness, unless a "Hide Zero Balances" filter is applied.
- **Closed/Deleted Accounts**: Accounts that are deleted/closed but have historical transactions MUST still appear in reports for the periods they were active to ensure the Balance Sheet always balances.
- **Hierarchy Changes**: Reports are generated using the _current_ account hierarchy. Historical hierarchy states are not preserved.
- **Data Limits**: Income Statement period is limited to a maximum of 5 years to prevent performance degradation.

## Error Handling

- **Invalid Dates**: Return 400 Bad Request if dates are malformed or start_date > end_date.
- **Empty States**: If no transactions exist for a period, the report should still return the hierarchical structure with zero balances rather than a 404 or empty response.
- **Aggregation Failures**: Return 500 Internal Server Error with a descriptive message if a calculation fails (e.g., unbalanced transaction detected).
