# Feature: Data Export (008-data-export)

## 1. Overview

**Objective**: Implement data export functionality to allow users to backup, analysis, and share their financial data.

**Context**: Users need to export their data for various reasons:

- **Backup**: Creating a copy of their data for safekeeping.
- **Analysis**: Using tools like Excel for more advanced analysis.
- **Printing**: Generating printable reports for record-keeping.
- **Sharing**: Providing data to accountants or other stakeholders.

**Goals**:

- Provide CSV export for full data portability (backup/restore compatible).
- Provide HTML export for human-readable reports and printing.
- Support filtering exports by account (single account export).
- Support filtering exports by date range (cross-account period export).

**Non-Goals**:

- Direct printing functionality (printing is handled via HTML export + browser print).
- PDF export (handled via HTML + browser "Save as PDF").
- Proprietary .mbu backup format (this is handled in feature 012-backup-sync).

## 2. User Stories

### US1: Cross-Account Period Export (CSV)

**As a** user who wants to backup or analyze my data,
**I want to** export all transactions within a specific date range to a CSV file,
**So that** I can import it back later, use it in Excel, or move it to another tool.

**Acceptance Criteria**:

- [ ] User can select "Export Data" from the menu.
- [ ] User can specify a date range (Start Date, End Date).
- [ ] User can choose "CSV" as the format.
- [ ] The exported CSV must contain all necessary fields for re-import (Date, Type, Expense Account, Income Account, From Account, To Account, Amount, Description, Invoice No).
- [ ] The CSV file is downloaded to the user's computer.
- [ ] The CSV encoding should support international characters (UTF-8).

### US2: Single Account Export (CSV)

**As a** user analyzing a specific account,
**I want to** export transactions for just one account to a CSV file,
**So that** I can focus my analysis on that specific asset, liability, income, or expense.

**Acceptance Criteria**:

- [ ] User can select a specific account to export.
- [ ] User can specify a date range.
- [ ] User can choose "CSV" format.
- [ ] The exported CSV contains transactions only involving the selected account.
- [ ] (Note: Single account exports might not be fully re-importable as complete double-entry records if the other side of the transaction is lost in filtering, but per roadmap spec 5.2, "Full format" is emphasized for cross-account. We should aim for the standard CSV format regardless).

### US3: Data Export for Printing (HTML)

**As a** user who wants a hard copy of my records,
**I want to** export my transactions to an HTML file,
**So that** I can open it in a browser and print it nicely.

**Acceptance Criteria**:

- [ ] User can choose "HTML" format during export.
- [ ] The HTML output is formatted as a clean, readable table.
- [ ] The HTML includes headers: Date, Account, Amount, Description.
- [ ] The HTML file opens in a new tab or downloads.
- [ ] The layout is optimized for printing (simple CSS).

## 3. Data Integrity Requirements

> **Constitution Principle I**: Data validation required at all boundaries.

- **DI-001 (Validation)**: Export date ranges must be valid (Start <= End).
- **DI-002 (Consistency)**: Exported data must match the database exactly. Calculations for export (if any) must match dashboard displays.
- **DI-003 (Completeness)**: "Full" exports must contain _all_ transactions in the range, ensuring no financial data is hidden.
- **DI-004 (Format)**: CSV format must strictly adhere to the import spec to ensure restore capability (Round-trip integrity).
- **DI-005 (Privacy)**: Exported files are local only; no data is sent to external servers during generation.

## 4. UI/UX Design

**Entry Point**:

- New "Export" item in the Sidebar (under Import or Data Management section).
- "Export" button on individual Account Details page (for US2).

**Export Modal/Page**:

- **Source**: "All Accounts" (default) or [Account Dropdown]
- **Date Range**: [Start Date] - [End Date] (Default: Current Month or All Time)
- **Format**: (Radio Buttons)
  - [x] CSV (Excel/Backup)
  - [ ] HTML (Printable)
- **Action**: "Export" button (Triggers download).

## 5. Technical Considerations

- **Backend**:
  - New endpoint: `GET /api/v1/export/transactions`
  - Parameters: `start_date`, `end_date`, `account_id` (optional), `format` (csv/html).
  - Streaming response for large datasets to avoid memory spikes.
- **Frontend**:
  - Use `blob` download for file handling.
  - Re-use `DateRangePicker` component.
- **CSV Library**: Use Python's built-in `csv` module or `pandas` (if already used) to handle escaping and encoding correctly.
- **HTML Generation**: Use Jinja2 templates (FastAPI default) for server-side rendering of the HTML report.

## 6. Open Questions

- Should "Single Account Export" include the counter-account in the CSV? (Yes, to maintain context, even if filtering hides the other side's separate ledger entry).
- Is there a maximum limit for export rows? (Constitution says 30k transaction limit for DB, so export should handle 30k rows).
