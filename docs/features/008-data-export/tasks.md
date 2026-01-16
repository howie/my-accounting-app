# Feature 008: Data Export - Task List

## Phase 1: Setup & Testing (Mandatory TDD)

- [x] T001 [P] Create `ExportService` interface and test structure
  - **File**: `backend/src/services/export_service.py` (Stub)
  - **File**: `backend/tests/unit/test_export_service.py`
  - **Description**: Define the `ExportService` class and write unit tests for `generate_csv_content` logic. Test cases: empty list, single transaction (Expense/Income/Transfer), special characters.
  - **Gate**: Tests must FAIL (Red).

- [x] T002 [P] Create Export API Contract Tests
  - **File**: `backend/tests/contract/test_export_api.py`
  - **Description**: Write tests for `GET /api/v1/export/transactions`. Test query params (date range, account_id, format), content-type headers, and error states (422, 404).
  - **Gate**: Tests must FAIL (Red).

- [x] T003 [US1] Implement Export Service CSV Logic
  - **File**: `backend/src/services/export_service.py`
  - **Description**: Implement `generate_csv_content` using Python's `csv` module with `StringIO` and `yield`. Implement logic to map `Transaction` model to the required 9-column CSV format. Handle UTF-8 BOM.
  - **Gate**: Unit tests must PASS (Green).

- [x] T004 [US3] Implement Export Service HTML Logic
  - **File**: `backend/src/services/export_service.py`
  - **File**: `backend/src/templates/export_report.html` (New)
  - **Description**: Add `generate_html_content` method. Create a Jinja2 template for the print-friendly table.
  - **Gate**: Unit tests must PASS (Green).

- [x] T005 [US1] Implement Export API Endpoint
  - **File**: `backend/src/api/routes/export.py`
  - **File**: `backend/src/api/main.py` (Register router)
  - **Description**: Create the router, inject `ExportService` (and dependencies like `TransactionService` for data fetching), handle `StreamingResponse` for CSV and HTML return. Connect to `GET /api/v1/export/transactions`.
  - **Gate**: Contract tests must PASS (Green).

## Phase 2: Frontend Implementation

- [x] T006 [US1] Add Export API Client Function
  - **File**: `frontend/src/lib/api/export.ts`
  - **Description**: Implement `exportTransactions(params)` function using `fetch` (or existing api client wrapper). Needs to handle Blob response for download.

- [x] T007 [US1] Create Export UI Component
  - **File**: `frontend/src/components/export/ExportModal.tsx`
  - **Description**: Create a Dialog/Modal with:
    - Date Range Picker (Start/End).
    - Format Selection (Radio: CSV/HTML).
    - Account Selection (Optional dropdown, default "All").
    - "Export" button (Loading state handling).

- [x] T008 [US1] Integrate Export Entry Point
  - **File**: `frontend/src/components/layout/Sidebar.tsx`
  - **Description**: Add "Export" link/button to the sidebar navigation.
  - **File**: `frontend/src/app/export/page.tsx` (Optional, if using page instead of modal, but modal is preferred per spec. Let's stick to Modal trigger from Sidebar or a dedicated Data Management page. Spec says "New Export item in Sidebar". Let's make it a Modal triggered from Sidebar action or a simple page `src/app/export/page.tsx` if it's a top-level feature. Let's do a simple Page for clarity).
  - **Decision**: Create `frontend/src/app/export/page.tsx` containing the export form.

## Phase 3: Integration & Polish

- [x] T009 [US1] Integration Verification
  - **Description**: Manually verify export of CSV. Import the same CSV using Feature 006 (Import) into a new empty ledger and verify balances match.
  - **Check**: Chinese characters display correctly in Excel.

- [x] T010 [US3] HTML Print Styling
  - **File**: `backend/src/templates/export_report.html`
  - **Description**: Refine CSS `@media print` to ensure table fits on A4 paper, hides URL headers/footers if possible, ensures good contrast.

- [x] T011 Documentation
  - **File**: `docs/myab-spec/05-data-management.md`
  - **Description**: Update User Guide with Export instructions if strictly necessary (already exists in spec, just verify accuracy).

- [x] T012 Final cleanup
  - **Description**: Run linters, remove unused code.

## Dependencies

- **US1 (CSV Export)**: T001, T002, T003, T005, T006, T007, T008
- **US2 (Single Account)**: Included in US1 tasks (account_id parameter handling)
- **US3 (HTML Export)**: T004, T010 (plus frontend option in T007)

## Parallel Execution

- T001 and T002 can be done in parallel.
- T006 and T007 can be done in parallel with backend tasks after API contract is settled.
