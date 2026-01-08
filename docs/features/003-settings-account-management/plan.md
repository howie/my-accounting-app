# Implementation Plan: Settings & Account Management

**Branch**: `003-settings-account-management` | **Date**: 2026-01-07 | **Spec**: [spec.md](./spec.md)
**Status**: Implemented | **Version**: 1.0.0 | **Completed**: 2026-01-07
**Input**: Feature specification from `/docs/features/003-settings-account-management/spec.md`

## Summary

Implement a Settings page accessible from the sidebar with Account Management functionality. Users can create, edit, delete, and reorder accounts (科目) via drag-and-drop, supporting up to 3 levels of hierarchy. Also includes language switching (zh-TW/en) and dark/light theme toggle with preferences persisted in browser local storage.

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**:

- Backend: FastAPI 0.109, SQLModel 0.0.14, Alembic 1.13
- Frontend: Next.js 15.0, React 19.0, TanStack React Query 5.17, next-intl 4.7, Tailwind CSS 3.4
  **Storage**: PostgreSQL 16 (accounts, transactions), Browser localStorage (user preferences)
  **Testing**: pytest 8.0 + pytest-asyncio (backend), Vitest 1.2 + Testing Library (frontend)
  **Target Platform**: Web application (desktop/mobile responsive)
  **Project Type**: Web application (frontend + backend)
  **Performance Goals**: < 100ms response time for account operations, < 1 second for theme/language changes
  **Constraints**: Offline-capable for preference changes (localStorage), 3-level max account hierarchy
  **Scale/Scope**: Single user per ledger, up to 30,000 transactions per database

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - Account management does not modify transaction amounts, only categorization
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - DI-004 requires audit trail for account creation, modification, deletion
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - Delete requires confirmation; accounts with transactions require reassignment first
- [x] Is input validation enforced (amounts, dates, account references)?
  - DI-001 validates account names (1-100 chars, non-empty, unique per parent)
- [x] Are destructive operations reversible?
  - Transaction reassignment preserves data; deleted accounts have no transactions

**Violations**: None

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
  - Tasks will include test-first workflow per constitution
- [x] Will tests be reviewed/approved before coding?
  - Part of PR review process
- [x] Are contract tests planned for service boundaries?
  - Yes, for new account management API endpoints
- [x] Are integration tests planned for multi-account transactions?
  - Yes, for transaction reassignment during account deletion
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - Edge cases: 3-level depth limit, circular reference prevention, duplicate names

**Violations**: None

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - Not directly affected; transaction reassignment maintains existing entries
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - Feature only changes account reference, not transaction amounts
- [x] Are calculations traceable to source transactions?
  - Account balances still calculated from source transactions
- [x] Are timestamps tracked (created, modified, business date)?
  - Existing updated_at timestamps on Account model preserved
- [x] Is change logging implemented (who, what, when, why)?
  - DI-004 requires audit trail; will log account changes

**Violations**: None

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
  - Required per ROADMAP.md, high priority feature
- [x] Is the design clear over clever (human-auditable)?
  - Standard CRUD operations, existing patterns
- [x] Are abstractions minimized (especially for financial calculations)?
  - Reusing existing Account model and services
- [x] Are complex business rules documented with accounting references?
  - Transaction reassignment follows standard account migration patterns

**Violations**: None

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
  - Backend handles all calculations; frontend display only
- [x] Is data format compatible between desktop and web?
  - PostgreSQL database shared across access methods
- [x] Are platform-specific features clearly documented?
  - localStorage for preferences is per-device by design (documented in clarifications)
- [x] Do workflows follow consistent UX patterns?
  - Follows existing sidebar and form patterns from 001/002
- [x] Does cloud sync maintain transaction ordering?
  - Not applicable; preferences intentionally device-local

**Violations**: None

**Overall Assessment**: PASS

## Project Structure

### Documentation (this feature)

```text
docs/features/003-settings-account-management/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (OpenAPI)
├── tasks.md             # Phase 2 output (/speckit.tasks command)
├── checklists/          # Quality validation
│   └── requirements.md  # Spec quality checklist (complete)
└── issues/              # Issue tracking for this feature
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   └── account.py           # Extend: sort_order field
│   ├── schemas/
│   │   └── account.py           # Extend: reorder, reassign schemas
│   ├── services/
│   │   ├── account_service.py   # Extend: reorder, reassign, audit
│   │   └── audit_service.py     # NEW: audit trail logging
│   └── api/routes/
│       └── accounts.py          # Extend: reorder, bulk reassign endpoints
└── tests/
    ├── contract/
    │   └── test_account_api.py  # NEW: contract tests
    ├── integration/
    │   └── test_account_reassign.py  # NEW: reassignment tests
    └── unit/
        ├── test_account_service.py   # Extend: new operations
        └── test_audit_service.py     # NEW: audit tests

frontend/
├── src/
│   ├── app/
│   │   └── settings/
│   │       ├── page.tsx              # NEW: Settings main page
│   │       └── accounts/
│   │           └── page.tsx          # NEW: Account management page
│   ├── components/
│   │   ├── settings/
│   │   │   ├── SettingsNav.tsx       # NEW: Settings navigation
│   │   │   ├── LanguageSelector.tsx  # NEW: Language dropdown
│   │   │   └── ThemeToggle.tsx       # NEW: Dark/light toggle
│   │   └── accounts/
│   │       ├── AccountTree.tsx       # NEW: Draggable account tree
│   │       ├── AccountForm.tsx       # Extend: for create/edit
│   │       └── DeleteAccountDialog.tsx  # NEW: With reassignment
│   ├── lib/
│   │   ├── hooks/
│   │   │   ├── useUserPreferences.ts # NEW: localStorage hook
│   │   │   └── useAccounts.ts        # Extend: reorder mutations
│   │   └── context/
│   │       └── ThemeContext.tsx      # NEW: Theme provider
│   └── types/
│       └── index.ts                  # Extend: preference types
├── messages/
│   ├── en.json                       # Extend: settings translations
│   └── zh-TW.json                    # Extend: settings translations
└── tests/
    ├── components/
    │   └── settings/                 # NEW: component tests
    └── hooks/
        └── useUserPreferences.test.ts  # NEW: hook tests
```

**Structure Decision**: Web application structure (Option 2) - extending existing backend/frontend separation established in 001-core-accounting and 002-ui-layout-dashboard.

## Complexity Tracking

> No constitution violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| N/A       | -          | -                                    |
