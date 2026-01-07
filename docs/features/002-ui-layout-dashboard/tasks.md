# Tasks: UI Layout Improvement with Sidebar Navigation and Dashboard

**Input**: Design documents from `/docs/features/002-ui-layout-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/dashboard_service.md

**Tests**: Per MyAB Constitution Principle II (Test-First Development), tests are MANDATORY and MUST be written BEFORE implementation. Tests must be reviewed/approved before coding begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/src/`, `frontend/src/`
- Backend: Python 3.12 + FastAPI
- Frontend: Next.js 15 + React 19 + Tailwind + Tremor

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependencies and create directory structure

- [x] T001 Install Tremor chart library in frontend/package.json
- [x] T002 [P] Create frontend/src/components/layout/ directory
- [x] T003 [P] Create frontend/src/components/dashboard/ directory
- [x] T004 [P] Add sidebar CSS variables to frontend/src/app/globals.css
- [x] T005 [P] Create frontend/src/types/dashboard.ts with view model types from data-model.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend service and API routes that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T006 [P] Contract test for DashboardService in backend/tests/unit/test_dashboard_service.py
- [x] T007 **GATE**: Get test approval from stakeholder before proceeding to implementation
- [x] T008 **GATE**: Verify all tests FAIL (proving they test the missing feature)

### Implementation for Foundational

- [x] T009 Create DashboardService class in backend/src/services/dashboard_service.py
- [x] T010 Implement get_dashboard_summary() with total assets and current month aggregations in backend/src/services/dashboard_service.py
- [x] T011 Implement get_accounts_by_category() in backend/src/services/dashboard_service.py
- [x] T012 Implement get_account_transactions() with pagination in backend/src/services/dashboard_service.py
- [x] T013 Create API routes in backend/src/api/routes/dashboard.py (GET /ledgers/{id}/dashboard, /accounts/by-category, /accounts/{id}/transactions)
- [x] T014 Register dashboard routes in backend/src/api/routes/__init__.py
- [x] T015 Ensure all foundational tests PASS
- [x] T016 Refactor while keeping tests green

**Checkpoint**: Backend APIs ready - user story frontend work can now begin

---

## Phase 3: User Story 1 - View Financial Dashboard (Priority: P1) 🎯 MVP

**Goal**: Dashboard homepage showing total assets, current month income/expenses with donut chart

**Independent Test**: Login and view homepage. See balance overview card with total assets, donut chart with income vs expenses breakdown for current month.

### Tests for User Story 1 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T017 [P] [US1] Component test for BalanceCard in frontend/tests/components/dashboard/BalanceCard.test.tsx
- [ ] T018 [P] [US1] Component test for IncomeExpenseChart in frontend/tests/components/dashboard/IncomeExpenseChart.test.tsx
- [ ] T019 [P] [US1] Component test for DashboardGrid in frontend/tests/components/dashboard/DashboardGrid.test.tsx
- [ ] T020 [P] [US1] Integration test for dashboard page in frontend/tests/integration/dashboard.test.tsx
- [ ] T021 [P] [US1] Edge case test for empty state (no transactions) in frontend/tests/edge_cases/dashboard-empty.test.tsx
- [ ] T022 **GATE**: Get test approval from stakeholder before proceeding to implementation
- [ ] T023 **GATE**: Verify all tests FAIL (proving they test the missing feature)

### Implementation for User Story 1

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T024 [P] [US1] Create useDashboard hook in frontend/src/lib/hooks/useDashboard.ts
- [x] T025 [P] [US1] Create BalanceCard component (large total assets display) in frontend/src/components/dashboard/BalanceCard.tsx
- [x] T026 [P] [US1] Create IncomeExpenseChart component (Tremor DonutChart) in frontend/src/components/dashboard/IncomeExpenseChart.tsx
- [x] T027 [US1] Create DashboardGrid component (layout container) in frontend/src/components/dashboard/DashboardGrid.tsx
- [x] T028 [US1] Update homepage to render Dashboard in frontend/src/app/page.tsx
- [x] T029 [US1] Add empty state messaging when no data exists in frontend/src/components/dashboard/DashboardGrid.tsx
- [ ] T030 [US1] Ensure all US1 tests PASS (green phase of TDD)
- [ ] T031 [US1] Refactor while keeping tests green

**Checkpoint**: Dashboard homepage with total assets and income/expense donut chart functional

---

## Phase 4: User Story 2 - Navigate Account Categories via Sidebar (Priority: P2)

**Goal**: Dark sidebar with expandable categories (Assets, Loans, Income, Expenses) showing accounts

**Independent Test**: View sidebar on any page. Click category to expand/collapse. See accounts listed under each category.

### Tests for User Story 2 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T032 [P] [US2] Component test for Sidebar in frontend/tests/components/layout/Sidebar.test.tsx
- [ ] T033 [P] [US2] Component test for SidebarItem (expand/collapse) in frontend/tests/components/layout/SidebarItem.test.tsx
- [ ] T034 [P] [US2] Test for mobile responsive collapse in frontend/tests/components/layout/Sidebar.mobile.test.tsx
- [ ] T035 [P] [US2] Integration test for sidebar navigation in frontend/tests/integration/sidebar-nav.test.tsx
- [ ] T036 **GATE**: Get test approval from stakeholder
- [ ] T037 **GATE**: Verify all tests FAIL

### Implementation for User Story 2

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T038 [P] [US2] Create useSidebarAccounts hook in frontend/src/lib/hooks/useSidebarAccounts.ts
- [x] T039 [P] [US2] Create SidebarItem component (expandable category) in frontend/src/components/layout/SidebarItem.tsx
- [x] T040 [US2] Create Sidebar component (dark theme container) in frontend/src/components/layout/Sidebar.tsx
- [x] T041 [US2] Create MainContent wrapper component in frontend/src/components/layout/MainContent.tsx
- [x] T042 [US2] Update root layout with sidebar + main content structure in frontend/src/app/layout.tsx
- [x] T043 [US2] Implement mobile hamburger menu toggle in frontend/src/components/layout/Sidebar.tsx
- [x] T044 [US2] Add sidebar state persistence (session storage) in frontend/src/lib/hooks/useSidebarState.ts
- [ ] T045 [US2] Ensure all US2 tests PASS
- [ ] T046 [US2] Refactor while keeping tests green

**Checkpoint**: Sidebar navigation with expandable categories working on all screen sizes

---

## Phase 5: User Story 3 - View Account Transactions (Priority: P2)

**Goal**: Click account in sidebar to display its transactions in main content area

**Independent Test**: Expand category, click account. See transaction list with date, description, amount. Test pagination with many transactions.

### Tests for User Story 3 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T047 [P] [US3] Component test for AccountTransactionList in frontend/tests/components/tables/AccountTransactionList.test.tsx
- [ ] T048 [P] [US3] Test for empty state (no transactions) in frontend/tests/components/tables/AccountTransactionList.empty.test.tsx
- [ ] T049 [P] [US3] Test for pagination in frontend/tests/components/tables/AccountTransactionList.pagination.test.tsx
- [ ] T050 [P] [US3] Integration test for account selection flow in frontend/tests/integration/account-transactions.test.tsx
- [ ] T051 **GATE**: Get test approval from stakeholder
- [ ] T052 **GATE**: Verify all tests FAIL

### Implementation for User Story 3

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T053 [P] [US3] Create useAccountTransactions hook with pagination in frontend/src/lib/hooks/useAccountTransactions.ts
- [x] T054 [US3] Create AccountTransactionList component in frontend/src/components/tables/AccountTransactionList.tsx
- [x] T055 [US3] Create account transactions page in frontend/src/app/accounts/[id]/page.tsx
- [x] T056 [US3] Add account selection highlighting in Sidebar in frontend/src/components/layout/Sidebar.tsx
- [x] T057 [US3] Handle empty state with message in frontend/src/components/tables/AccountTransactionList.tsx
- [x] T058 [US3] Implement infinite scroll or pagination UI in frontend/src/components/tables/AccountTransactionList.tsx
- [ ] T059 [US3] Ensure all US3 tests PASS
- [ ] T060 [US3] Refactor while keeping tests green

**Checkpoint**: Account transaction viewing with pagination fully functional

---

## Phase 6: User Story 4 - View Monthly Financial Trends (Priority: P3)

**Goal**: Bar charts on dashboard showing 6-month income and expense trends

**Independent Test**: View dashboard with historical data. See bar charts for last 6 months of income and expenses. Test with <6 months data.

### Tests for User Story 4 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T061 [P] [US4] Component test for TrendChart (bar chart) in frontend/tests/components/dashboard/TrendChart.test.tsx
- [ ] T062 [P] [US4] Test for partial data (<6 months) in frontend/tests/components/dashboard/TrendChart.partial.test.tsx
- [ ] T063 [P] [US4] Integration test for trend display on dashboard in frontend/tests/integration/dashboard-trends.test.tsx
- [ ] T064 **GATE**: Get test approval from stakeholder
- [ ] T065 **GATE**: Verify all tests FAIL

### Implementation for User Story 4

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T066 [US4] Create TrendChart component (Tremor BarChart) in frontend/src/components/dashboard/TrendChart.tsx
- [x] T067 [US4] Add TrendChart to DashboardGrid in frontend/src/components/dashboard/DashboardGrid.tsx
- [x] T068 [US4] Handle partial data display (< 6 months) in frontend/src/components/dashboard/TrendChart.tsx
- [ ] T069 [US4] Ensure all US4 tests PASS
- [ ] T070 [US4] Refactor while keeping tests green

**Checkpoint**: Full dashboard with trends visualization complete

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T071 [P] Add loading skeletons for dashboard components in frontend/src/components/dashboard/
- [x] T072 [P] Add loading skeletons for sidebar in frontend/src/components/layout/
- [x] T073 [P] Add error boundary handling in frontend/src/app/error.tsx
- [ ] T074 Verify responsive layout on all breakpoints (320px, 768px, 1024px, 2560px)
- [x] T075 [P] Add account name truncation with tooltip in frontend/src/components/layout/SidebarItem.tsx
- [ ] T076 Performance check: Dashboard load < 2s
- [ ] T077 Performance check: Transaction list load < 1s
- [ ] T078 Run quickstart.md validation scenarios
- [x] T079 Update frontend API client with new endpoints in frontend/src/lib/api.ts

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (US1 → US2 → US3 → US4)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - Dashboard uses `/dashboard` endpoint
- **User Story 2 (P2)**: Can start after Foundational - Sidebar uses `/accounts/by-category` endpoint
- **User Story 3 (P2)**: Can start after Foundational - Transaction list uses `/accounts/{id}/transactions` endpoint
  - Integrates with US2 (account selection from sidebar)
- **User Story 4 (P3)**: Can start after Foundational - Uses trends data from `/dashboard` endpoint
  - Integrates with US1 (adds charts to dashboard)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Hooks before components
- Individual components before container components
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- T002, T003, T004, T005 can run in parallel (different files)
- T006 (backend test) can run in parallel with T001-T005 (frontend setup)
- T017, T018, T019, T020, T021 (US1 tests) can run in parallel
- T024, T025, T026 (US1 components) can run in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Component test for BalanceCard in frontend/tests/components/dashboard/BalanceCard.test.tsx"
Task: "Component test for IncomeExpenseChart in frontend/tests/components/dashboard/IncomeExpenseChart.test.tsx"
Task: "Component test for DashboardGrid in frontend/tests/components/dashboard/DashboardGrid.test.tsx"

# After tests approved and failing, launch components in parallel:
Task: "Create useDashboard hook in frontend/src/lib/hooks/useDashboard.ts"
Task: "Create BalanceCard component in frontend/src/components/dashboard/BalanceCard.tsx"
Task: "Create IncomeExpenseChart component in frontend/src/components/dashboard/IncomeExpenseChart.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - backend APIs)
3. Complete Phase 3: User Story 1 (Dashboard with metrics)
4. **STOP and VALIDATE**: Test dashboard independently
5. Deploy/demo if ready - basic dashboard functional!

### Incremental Delivery

1. Complete Setup + Foundational → Backend APIs ready
2. Add User Story 1 (Dashboard) → Deploy/Demo (MVP!)
3. Add User Story 2 (Sidebar) → Deploy/Demo
4. Add User Story 3 (Transactions) → Deploy/Demo
5. Add User Story 4 (Trends) → Deploy/Demo (Full feature!)

### Suggested MVP Scope

**MVP = Setup + Foundational + User Story 1**

This delivers:
- Dashboard homepage with total assets card
- Income/expense donut chart for current month
- Backend APIs ready for future stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- This is a READ-ONLY UI feature - no data modification tasks needed
- Uses existing account/transaction data from 001-core-accounting
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
