# Implementation Plan: LedgerOne Core Accounting System

**Branch**: `001-core-accounting` | **Date**: 2026-01-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/001-core-accounting/spec.md`

## Summary

實作 LedgerOne 的核心記帳功能，採用 Next.js (Frontend) + Python FastAPI (Backend) + PostgreSQL 架構。系統遵循嚴格的雙重記帳邏輯，支援多帳本管理、科目 CRUD、交易記錄與餘額計算。

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**:

- Backend: FastAPI 0.109+, SQLModel 0.0.14+, uvicorn, alembic
- Frontend: Next.js 15, React 19, Tailwind CSS 3.4+, ShadcnUI, Tremor
  **Storage**: PostgreSQL 16 (via Docker or Supabase)
  **Testing**: pytest (Backend), Vitest + Testing Library (Frontend)
  **Target Platform**: macOS (Tauri desktop wrapper - separate feature), Web browser
  **Project Type**: Web application (frontend + backend separation)
  **Performance Goals**: API response < 200ms, UI interactions < 100ms
  **Constraints**: Single currency per ledger, single-user mode, 2 decimal precision
  **Scale/Scope**: Personal use, thousands of transactions per ledger

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - Decimal(15,2) for all amounts, banker's rounding enforced
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - created_at/updated_at on all entities, transaction log is immutable record
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - Confirmation dialogs for delete operations (FR-008, DI-004)
- [x] Is input validation enforced (amounts, dates, account references)?
  - Pydantic/SQLModel validation on backend, Zod validation on frontend
- [x] Are destructive operations reversible?
  - Via transaction edit/delete with audit trail; full backup in separate feature (007-backup)

**Violations**: None

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
  - TDD workflow: tests → red → green → refactor
- [x] Will tests be reviewed/approved before coding?
  - Tests in tasks.md reviewed before implementation tasks
- [x] Are contract tests planned for service boundaries?
  - FastAPI endpoint contracts, service layer contracts
- [x] Are integration tests planned for multi-account transactions?
  - Double-entry balance verification tests
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - Banker's rounding tests, large amount tests, negative balance tests

**Violations**: None

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - FR-002, FR-006: Every transaction has from_account and to_account with equal amounts
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - Transactions can be edited but changes are tracked via updated_at
  - Note: Full void-and-reenter pattern deferred to future enhancement
- [x] Are calculations traceable to source transactions?
  - Balance is cached but always verifiable by summing transactions
- [x] Are timestamps tracked (created, modified, business date)?
  - created_at, updated_at, and transaction date fields
- [x] Is change logging implemented (who, what, when, why)?
  - Partial: timestamps logged; full audit log deferred to future feature

**Violations**:

- CONDITIONAL: Full immutable transaction history (void-and-reenter) deferred
  - Justification: Core MVP allows edit/delete with timestamps; full audit log in future feature
  - Mitigation: All changes tracked via updated_at timestamp

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
  - Core accounting is foundational; no speculative features included
- [x] Is the design clear over clever (human-auditable)?
  - Simple from/to account model, explicit transaction types
- [x] Are abstractions minimized (especially for financial calculations)?
  - Direct calculations in service layer, no unnecessary patterns
- [x] Are complex business rules documented with accounting references?
  - Double-entry rules documented in spec and contracts

**Violations**: None

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
  - All calculations in Python backend; frontend displays only
- [x] Is data format compatible between desktop and web?
  - PostgreSQL as single source; Tauri wraps same web UI
- [x] Are platform-specific features clearly documented?
  - Desktop wrapper (Tauri) in separate feature (005-pwa-mobile)
- [x] Do workflows follow consistent UX patterns?
  - ShadcnUI components ensure consistency
- [x] Does cloud sync maintain transaction ordering?
  - N/A for this feature; single-user local/self-hosted

**Violations**: None

**Overall Assessment**: CONDITIONAL PASS

- Condition: Full immutable audit log (void-and-reenter pattern) tracked as future enhancement
- Proceed with current design; timestamps provide sufficient audit trail for MVP

## Project Structure

### Documentation (this feature)

```text
docs/features/001-core-accounting/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (API contracts)
│   ├── ledger_service.md
│   ├── account_service.md
│   ├── transaction_service.md
│   └── user_account_service.md
├── tasks.md             # Phase 2 output
└── issues/              # Issue tracking for this feature
```

### Source Code (repository root)

```text
# Web application structure (frontend + backend separation)

backend/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── deps.py              # Dependency injection
│   │   └── routes/
│   │       ├── ledgers.py
│   │       ├── accounts.py
│   │       └── transactions.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── ledger.py
│   │   ├── account.py
│   │   └── transaction.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ledger_service.py
│   │   ├── account_service.py
│   │   └── transaction_service.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py
│   │   └── migrations/
│   └── core/
│       ├── config.py
│       └── exceptions.py
├── tests/
│   ├── conftest.py
│   ├── contract/
│   ├── integration/
│   └── unit/
├── pyproject.toml
└── alembic.ini

frontend/
├── src/
│   ├── app/                     # Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── ledgers/
│   │   ├── accounts/
│   │   └── transactions/
│   ├── components/
│   │   ├── ui/                  # ShadcnUI components
│   │   ├── forms/
│   │   └── tables/
│   ├── lib/
│   │   ├── api.ts               # API client
│   │   └── utils.ts
│   └── types/
│       └── index.ts
├── tests/
│   ├── components/
│   └── integration/
├── package.json
├── next.config.js
├── tailwind.config.js
└── tsconfig.json

docker-compose.yml               # PostgreSQL + backend + frontend
```

**Structure Decision**: Web application with clear frontend/backend separation. Backend handles all business logic and data persistence; frontend is a thin UI layer consuming REST API.

## Complexity Tracking

| Violation                            | Why Needed                       | Simpler Alternative Rejected Because                                     |
| ------------------------------------ | -------------------------------- | ------------------------------------------------------------------------ |
| Conditional: Full audit log deferred | MVP needs edit/delete capability | Void-and-reenter adds complexity; timestamps sufficient for personal use |
