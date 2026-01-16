# Implementation Plan - 008 Data Export

## Technical Context

**Feature**: Data Export (CSV/HTML)
**App**: MyAB (Web Version)
**Stack**: Next.js (Frontend) + FastAPI (Backend) + SQLite (DB)

**Existing Components**:

- `Transaction` model (SQLModel)
- `TransactionService` (Core logic)
- `DateRangePicker` (Frontend UI)
- `ImportService` (Defines CSV format expectations)

**New Components**:

- `ExportService`: Logic to query and format data.
- `GET /api/v1/export`: Endpoint to trigger download.
- `ExportModal`: UI for user selection.

**Unknowns & Risks**:

- **Memory Usage**: Exporting 30k transactions at once might spike memory if loaded entirely into objects.
  - _Mitigation_: Use streaming response in FastAPI (`StreamingResponse`) with a generator.
- **Encoding**: Excel sometimes has trouble with UTF-8 CSVs (needs BOM).
  - _Plan_: Add UTF-8 BOM `\ufeff` to CSV output.
- **HTML Styling**: Needs to be print-friendly.
  - _Plan_: Use minimal CSS, `@media print` query.

## Constitution Check

### I. Data-First Design

- [x] **No Data Loss**: Export is read-only.
- [x] **Validation**: Date ranges validated.
- [x] **Recovery**: CSV format matches Import format, enabling backup/restore cycle.

### II. Test-First Development

- [x] **Contract Tests**: Define API response format (file stream).
- [x] **Integration Tests**: Verify exported data matches database content.
- [x] **Edge Cases**: Empty date range, no transactions, special characters in descriptions.

### III. Financial Accuracy

- [x] **Double-Entry**: Exports reflect the stored double-entry transactions.
- [x] **Immutable History**: Export is a snapshot in time.

### IV. Simplicity

- [x] **YAGNI**: Only CSV and HTML. No PDF generation (browser handles it).
- [x] **Standard Libs**: Python `csv` module, Jinja2 for HTML.

### V. Cross-Platform

- [x] **Web Compatible**: Standard HTTP downloads.

**Assessment**: PASS

## Phase 0: Research & Decisions

### Decision 1: CSV Library vs Manual String Building

- **Decision**: Use Python's built-in `csv` module.
- **Rationale**: Handles escaping (quotes, commas) correctly and robustly. Manual string concatenation is error-prone.

### Decision 2: Streaming vs Buffered Response

- **Decision**: Use `StreamingResponse` for CSV.
- **Rationale**: Future-proofing for larger datasets (Constitution mentions 30k limit). Keeps memory footprint low.
- **Note**: HTML can be buffered as it's typically for smaller "report" ranges, but streaming is consistent. Let's stream CSV, buffer HTML (simpler templating) unless size requires streaming. _Correction_: HTML tables for 30k rows might crash a browser rendering engine anyway. HTML is likely for "monthly" reports. We will implement simple buffering for HTML for now.

### Decision 3: CSV Format Specifics

- **Format**:
  `Date,Type,Expense Account,Income Account,From Account,To Account,Amount,Description,Invoice No`
- **Mapping**:
  - `Expense`: Type=支出, Expense Account=[Target], From Account=[Source]
  - `Income`: Type=收入, Income Account=[Source], To Account=[Target]
  - `Transfer`: Type=轉帳, From Account=[Source], To Account=[Target]
- **Rationale**: Strict adherence to Feature 006 Import format for round-trip compatibility.

---

## Phase 1: Design & Contracts

### 1. Data Model (`data-model.md`)

No new database models required. We are reading existing `Transaction` and `Account` entities.
However, we define the **Export Schema** (output format).

**CSV Columns**:

1. `date`: YYYY/MM/DD
2. `type`: 支出/收入/轉帳 (Localized?) -> _Spec says "支出" etc. We should check if strict string matching is required or if we stick to internal Enums `EXPENSE`/`INCOME` and map them._ -> **Decision**: Map to the localized strings expected by the Import logic (Feature 006).
3. `expense_account`: Name of account (if type=EXPENSE)
4. `income_account`: Name of account (if type=INCOME)
5. `from_account`: Name of source account
6. `to_account`: Name of dest account
7. `amount`: Numeric (positive)
8. `description`: Text
9. `invoice_no`: Text (optional)

### 2. API Contracts (`contracts/`)

**Endpoint**: `GET /api/v1/export`

**Query Parameters**:

- `start_date` (date, optional)
- `end_date` (date, optional)
- `account_id` (uuid, optional) - for Single Account Export
- `format` (enum: `csv`, `html`)

**Response**:

- Content-Type: `text/csv` or `text/html`
- Content-Disposition: `attachment; filename="export_20251120.csv"`

### 3. Agent Context

Update `backend/GEMINI.md` (or equivalent) to include `ExportService`.

---

## Phase 2: Implementation Steps

### Backend

1. **Contract Test**: Create `tests/contract/test_export_api.py`.
   - Verify endpoint accepts params.
   - Verify correct Content-Type headers.
2. **Export Service**: Implement `src/services/export_service.py`.
   - `generate_csv(query)`: Generator function.
   - `generate_html(query)`: Template rendering.
   - Logic to map `Transaction` -> CSV Row format.
3. **API Router**: Implement `src/api/routes/export.py`.
   - Connect service to endpoint.
   - Handle `StreamingResponse`.

### Frontend

1. **API Client**: Add `exportData` function to `src/lib/api`.
2. **Export UI**:
   - Create `ExportDialog` component (or add to `Settings` / `Sidebar`).
   - Add button to `AccountDetails` page.
   - Handle download action (blob URL).

### Verification

1. **Round Trip Test**:
   - Export Data -> Clear DB -> Import Data -> Verify Balances match.
2. **Visual Check**:
   - Open HTML export, print preview.
