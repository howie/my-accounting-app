# Implementation Plan: UI Layout Improvement with Sidebar Navigation and Dashboard

**Branch**: `002-ui-layout-dashboard` | **Date**: 2026-01-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/002-ui-layout-dashboard/spec.md`

## Summary

重新設計應用程式的 UI 布局，採用 Mirauve 風格的儀表板設計。新布局包含：深色左側邊欄導航（按科目類別分組：Assets, Loans, Income, Expenses）、主內容區顯示交易明細、以及儀表板首頁顯示總資產、收支摘要（甜甜圈圖）和月度趨勢（柱狀圖）。

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**:

- Backend: FastAPI 0.109+, SQLModel 0.0.14+ (existing)
- Frontend: Next.js 15, React 19, Tailwind CSS 3.4+, ShadcnUI, Tremor (charts)
  **Storage**: PostgreSQL 16 (existing data model from 001-core-accounting)
  **Testing**: pytest (Backend), Vitest + Testing Library (Frontend)
  **Target Platform**: Web browser (primary), macOS desktop via Tauri (future)
  **Project Type**: Web application (frontend + backend separation)
  **Performance Goals**: Dashboard load < 2s, Account selection < 1s, API response < 200ms
  **Constraints**: Read-only data display (no CRUD in this feature), responsive 320px-2560px
  **Scale/Scope**: Personal use, 6-month trend data, existing account/transaction data

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - Read-only display; uses existing calculated balances from 001-core-accounting
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - N/A - This feature does not modify data, display only
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - N/A - No destructive operations in this feature
- [x] Is input validation enforced (amounts, dates, account references)?
  - N/A - No data input in this feature
- [x] Are destructive operations reversible?
  - N/A - No destructive operations

**Violations**: None (read-only UI feature)

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
  - Component tests for sidebar, dashboard, transaction list
- [x] Will tests be reviewed/approved before coding?
  - Tests in tasks.md reviewed before implementation tasks
- [x] Are contract tests planned for service boundaries?
  - API endpoint tests for dashboard aggregation endpoints
- [x] Are integration tests planned for multi-account transactions?
  - Dashboard aggregation tests across account types
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - Empty state tests, large dataset tests, 6-month boundary tests

**Violations**: None

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - N/A - Display only, uses existing transaction data
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - N/A - No transaction modifications
- [x] Are calculations traceable to source transactions?
  - Dashboard totals derive from existing account balances and transaction sums
- [x] Are timestamps tracked (created, modified, business date)?
  - N/A - No data creation/modification
- [x] Is change logging implemented (who, what, when, why)?
  - N/A - Read-only feature

**Violations**: None (read-only UI feature)

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
  - Core navigation and dashboard for usability; directly requested
- [x] Is the design clear over clever (human-auditable)?
  - Simple sidebar + content layout, standard chart components
- [x] Are abstractions minimized (especially for financial calculations)?
  - Uses Tremor charts (established library), no custom chart implementations
- [x] Are complex business rules documented with accounting references?
  - Balance calculations reuse 001-core-accounting logic

**Violations**: None

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
  - All calculations in Python backend; frontend displays only
- [x] Is data format compatible between desktop and web?
  - Same API endpoints for web and future Tauri wrapper
- [x] Are platform-specific features clearly documented?
  - Responsive breakpoints documented (320px mobile, 768px tablet, 1024px+ desktop)
- [x] Do workflows follow consistent UX patterns?
  - Mirauve design system applied consistently
- [x] Does cloud sync maintain transaction ordering?
  - N/A for this feature; single-user local/self-hosted

**Violations**: None

**Overall Assessment**: PASS

- Read-only UI feature with no data modifications
- Reuses existing data model and calculation logic from 001-core-accounting

## Project Structure

### Documentation (this feature)

```text
docs/features/002-ui-layout-dashboard/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output (view models only)
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (dashboard API contracts)
│   └── dashboard_service.md
├── tasks.md             # Phase 2 output (/speckit.tasks command)
└── issues/              # Issue tracking for this feature
```

### Source Code (repository root)

```text
# Extends existing web application structure

backend/
├── src/
│   ├── api/
│   │   └── routes/
│   │       ├── dashboard.py      # NEW: Dashboard aggregation endpoints
│   │       └── ...existing...
│   └── services/
│       ├── dashboard_service.py  # NEW: Dashboard calculations
│       └── ...existing...
└── tests/
    └── unit/
        └── test_dashboard_service.py  # NEW

frontend/
├── src/
│   ├── app/
│   │   ├── layout.tsx            # MODIFY: Add sidebar layout
│   │   ├── page.tsx              # MODIFY: Dashboard homepage
│   │   ├── accounts/
│   │   │   └── [id]/
│   │   │       └── page.tsx      # NEW: Account transactions view
│   │   └── ...existing...
│   ├── components/
│   │   ├── layout/               # NEW: Layout components
│   │   │   ├── Sidebar.tsx       # Dark sidebar navigation
│   │   │   ├── SidebarItem.tsx   # Expandable category item
│   │   │   └── MainContent.tsx   # Content area wrapper
│   │   ├── dashboard/            # NEW: Dashboard components
│   │   │   ├── BalanceCard.tsx   # Total assets card
│   │   │   ├── IncomeExpenseChart.tsx  # Donut chart
│   │   │   ├── TrendChart.tsx    # Bar chart (6 months)
│   │   │   └── DashboardGrid.tsx # Layout grid
│   │   └── ...existing...
│   └── lib/
│       └── hooks/
│           └── useDashboard.ts   # NEW: Dashboard data hook
└── tests/
    └── components/
        ├── layout/               # NEW
        └── dashboard/            # NEW
```

**Structure Decision**: Extends existing web application structure. Adds new layout components for sidebar, new dashboard components for charts, and new backend endpoints for dashboard aggregations.

## Complexity Tracking

> No violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| N/A       | N/A        | N/A                                  |
