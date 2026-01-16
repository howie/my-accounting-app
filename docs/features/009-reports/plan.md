# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]
**Input**: Feature specification from `/docs/features/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature implements the core financial reports defined in `docs/myab-spec/04-reports-analysis.md` (Section 4.1):

1.  **Balance Sheet (資產負債表)**: A point-in-time snapshot showing Assets, Liabilities, and Net Worth (Equity).
2.  **Income Statement (損益表)**: A period-based report showing Income, Expenses, and Net Income.

It also includes the necessary backend APIs to calculate these aggregates and frontend pages to display them with date range filtering.

_Note: Section 4.3 (Closing/Data Purging) is out of scope for this feature and belongs to Data Management._

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript/React (Frontend)
**Primary Dependencies**: FastAPI, Pydantic (Backend); Next.js, Tailwind CSS, Recharts (Frontend)
**Storage**: SQLite (via SQLAlchemy or raw SQL)
**Testing**: pytest (Backend), vitest (Frontend)
**Target Platform**: Web (Desktop/Mobile responsive)
**Project Type**: Full-stack (FastAPI + Next.js)
**Performance Goals**: Report generation < 200ms for typical datasets (< 10k transactions).
**Constraints**:

- Must maintain double-entry accounting integrity in calculations.
- Calculations must be precise (decimal arithmetic, no floating point errors).
- Frontend must allow date range selection.
  **Scale/Scope**: ~2 new pages, ~2 new API endpoints, shared calculation logic.

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

Verify compliance with all five core principles from `.specify/memory/constitution.md`:

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
- [ ] Are audit trails maintained (all modifications logged with timestamp/reason)? (N/A - Read Only)
- [ ] Is data loss prevented (confirmations + backups for destructive operations)? (N/A - Read Only)
- [x] Is input validation enforced (amounts, dates, account references)?
- [ ] Are destructive operations reversible? (N/A - Read Only)

**Violations**: None. Feature is read-only reporting.

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
- [x] Will tests be reviewed/approved before coding?
- [x] Are contract tests planned for service boundaries?
- [ ] Are integration tests planned for multi-account transactions? (N/A - Reporting)
- [x] Are edge case tests planned (rounding, currency, date boundaries)?

**Violations**: None.

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
- [ ] Are transactions immutable once posted (void-and-reenter only)? (N/A - Read Only)
- [x] Are calculations traceable to source transactions?
- [ ] Are timestamps tracked (created, modified, business date)? (N/A - Read Only)
- [ ] Is change logging implemented (who, what, when, why)? (N/A - Read Only)

**Violations**: None.

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
- [x] Is the design clear over clever (human-auditable)?
- [x] Are abstractions minimized (especially for financial calculations)?
- [x] Are complex business rules documented with accounting references?

**Violations**: None.

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
- [x] Is data format compatible between desktop and web?
- [ ] Are platform-specific features clearly documented? (N/A)
- [x] Do workflows follow consistent UX patterns?
- [ ] Does cloud sync maintain transaction ordering? (N/A)

**Violations**: None.

**Overall Assessment**: PASS

## Project Structure

### Documentation (this feature)

```text
docs/features/[###-feature]/
├── spec.md              # Feature specification
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
├── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
└── issues/              # Issue tracking for this feature
```

### Source Code (repository root)

<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation                  | Why Needed         | Simpler Alternative Rejected Because |
| -------------------------- | ------------------ | ------------------------------------ |
| [e.g., 4th project]        | [current need]     | [why 3 projects insufficient]        |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient]  |
