# Implementation Plan: Gmail 信用卡帳單自動掃描匯入

**Branch**: `011-gmail-cc-statement-import` | **Date**: 2026-02-05 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/011-gmail-cc-statement-import/spec.md`

## Summary

實作 Gmail 信用卡帳單自動掃描匯入功能。系統透過 Gmail API（OAuth2 唯讀權限）連接使用者信箱，以各銀行特定的寄件者地址與關鍵字搜尋帳單郵件，下載 PDF 附件後解密並解析帳單內容（使用 pdfplumber 搭配可選的 LLM 輔助），最後透過現有的 ImportService 匯入複式記帳系統。採用 Strategy 模式設計可擴充的銀行 Parser 架構，初始支援 8 家台灣銀行。支援手動與排程自動掃描，具備帳單層級與交易層級的重複偵測機制。

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**: FastAPI, SQLModel, google-api-python-client, google-auth-oauthlib, pdfplumber, pikepdf (PDF decryption), cryptography (credential encryption), APScheduler (scheduling); Next.js 15, React 19, TanStack Query (Frontend)
**Storage**: PostgreSQL 16 (existing schema from 001-core-accounting, extended with new tables)
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Web application (Linux server backend, browser frontend)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: 掃描 3 家銀行帳單（搜尋+下載+解密+解析）在 60 秒內完成；單份帳單（50 筆交易）解析在 10 秒內完成
**Constraints**: OAuth2 token 與 PDF 密碼必須加密儲存；LLM 呼叫僅傳送文字內容（不傳 PDF 二進位）；PDF 附件暫存需在處理完畢後清除
**Scale/Scope**: 單一使用者、1-3 家銀行、每月 1-3 份帳單、每份 20-50 筆交易

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

Verify compliance with all five core principles from `.specify/memory/constitution.md`:

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - 金額從 PDF 解析後使用 Decimal 處理，驗證格式與精度（TWD 最多 2 位小數）
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - 所有匯入交易標記 source="gmail-statement-import"，記錄來源 email message ID 與銀行名稱
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - 匯入需使用者明確確認；原始 PDF 保留供稽核；原子操作確保不會部分匯入
- [x] Is input validation enforced (amounts, dates, account references)?
  - PDF 解析後驗證所有欄位：金額格式與範圍、日期有效性、商家名稱非空
- [x] Are destructive operations reversible?
  - 匯入為新增操作；刪除 Gmail 連接會清除憑證但不影響已匯入的交易

**Violations**: None

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
  - 依據 TDD 流程：先撰寫 Gmail service mock tests、PDF parser tests、bank parser tests
- [x] Will tests be reviewed/approved before coding?
  - 測試檔案在 tasks.md 中明確列出，需審核後實作
- [x] Are contract tests planned for service boundaries?
  - Gmail API 互動使用 mock/stub 測試；新增 API endpoints 有對應 contract tests
- [x] Are integration tests planned for multi-account transactions?
  - 匯入流程整合測試：從 parsed statement → ImportService → 交易建立
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - PDF 解析 edge cases：密碼錯誤、格式變更、金額解析（千分位/負數/外幣）、日期格式

**Violations**: None

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - 每筆匯入交易：from_account（信用卡科目）→ to_account（費用科目），金額相等
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - 匯入後交易與一般交易相同，遵循現有不可變規則
- [x] Are calculations traceable to source transactions?
  - 每筆交易記錄來源 email message ID、銀行名稱、帳單期間，可追溯至原始 PDF
- [x] Are timestamps tracked (created, modified, business date)?
  - 保留 PDF 中的原始交易日期；created_at 記錄匯入時間；scan job 記錄掃描時間
- [x] Is change logging implemented (who, what, when, why)?
  - 使用 AuditLog 記錄掃描操作與匯入操作

**Violations**: None

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
  - 使用者明確需求：自動化信用卡帳單記帳，減少手動輸入
- [x] Is the design clear over clever (human-auditable)?
  - Strategy 模式清晰：每家銀行一個 Parser 類別，定義搜尋條件+密碼規則+解析邏輯
- [x] Are abstractions minimized (especially for financial calculations)?
  - 金額直接使用 Decimal，無額外抽象；Parser 抽象僅在銀行差異處
- [x] Are complex business rules documented with accounting references?
  - 帳單對應規則（信用卡消費 = 負債支出到費用科目）在 data-model 中記錄

**Violations**: None

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
  - 金額使用 Decimal，前後端一致
- [x] Is data format compatible between desktop and web?
  - Web-only 功能，資料儲存在 PostgreSQL，與現有系統一致
- [x] Are platform-specific features clearly documented?
  - Gmail OAuth2 流程需要瀏覽器環境（redirect URI），已記錄
- [x] Do workflows follow consistent UX patterns?
  - 掃描→預覽→確認匯入，與現有 006-data-import 的 upload→preview→confirm 一致
- [x] Does cloud sync maintain transaction ordering?
  - N/A - 本功能不涉及 cloud sync

**Violations**: None

**Overall Assessment**: PASS

## Project Structure

### Documentation (this feature)

```text
docs/features/011-gmail-cc-statement-import/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
│   └── gmail-import-api.yaml
├── tasks.md             # Phase 2 output (/speckit.tasks command)
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── issues/              # Issue tracking for this feature
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── gmail_connection.py       # New: GmailConnection model
│   │   ├── gmail_scan.py             # New: StatementScanJob, DiscoveredStatement models
│   │   └── user_bank_setting.py      # New: UserBankSetting model
│   ├── schemas/
│   │   └── gmail_import.py           # New: Gmail import request/response schemas
│   ├── services/
│   │   ├── gmail_service.py          # New: Gmail API client (search, download, auth)
│   │   ├── pdf_parser.py             # New: PDF decryption + text extraction
│   │   ├── gmail_import_service.py   # New: Orchestration (scan → parse → import)
│   │   ├── gmail_scheduler.py        # New: Scan scheduling with APScheduler
│   │   └── bank_parsers/             # New: Bank-specific PDF parsers (Strategy pattern)
│   │       ├── __init__.py           # Base class + registry
│   │       ├── base.py               # Abstract BankStatementParser
│   │       ├── ctbc_parser.py        # 中國信託
│   │       ├── fubon_parser.py       # 台北富邦
│   │       ├── cathay_parser.py      # 國泰世華
│   │       ├── dbs_parser.py         # 星展
│   │       ├── hsbc_parser.py        # 匯豐
│   │       ├── hncb_parser.py        # 華南
│   │       ├── esun_parser.py        # 玉山
│   │       └── sinopac_parser.py     # 永豐
│   └── api/
│       └── routes/
│           └── gmail_import_routes.py  # New: Gmail import API endpoints
└── tests/
    ├── unit/
    │   ├── test_gmail_service.py
    │   ├── test_pdf_parser.py
    │   └── test_bank_parsers/
    │       ├── test_base_parser.py
    │       ├── test_ctbc_parser.py
    │       └── ...                    # One test file per bank parser
    ├── integration/
    │   └── test_gmail_import_service.py
    └── fixtures/
        └── pdf/                       # Sample PDF files for testing
            ├── ctbc_sample.pdf
            ├── fubon_sample.pdf
            └── ...

frontend/
├── src/
│   ├── app/
│   │   └── [locale]/
│   │       └── ledgers/
│   │           └── [ledgerId]/
│   │               └── gmail-import/
│   │                   ├── page.tsx           # New: Gmail import main page
│   │                   ├── settings/
│   │                   │   └── page.tsx       # New: Gmail connection & bank settings
│   │                   └── history/
│   │                       └── page.tsx       # New: Scan history page
│   ├── components/
│   │   └── gmail-import/
│   │       ├── GmailConnectButton.tsx         # New: OAuth2 connect/disconnect
│   │       ├── BankSettingsPanel.tsx           # New: Bank enable/disable + password
│   │       ├── ScanProgressIndicator.tsx      # New: Scan progress display
│   │       ├── StatementList.tsx              # New: Found statements list
│   │       ├── StatementPreview.tsx           # New: Transaction details preview
│   │       ├── ScanHistoryTable.tsx           # New: Scan history list
│   │       └── ScheduleSettings.tsx           # New: Auto-scan schedule config
│   └── lib/
│       └── api/
│           └── gmail-import.ts                # New: Gmail import API client
└── tests/
    └── components/
        └── gmail-import/
            ├── GmailConnectButton.test.tsx
            └── StatementPreview.test.tsx
```

**Structure Decision**: Web application structure (existing pattern from 001-core-accounting). New bank parsers use a dedicated `bank_parsers/` subdirectory with Strategy pattern to keep each bank's logic isolated.

## Complexity Tracking

> No constitution violations requiring justification.

N/A
