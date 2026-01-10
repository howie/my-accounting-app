# Implementation Plan: Transaction Entry

**Branch**: `004-transaction-entry` | **Date**: 2026-01-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/004-transaction-entry/spec.md`

## Summary

實作交易輸入功能，讓使用者可以從科目頁面新增交易，並支援快速記帳模板。核心功能包括：

- Modal 形式的交易表單（支援表達式計算金額）
- 日期選擇器與欄位驗證
- 交易模板的建立、套用與管理
- Dashboard 上的快速記帳區塊

技術方案：擴展現有的 Next.js + FastAPI + PostgreSQL 架構，新增 TransactionTemplate 資料模型，並在前端實作 Modal 表單元件。

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**:

- Backend: FastAPI, SQLModel, Alembic, Pydantic
- Frontend: Next.js 15, React 19, @tanstack/react-query, date-fns, zod, @dnd-kit (for drag-drop)
  **Storage**: PostgreSQL 16 (via Docker or Supabase)
  **Testing**:
- Backend: pytest, pytest-asyncio, httpx
- Frontend: Vitest, @testing-library/react
  **Target Platform**: Web (Desktop & Mobile responsive)
  **Project Type**: Web application (frontend + backend)
  **Performance Goals**:
- Transaction save: < 1 second response
- Expression calculation: < 100ms
- Template list load: < 500ms
  **Constraints**:
- Must integrate with existing Transaction model from 001-core-accounting
- Must follow i18n patterns (zh-TW, en) from 002-ui-layout-dashboard
- Must respect dark/light mode from 003-settings-account-management
  **Scale/Scope**:
- Up to 30,000 transactions per ledger
- Maximum 50 templates per ledger

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - Yes: FR-010 requires banker's rounding to 2 decimal places
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - Yes: DI-002 requires created_at, updated_at for all transactions
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - Yes: DI-004 requires confirmation for zero-amount transactions; FR-024 requires confirmation for template deletion
- [x] Is input validation enforced (amounts, dates, account references)?
  - Yes: DI-001 validates amount format, range, precision; FR-005 validates different accounts
- [x] Are destructive operations reversible?
  - Yes: Transactions follow existing void-and-reenter pattern from 001-core-accounting

**Violations**: None

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
  - Yes: TDD workflow will be followed per constitution
- [x] Will tests be reviewed/approved before coding?
  - Yes: Test approval gate included in tasks.md
- [x] Are contract tests planned for service boundaries?
  - Yes: API endpoints will have contract tests
- [x] Are integration tests planned for multi-account transactions?
  - Yes: Transaction creation with From/To accounts will have integration tests
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - Yes: Expression calculation, zero-amount, max-value edge cases identified in spec

**Violations**: None

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - Yes: DI-003 enforces double-entry; extends existing 001-core-accounting validation
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - Yes: Follows existing pattern from 001-core-accounting
- [x] Are calculations traceable to source transactions?
  - Yes: DI-005 requires storing original expression if used
- [x] Are timestamps tracked (created, modified, business date)?
  - Yes: Transaction has date (business), created_at, updated_at
- [x] Is change logging implemented (who, what, when, why)?
  - Yes: Leverages existing audit_log from 003-settings-account-management

**Violations**: None

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
  - Yes: Core user workflow - adding transactions is the primary app function
- [x] Is the design clear over clever (human-auditable)?
  - Yes: Standard form + modal pattern; expression parser is well-defined
- [x] Are abstractions minimized (especially for financial calculations)?
  - Yes: Direct calculation with banker's rounding, no complex abstraction layers
- [x] Are complex business rules documented with accounting references?
  - Yes: Double-entry rules reference 001-core-accounting spec

**Violations**: None

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
  - Yes: Backend performs all financial calculations with Python Decimal
- [x] Is data format compatible between desktop and web?
  - Yes: Same PostgreSQL database, same API
- [x] Are platform-specific features clearly documented?
  - N/A: Web-only feature, no platform-specific behavior
- [x] Do workflows follow consistent UX patterns?
  - Yes: Modal dialog pattern consistent with 003-settings-account-management
- [x] Does cloud sync maintain transaction ordering?
  - N/A: No cloud sync in this feature scope

**Violations**: None

**Overall Assessment**: PASS

## Project Structure

### Documentation (this feature)

```text
docs/features/004-transaction-entry/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI specs)
│   ├── transactions.yaml
│   └── templates.yaml
├── tasks.md             # Phase 2 output (/speckit.tasks command)
├── checklists/          # Quality validation
│   └── requirements.md
└── issues/              # Issue tracking for this feature
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── transaction.py      # Existing - extend with notes field
│   │   └── transaction_template.py  # NEW
│   ├── schemas/
│   │   ├── transaction.py      # Existing - extend
│   │   └── transaction_template.py  # NEW
│   ├── services/
│   │   ├── transaction_service.py   # Existing - extend
│   │   └── template_service.py      # NEW
│   └── api/routes/
│       ├── transactions.py     # Existing - extend
│       └── templates.py        # NEW
└── tests/
    ├── contract/
    │   ├── test_transaction_create.py   # Existing - extend
    │   └── test_template_crud.py        # NEW
    ├── integration/
    │   ├── test_transaction_entry.py    # NEW
    │   └── test_template_apply.py       # NEW
    └── unit/
        ├── test_expression_parser.py    # NEW
        └── test_template_service.py     # NEW

frontend/
├── src/
│   ├── components/
│   │   ├── transactions/
│   │   │   ├── TransactionModal.tsx     # NEW
│   │   │   ├── TransactionForm.tsx      # NEW
│   │   │   ├── AmountInput.tsx          # NEW (with calculator)
│   │   │   └── AccountSelect.tsx        # NEW
│   │   ├── templates/
│   │   │   ├── TemplateList.tsx         # NEW
│   │   │   ├── TemplateCard.tsx         # NEW
│   │   │   ├── SaveTemplateDialog.tsx   # NEW
│   │   │   └── QuickEntryPanel.tsx      # NEW (Dashboard component)
│   │   └── ui/
│   │       └── DatePicker.tsx           # NEW or extend existing
│   ├── lib/
│   │   ├── hooks/
│   │   │   ├── useTransactions.ts       # Existing - extend with create mutation
│   │   │   └── useTemplates.ts          # NEW
│   │   └── utils/
│   │       └── expressionParser.ts      # NEW
│   └── app/
│       └── [ledgerId]/
│           └── accounts/
│               └── [accountId]/
│                   └── page.tsx         # Existing - add TransactionModal
└── tests/
    ├── components/
    │   ├── transactions/
    │   │   ├── TransactionModal.test.tsx    # NEW
    │   │   ├── TransactionForm.test.tsx     # NEW
    │   │   └── AmountInput.test.tsx         # NEW
    │   └── templates/
    │       ├── TemplateList.test.tsx        # NEW
    │       └── QuickEntryPanel.test.tsx     # NEW
    ├── lib/
    │   └── utils/
    │       └── expressionParser.test.ts     # NEW
    └── integration/
        └── transaction-entry.test.tsx       # NEW
```

**Structure Decision**: Web application structure matching existing 001/002/003 feature patterns. Backend uses Python FastAPI with SQLModel; Frontend uses Next.js 15 with App Router.

## Complexity Tracking

No constitution violations - complexity tracking not required.
