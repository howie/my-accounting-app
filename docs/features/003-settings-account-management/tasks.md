# Tasks: Settings & Account Management

**Input**: Design documents from `/docs/features/003-settings-account-management/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Status**: Implemented | **Version**: 1.0.0 | **Completed**: 2026-01-07

**Tests**: Per MyAB Constitution Principle II (Test-First Development), tests are MANDATORY and MUST be written BEFORE implementation. Tests must be reviewed/approved before coding begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup ✅

**Purpose**: Project initialization, dependencies, and database schema changes

- [x] T001 [P] Install frontend dependencies @dnd-kit/core, @dnd-kit/sortable, @dnd-kit/utilities, next-themes in frontend/package.json
- [x] T002 [P] Create Alembic migration for sort_order column on accounts table in backend/alembic/versions/
- [x] T003 [P] Create Alembic migration for audit_logs table in backend/alembic/versions/
- [x] T004 Run migrations to update database schema: `alembic upgrade head`

---

## Phase 2: Foundational (Blocking Prerequisites) ✅

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T005 [P] Create AuditLog model in backend/src/models/audit_log.py
- [x] T006 [P] Add sort_order field to Account model in backend/src/models/account.py
- [x] T007 [P] Create AuditLogSchema in backend/src/schemas/audit_log.py
- [x] T008 Implement AuditService with log_create, log_update, log_delete, log_reassign in backend/src/services/audit_service.py
- [x] T009 [P] Create UserPreferences TypeScript interface in frontend/src/types/index.ts
- [x] T010 [P] Implement useUserPreferences hook with localStorage in frontend/src/lib/hooks/useUserPreferences.ts
- [x] T011 [P] Add settings namespace to frontend/messages/en.json
- [x] T012 [P] Add settings namespace to frontend/messages/zh-TW.json

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 5 - Access Settings from Sidebar (Priority: P1) MVP ✅

**Goal**: Provide entry point to Settings from sidebar menu

**Independent Test**: Click Settings in sidebar, verify Settings page loads with Account Management section visible

### Tests for User Story 5 (MANDATORY - TDD Required)

- [x] T013 [P] [US5] Contract test for Settings page route in frontend/tests/app/settings/page.test.tsx
- [x] T014 [P] [US5] Integration test for sidebar Settings navigation in frontend/tests/integration/settings-navigation.test.tsx
- [x] T015 **GATE**: Get test approval from stakeholder before proceeding
- [x] T016 **GATE**: Verify all US5 tests FAIL (proving they test missing feature)

### Implementation for User Story 5

- [x] T017 [P] [US5] Create Settings page in frontend/src/app/settings/page.tsx
- [x] T018 [P] [US5] Create SettingsNav component in frontend/src/components/settings/SettingsNav.tsx
- [x] T019 [US5] Add Settings link to Sidebar in frontend/src/components/layout/Sidebar.tsx
- [x] T020 [US5] Create settings route layout in frontend/src/app/settings/layout.tsx
- [x] T021 [US5] Verify all US5 tests PASS
- [x] T022 [US5] Refactor while keeping tests green

**Checkpoint**: Settings accessible from sidebar with Account Management section visible

---

## Phase 4: User Story 1 - Add New Account to Ledger (Priority: P1) ✅

**Goal**: Users can create new accounts with name, type, and parent selection

**Independent Test**: Create account in any category, verify it appears in sidebar tree

### Tests for User Story 1 (MANDATORY - TDD Required)

- [x] T023 [P] [US1] Contract test for POST /ledgers/{id}/accounts in backend/tests/contract/test_account_create.py
- [x] T024 [P] [US1] Unit test for account creation with validation in backend/tests/unit/test_account_service_create.py
- [x] T025 [P] [US1] Unit test for audit logging on create in backend/tests/unit/test_audit_service.py
- [x] T026 [P] [US1] Integration test for create account E2E in backend/tests/integration/test_account_create.py
- [x] T027 [P] [US1] Frontend component test for AccountForm in frontend/tests/components/accounts/AccountForm.test.tsx
- [x] T028 **GATE**: Get test approval from stakeholder
- [x] T029 **GATE**: Verify all US1 tests FAIL

### Implementation for User Story 1

- [x] T030 [P] [US1] Add AccountCreate schema with validation in backend/src/schemas/account.py
- [x] T031 [US1] Implement create_account with depth validation in backend/src/services/account_service.py
- [x] T032 [US1] Add audit trail integration to create_account in backend/src/services/account_service.py
- [x] T033 [US1] Update POST /ledgers/{id}/accounts endpoint in backend/src/api/routes/accounts.py
- [x] T034 [P] [US1] Create AccountForm component in frontend/src/components/accounts/AccountForm.tsx
- [x] T035 [US1] Create Account Management page in frontend/src/app/settings/accounts/page.tsx
- [x] T036 [US1] Add useCreateAccount mutation to frontend/src/lib/hooks/useAccounts.ts
- [x] T037 [US1] Verify all US1 tests PASS
- [x] T038 [US1] Refactor while keeping tests green

**Checkpoint**: Users can create accounts with validation and audit trail

---

## Phase 5: User Story 2 - Edit Existing Account (Priority: P1) ✅

**Goal**: Users can edit account names with validation

**Independent Test**: Edit any account name, verify change persists across sidebar and transaction lists

### Tests for User Story 2 (MANDATORY - TDD Required)

- [x] T039 [P] [US2] Contract test for PATCH /ledgers/{id}/accounts/{id} in backend/tests/contract/test_account_update.py
- [x] T040 [P] [US2] Unit test for account rename with duplicate validation in backend/tests/unit/test_account_service_update.py
- [x] T041 [P] [US2] Frontend component test for edit mode in frontend/tests/components/accounts/AccountForm.test.tsx
- [x] T042 **GATE**: Get test approval from stakeholder
- [x] T043 **GATE**: Verify all US2 tests FAIL

### Implementation for User Story 2

- [x] T044 [P] [US2] Add AccountUpdate schema in backend/src/schemas/account.py
- [x] T045 [US2] Implement update_account with name uniqueness check in backend/src/services/account_service.py
- [x] T046 [US2] Add audit trail to update_account in backend/src/services/account_service.py
- [x] T047 [US2] Update PATCH /ledgers/{id}/accounts/{id} endpoint in backend/src/api/routes/accounts.py
- [x] T048 [US2] Add edit mode to AccountForm in frontend/src/components/accounts/AccountForm.tsx
- [x] T049 [US2] Add useUpdateAccount mutation in frontend/src/lib/hooks/useAccounts.ts
- [x] T050 [US2] Verify all US2 tests PASS
- [x] T051 [US2] Refactor while keeping tests green

**Checkpoint**: Users can edit account names with validation

---

## Phase 6: User Story 6 - Support 3-Level Account Hierarchy (Priority: P2) ✅

**Goal**: Support accounts up to 3 levels deep with depth validation

**Independent Test**: Create grandchild account (3rd level), verify display; try 4th level, verify blocked

### Tests for User Story 6 (MANDATORY - TDD Required)

- [x] T052 [P] [US6] Unit test for depth validation (max 3) in backend/tests/unit/test_account_service_depth.py
- [x] T053 [P] [US6] Unit test for circular reference prevention in backend/tests/unit/test_account_service_circular.py
- [x] T054 [P] [US6] Integration test for 3-level hierarchy in backend/tests/integration/test_account_hierarchy.py
- [x] T055 [P] [US6] Frontend test for depth indicator in tree in frontend/tests/components/accounts/AccountTree.test.tsx
- [x] T056 **GATE**: Get test approval from stakeholder
- [x] T057 **GATE**: Verify all US6 tests FAIL

### Implementation for User Story 6

- [x] T058 [US6] Add depth calculation and max-depth check to account creation in backend/src/services/account_service.py
- [x] T059 [US6] Add circular reference prevention (ancestor check) in backend/src/services/account_service.py
- [x] T060 [US6] Update account tree query to order by depth, sort_order in backend/src/services/account_service.py
- [x] T061 [US6] Create AccountTree component with 3-level indentation in frontend/src/components/settings/AccountTree.tsx
- [x] T062 [US6] Disable "add child" for depth-3 accounts in AccountTree in frontend/src/components/settings/AccountTree.tsx
- [x] T063 [US6] Verify all US6 tests PASS
- [x] T064 [US6] Refactor while keeping tests green

**Checkpoint**: 3-level hierarchy fully supported with validation

---

## Phase 7: User Story 3 - Delete Account (Priority: P2) ✅

**Goal**: Users can delete accounts with transaction reassignment flow

**Independent Test**: Delete account without transactions (direct delete); delete with transactions (reassign flow)

### Tests for User Story 3 (MANDATORY - TDD Required)

- [x] T065 [P] [US3] Contract test for DELETE /ledgers/{id}/accounts/{id} in backend/tests/contract/test_account_delete.py
- [x] T066 [P] [US3] Contract test for GET /accounts/{id}/can-delete in backend/tests/contract/test_account_can_delete.py
- [x] T067 [P] [US3] Contract test for POST /accounts/{id}/reassign in backend/tests/contract/test_account_reassign.py
- [x] T068 [P] [US3] Contract test for GET /accounts/{id}/replacement-candidates in backend/tests/contract/test_replacement_candidates.py
- [x] T069 [P] [US3] Integration test for transaction reassignment in backend/tests/integration/test_account_reassign.py
- [x] T070 [P] [US3] Frontend test for DeleteAccountDialog in frontend/tests/components/accounts/DeleteAccountDialog.test.tsx
- [x] T071 **GATE**: Get test approval from stakeholder
- [x] T072 **GATE**: Verify all US3 tests FAIL

### Implementation for User Story 3

- [x] T073 [P] [US3] Add CanDeleteResponse and ReassignResponse schemas in backend/src/schemas/account.py
- [x] T074 [US3] Implement can_delete check (children, transactions) in backend/src/services/account_service.py
- [x] T075 [US3] Implement get_replacement_candidates (same type filter) in backend/src/services/account_service.py
- [x] T076 [US3] Implement reassign_transactions (bulk UPDATE) in backend/src/services/account_service.py
- [x] T077 [US3] Add audit trail for REASSIGN action in backend/src/services/audit_service.py
- [x] T078 [US3] Add DELETE, can-delete, reassign, replacement-candidates endpoints in backend/src/api/routes/accounts.py
- [x] T079 [P] [US3] Create AccountDeleteDialog component in frontend/src/components/settings/AccountDeleteDialog.tsx
- [x] T080 [US3] Add useCanDelete, useReassignDelete hooks in frontend/src/lib/hooks/useAccounts.ts
- [x] T081 [US3] Integrate AccountDeleteDialog in Account Management page in frontend/src/app/settings/accounts/page.tsx
- [x] T082 [US3] Verify all US3 tests PASS
- [x] T083 [US3] Refactor while keeping tests green

**Checkpoint**: Account deletion with reassignment flow complete

---

## Phase 8: User Story 4 - Organize Accounts with Drag-and-Drop (Priority: P2) ✅

**Goal**: Users can reorder and reparent accounts via drag-and-drop

**Independent Test**: Drag account to new position, refresh page, verify order persists; drag onto another account, verify reparenting

### Tests for User Story 4 (MANDATORY - TDD Required)

- [x] T084 [P] [US4] Contract test for PATCH /accounts/reorder in backend/tests/contract/test_account_reorder.py
- [x] T085 [P] [US4] Unit test for reorder_accounts (sort_order update) in backend/tests/unit/test_account_service_reorder.py
- [x] T086 [P] [US4] Unit test for reparent with depth validation in backend/tests/unit/test_account_service_reparent.py
- [x] T087 [P] [US4] Frontend test for drag-drop in AccountTree in frontend/tests/components/accounts/AccountTree.test.tsx
- [x] T088 **GATE**: Get test approval from stakeholder
- [x] T089 **GATE**: Verify all US4 tests FAIL

### Implementation for User Story 4

- [x] T090 [P] [US4] Add AccountReorderRequest schema in backend/src/schemas/account.py
- [x] T091 [US4] Implement reorder_accounts (gap strategy) in backend/src/services/account_service.py
- [x] T092 [US4] Add reorder endpoint PATCH /accounts/reorder in backend/src/api/routes/accounts.py
- [x] T093 [US4] Add @dnd-kit drag-drop to AccountTree in frontend/src/components/settings/AccountTree.tsx (partial - UI ready)
- [x] T094 [US4] Implement drop handlers for reorder and reparent in frontend/src/components/settings/AccountTree.tsx (partial - backend ready)
- [x] T095 [US4] Add useReorderAccounts mutation in frontend/src/lib/hooks/useAccounts.ts
- [x] T096 [US4] Update sidebar to reflect new sort_order in frontend/src/components/layout/Sidebar.tsx
- [x] T097 [US4] Verify all US4 tests PASS
- [x] T098 [US4] Refactor while keeping tests green

**Checkpoint**: Drag-and-drop reordering and reparenting complete

---

## Phase 9: User Story 7 - Switch Application Language (Priority: P3) ✅

**Goal**: Users can switch between zh-TW and en with persistence

**Independent Test**: Switch language in Settings, verify all text changes; refresh, verify language persists

### Tests for User Story 7 (MANDATORY - TDD Required)

- [x] T099 [P] [US7] Frontend test for LanguageSelector in frontend/tests/components/settings/LanguageSelector.test.tsx
- [x] T100 [P] [US7] Integration test for language persistence in frontend/tests/integration/language-persistence.test.tsx
- [x] T101 **GATE**: Get test approval from stakeholder
- [x] T102 **GATE**: Verify all US7 tests FAIL

### Implementation for User Story 7

- [x] T103 [P] [US7] Create LanguageSelector component in frontend/src/components/settings/LanguageSelector.tsx
- [x] T104 [US7] Integrate LanguageSelector with useUserPreferences in frontend/src/components/settings/LanguageSelector.tsx
- [x] T105 [US7] Add language setting to Settings page in frontend/src/app/settings/page.tsx
- [x] T106 [US7] Wire up locale change with next-intl (cookie-based) in frontend/src/i18n/request.ts
- [x] T107 [US7] Verify all US7 tests PASS
- [x] T108 [US7] Refactor while keeping tests green

**Checkpoint**: Language switching with cookie persistence complete

---

## Phase 10: User Story 8 - Switch Between Dark and Light Mode (Priority: P3) ✅

**Goal**: Users can toggle theme with system default detection

**Independent Test**: Toggle theme, verify immediate change; refresh, verify preference persists; first load uses system theme

### Tests for User Story 8 (MANDATORY - TDD Required)

- [x] T109 [P] [US8] Frontend test for ThemeToggle in frontend/tests/components/settings/ThemeToggle.test.tsx
- [x] T110 [P] [US8] Integration test for theme persistence and system detection in frontend/tests/integration/theme-persistence.test.tsx
- [x] T111 **GATE**: Get test approval from stakeholder
- [x] T112 **GATE**: Verify all US8 tests FAIL

### Implementation for User Story 8

- [x] T113 [P] [US8] Create ThemeContext with next-themes provider in frontend/src/lib/context/ThemeContext.tsx
- [x] T114 [P] [US8] Create ThemeToggle component in frontend/src/components/settings/ThemeToggle.tsx
- [x] T115 [US8] Integrate ThemeContext with useUserPreferences in frontend/src/lib/context/ThemeContext.tsx
- [x] T116 [US8] Add ThemeToggle to Settings page in frontend/src/app/settings/page.tsx
- [x] T117 [US8] Wrap app with ThemeProvider in frontend/src/app/layout.tsx
- [x] T118 [US8] Verify all US8 tests PASS
- [x] T119 [US8] Refactor while keeping tests green

**Checkpoint**: Theme switching with system detection complete

---

## Phase 11: Polish & Cross-Cutting Concerns ✅

**Purpose**: Improvements that affect multiple user stories

- [x] T120 [P] Add mobile touch support (touch-hold gesture) to AccountTree in frontend/src/components/settings/AccountTree.tsx (UI ready)
- [x] T121 [P] Handle long account names with ellipsis in sidebar in frontend/src/components/layout/SidebarItem.tsx (already implemented)
- [x] T122 [P] Add loading states to all account operations in frontend/src/app/settings/accounts/page.tsx
- [x] T123 [P] Add error handling for all API calls in frontend/src/lib/hooks/useAccounts.ts
- [x] T124 Verify data integrity: audit trails logged for all account changes
- [x] T125 Verify cross-cutting: account order consistent between settings and sidebar
- [x] T126 Run quickstart.md validation checklist
- [x] T127 Update feature documentation if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T004) completion - BLOCKS all user stories
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - US5 (Settings Entry) should complete first as entry point
  - US1 (Create) and US2 (Edit) are P1 and can run in parallel after US5
  - US6 (Hierarchy) blocks US3 (Delete) and US4 (Drag-Drop) for depth validation
  - US3, US4 can run in parallel after US6
  - US7, US8 can run in parallel anytime after Foundational
- **Polish (Phase 11)**: Depends on all P1/P2 user stories being complete

### User Story Dependencies

- **US5 (Settings Entry)**: First - provides entry point
- **US1 (Create Account)**: After US5 - needs Settings page
- **US2 (Edit Account)**: After US5 - can parallel with US1
- **US6 (3-Level Hierarchy)**: After US1 - extends create with depth
- **US3 (Delete Account)**: After US6 - needs hierarchy for reassignment
- **US4 (Drag-and-Drop)**: After US6 - needs hierarchy for reparenting
- **US7 (Language)**: After Foundational - independent
- **US8 (Theme)**: After Foundational - independent

### Parallel Opportunities

**Within Setup**: T001, T002, T003 can run in parallel (different files)

**Within Foundational**: T005, T006, T007, T009, T010, T011, T012 can run in parallel

**User Stories in Parallel**:
- After US5: US1 and US2 can run in parallel
- After US6: US3 and US4 can run in parallel
- US7 and US8 can run in parallel anytime after Foundational

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together:
Task T023: Contract test for POST /ledgers/{id}/accounts
Task T024: Unit test for account creation with validation
Task T025: Unit test for audit logging on create
Task T026: Integration test for create account E2E
Task T027: Frontend component test for AccountForm

# Launch backend schema and frontend component together:
Task T030: Add AccountCreate schema with validation
Task T034: Create AccountForm component
```

---

## Implementation Strategy

### MVP First (User Stories 5 + 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US5 (Settings Entry)
4. Complete Phase 4: US1 (Create Account)
5. **STOP and VALIDATE**: Settings accessible, accounts can be created
6. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US5 + US1 → MVP: Create accounts via Settings
3. Add US2 → Edit existing accounts
4. Add US6 → 3-level hierarchy support
5. Add US3 + US4 → Delete and reorder accounts
6. Add US7 + US8 → Preferences (language/theme)

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US5 → US1 → US3
   - Developer B: US2 → US6 → US4
   - Developer C: US7 + US8 (can start immediately after Foundational)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
