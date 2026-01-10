# Implementation Plan: 資料匯入功能

**Branch**: `006-data-import` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/006-data-import/spec.md`

## Summary

實作批次資料匯入功能，支援 MyAB CSV 匯入及信用卡帳單 CSV 匯入。使用者可從 Sidebar 選單進入匯入頁面，上傳 CSV 檔案後預覽並確認匯入。系統支援科目自動對應、重複偵測、原子操作匯入，並維持完整的 audit trail。

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**: FastAPI, SQLModel, Next.js 15, React 19, TanStack Query
**Storage**: PostgreSQL 16 (existing schema from 001-core-accounting)
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 處理 2000 筆交易的 CSV 在 30 秒內完成解析與匯入
**Constraints**: 檔案大小上限 10MB, 原子操作（全成功或全回滾）
**Scale/Scope**: 單一帳本匯入，支援 5+ 銀行信用卡格式

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

Verify compliance with all five core principles from `.specify/memory/constitution.md`:

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - 使用 Decimal 處理金額，解析時驗證格式與精度
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - 所有匯入的交易標記 source="imported"，記錄來源檔案名稱
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - 匯入需明確確認，預覽階段不寫入資料，原子操作確保不會部分匯入
- [x] Is input validation enforced (amounts, dates, account references)?
  - CSV 解析時驗證所有欄位格式，金額範圍，日期有效性
- [x] Are destructive operations reversible?
  - 匯入為新增操作，可透過刪除交易回復（未來可考慮批次刪除已匯入交易）

**Violations**: None

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
  - 依據 TDD 流程，先撰寫 CSV 解析器測試、匯入服務測試
- [x] Will tests be reviewed/approved before coding?
  - 測試檔案在 tasks.md 中明確列出，需審核後實作
- [x] Are contract tests planned for service boundaries?
  - API endpoints 有對應的 contract tests
- [x] Are integration tests planned for multi-account transactions?
  - 匯入多筆交易涉及多科目，需 integration tests 驗證
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - 各種日期格式、金額格式、編碼問題的 edge case tests

**Violations**: None

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - 每筆匯入交易驗證 from_account 與 to_account 金額相等
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - 匯入後交易與一般交易相同，遵循現有不可變規則
- [x] Are calculations traceable to source transactions?
  - 匯入交易記錄來源檔案名稱，可追溯
- [x] Are timestamps tracked (created, modified, business date)?
  - 保留 CSV 中的原始日期，created_at 記錄匯入時間
- [x] Is change logging implemented (who, what, when, why)?
  - 使用 AuditLog 記錄匯入操作，包含匯入筆數、來源等資訊

**Violations**: None

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
  - ROADMAP 中明確規劃，使用者從 MyAB 遷移的關鍵需求
- [x] Is the design clear over clever (human-auditable)?
  - 使用簡單的 CSV 解析器，逐行處理，邏輯清晰
- [x] Are abstractions minimized (especially for financial calculations)?
  - 直接使用 Decimal 處理金額，無額外抽象層
- [x] Are complex business rules documented with accounting references?
  - 科目對應、重複偵測規則在 spec 中明確定義

**Violations**: None

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
  - 金額使用 Decimal，前後端一致
- [x] Is data format compatible between desktop and web?
  - CSV 為純文字格式，無平台相容性問題
- [x] Are platform-specific features clearly documented?
  - Web-only 功能，無跨平台考量
- [x] Do workflows follow consistent UX patterns?
  - 匯入流程遵循 upload → preview → confirm 標準模式
- [x] Does cloud sync maintain transaction ordering?
  - N/A - 本功能不涉及 cloud sync

**Violations**: None

**Overall Assessment**: PASS

## Project Structure

### Documentation (this feature)

```text
docs/features/006-data-import/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
├── tasks.md             # Phase 2 output
└── checklists/          # Quality validation
    └── requirements.md  # Spec quality checklist
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── import_session.py      # New: ImportSession model
│   ├── schemas/
│   │   └── data_import.py         # New: Import request/response schemas
│   ├── services/
│   │   ├── import_service.py      # New: Main import orchestration
│   │   ├── csv_parser.py          # New: CSV parsing utilities
│   │   └── category_suggester.py  # New: Credit card category suggestion
│   └── api/
│       └── import_routes.py       # New: Import API endpoints
└── tests/
    ├── unit/
    │   ├── test_csv_parser.py
    │   └── test_category_suggester.py
    ├── integration/
    │   └── test_import_service.py
    └── fixtures/
        └── csv/                   # Sample CSV files for testing

frontend/
├── src/
│   ├── app/
│   │   └── [locale]/
│   │       └── ledgers/
│   │           └── [ledgerId]/
│   │               └── import/
│   │                   └── page.tsx       # New: Import page
│   ├── components/
│   │   └── import/
│   │       ├── ImportTypeSelector.tsx     # New
│   │       ├── CsvUploader.tsx            # New
│   │       ├── ImportPreview.tsx          # New
│   │       ├── AccountMapper.tsx          # New
│   │       └── ImportConfirmation.tsx     # New
│   └── lib/
│       └── api/
│           └── import.ts                  # New: Import API client
└── tests/
    └── components/
        └── import/
            └── ImportPreview.test.tsx
```

**Structure Decision**: Web application structure (existing pattern from 001-core-accounting)

## Complexity Tracking

> No constitution violations requiring justification.

N/A
