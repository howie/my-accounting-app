# Tasks: Reports (009-reports)

**Feature**: 009-reports
**Status**: Implemented
**Branch**: 009-reports

## Dependencies

- **Phase 1 (Setup)** → Blocked by nothing
- **Phase 2 (Foundational)** → Blocked by Phase 1
- **Phase 3 (User Story 1)** → Blocked by Phase 2
- **Phase 4 (User Story 2)** → Blocked by Phase 2 (Parallel with Phase 3)
- **Phase 5 (User Story 3)** → Blocked by Phase 3, 4
- **Phase 6 (Polish)** → Blocked by Phase 3, 4

## Phase 1: Setup

_Goal: Initialize project structure and shared utilities_

- [x] T001 Create report schemas for BalanceSheet and IncomeStatement in backend/src/schemas/report.py
- [x] T002 Create empty ReportService class in backend/src/services/report_service.py
- [x] T003 Create Reports router boilerplate in backend/src/api/v1/reports.py
- [x] T004 Register Reports router in backend/src/api/main.py

## Phase 2: Foundational

_Goal: Implement shared calculation logic for financial reports_

**Criteria:**

- [x] Account balance calculation logic is robust and tested for any given date
- [x] Hierarchy aggregation logic handles 3 levels of depth correctly

**Tests:**

- [x] T005 Create unit tests for balance calculation logic in backend/tests/unit/services/test_report_service.py
- [x] T028 [P] Add edge case tests for future dates, closed accounts, and zero balances in backend/tests/unit/services/test_report_service.py

**Implementation:**

- [x] T006 Implement get_account_balances_at_date aggregation in ReportService (backend/src/services/report_service.py)
- [x] T007 Implement hierarchical tree builder with support for showing zero-balance accounts in ReportService (backend/src/services/report_service.py)
- [x] T029 [US1] Implement date validation and 5-year range limit for reports in backend/src/api/v1/reports.py

## Phase 3: User Story 1 - Balance Sheet

_Goal: As a user, I want to pick a date and see my total assets and liabilities so I know my current net worth._

**Criteria:**

- [x] API returns correct Assets, Liabilities, and Equity structure
- [x] Frontend displays the balance sheet with a date picker
- [x] Net Worth is correctly calculated as Assets - Liabilities

**Tests:**

- [x] T008 [US1] Create contract tests for Balance Sheet API in backend/tests/contract/api/test_reports.py

**Implementation (Backend):**

- [x] T009 [US1] Implement get_balance_sheet logic with Equity calculation in backend/src/services/report_service.py
- [x] T010 [US1] Implement GET /reports/balance-sheet endpoint in backend/src/api/v1/reports.py

**Implementation (Frontend):**

- [x] T011 [US1] Create Collapsible ReportTable component in frontend/src/components/reports/ReportTable.tsx
- [x] T012 [US1] Create Balance Sheet page with DatePicker in frontend/src/app/reports/balance-sheet/page.tsx
- [x] T013 [US1] Connect Balance Sheet page to API using React Query

## Phase 4: User Story 2 - Income Statement

_Goal: As a user, I want to select a month or year and see my total income and expenses so I know if I saved money._

**Criteria:**

- [x] API returns correct Income and Expense structure with Net Income
- [x] Frontend displays the income statement with a date range picker
- [x] Date range boundaries are inclusive

**Tests:**

- [x] T014 [US2] Add contract tests for Income Statement API in backend/tests/contract/api/test_reports.py

**Implementation (Backend):**

- [x] T015 [US2] Implement get_income_statement logic with period aggregation in backend/src/services/report_service.py
- [x] T016 [US2] Implement GET /reports/income-statement endpoint in backend/src/api/v1/reports.py

**Implementation (Frontend):**

- [x] T017 [US2] Create Income Statement page with DateRangePicker in frontend/src/app/reports/income-statement/page.tsx
- [x] T018 [US2] Connect Income Statement page to API using React Query

## Phase 5: User Story 3 - Export Reports

_Goal: As a user, I want to export reports to HTML and CSV so I can print them or analyze them in Excel._

**Criteria:**

- [x] User can download CSV of the current report
- [x] User can view/print a printer-friendly HTML version of the report

**Implementation (Backend):**

- [x] T019 [US3] Implement CSV generation for report data in backend/src/services/export_service.py
- [x] T020 [US3] Implement HTML template and rendering for reports in backend/src/services/export_service.py
- [x] T021 [US3] Add /reports/balance-sheet/export and /reports/income-statement/export endpoints in backend/src/api/v1/reports.py

**Implementation (Frontend):**

- [x] T022 [US3] Add "Export CSV" and "Print (HTML)" buttons to Balance Sheet page
- [x] T023 [US3] Add "Export CSV" and "Print (HTML)" buttons to Income Statement page

## Phase 6: Polish & Cross-Cutting Concerns

_Goal: Ensure UI consistency, navigation, and visual appeal_

- [x] T024 Add "Reports" section with sub-links to Sidebar in frontend/src/components/layout/Sidebar.tsx
- [x] T025 [P] Add breakdown charts (Recharts/Tremor) to Balance Sheet page
- [x] T026 [P] Add monthly comparison charts to Income Statement page
- [x] T027 Run final manual verification script with 30k transaction load test in backend/scripts/manual-test.md
