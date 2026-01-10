# Tasks: Transaction Entry

**Input**: Design documents from `/docs/features/004-transaction-entry/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

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

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, migrations, and shared utilities

- [x] T001 Create database migration for Transaction model extensions (notes, amount_expression) in backend/alembic/versions/004_add_transaction_notes.py
- [x] T002 Create database migration for TransactionTemplate table in backend/alembic/versions/004_create_transaction_templates.py
- [x] T003 [P] Create TransactionTemplate SQLModel in backend/src/models/transaction_template.py
- [x] T004 [P] Extend Transaction model with notes and amount_expression fields in backend/src/models/transaction.py
- [x] T005 [P] Create expression parser utility in frontend/src/lib/utils/expressionParser.ts
- [x] T006 Add i18n keys for transactions and templates in frontend/src/locales/zh-TW.json and frontend/src/locales/en.json

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 Run migrations and verify database schema in backend
- [x] T008 [P] Create TransactionTemplate Pydantic schemas (Create, Update, Response) in backend/src/schemas/transaction_template.py
- [x] T009 [P] Extend Transaction Pydantic schemas with notes and amount_expression in backend/src/schemas/transaction.py
- [x] T010 [P] Create template service with CRUD operations in backend/src/services/template_service.py
- [x] T011 Extend transaction service with expression validation in backend/src/services/transaction_service.py
- [x] T012 [P] Create useTemplates hook (list, create, update, delete, reorder) in frontend/src/lib/hooks/useTemplates.ts
- [x] T013 Extend useTransactions hook with create mutation in frontend/src/lib/hooks/useTransactions.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Add Transaction from Account Page (Priority: P1) MVP

**Goal**: Users can add transactions directly from the account page via a modal dialog

**Independent Test**: Click "Add Transaction" on account page, fill form, save - transaction appears in list immediately

### Tests for User Story 1 (MANDATORY - TDD Required)

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**
> Per Constitution Principle II: Tests -> Approval -> Red -> Green -> Refactor

- [x] T014 [P] [US1] Contract test for POST /api/ledgers/{id}/transactions in backend/tests/contract/test_transaction_create.py
- [x] T015 [P] [US1] Integration test for transaction entry flow in backend/tests/integration/test_transaction_entry.py
- [x] T016 [P] [US1] Unit test for expression parser in frontend/tests/lib/utils/expressionParser.test.ts
- [x] T017 [P] [US1] Component test for TransactionModal in frontend/tests/components/transactions/TransactionModal.test.tsx
- [x] T018 [P] [US1] Component test for TransactionForm in frontend/tests/components/transactions/TransactionForm.test.tsx
- [x] T018A [P] [US1] Edge case test for zero-amount confirmation dialog in frontend/tests/components/transactions/TransactionForm.test.tsx
- [x] T019 **GATE**: Get test approval from stakeholder before proceeding to implementation
- [x] T020 **GATE**: Verify all tests FAIL (proving they test the missing feature)

### Implementation for User Story 1

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T021 [US1] Implement POST /api/ledgers/{id}/transactions endpoint in backend/src/api/routes/transactions.py
- [x] T022 [US1] Add double-entry validation (from != to account) in transaction service
- [x] T023 [US1] Add expression validation (amount matches expression result) in transaction service
- [x] T024 [P] [US1] Create AccountSelect component with hierarchical dropdown in frontend/src/components/transactions/AccountSelect.tsx
- [x] T025 [P] [US1] Create AmountInput component with expression calculator in frontend/src/components/transactions/AmountInput.tsx
- [x] T026 [US1] Create TransactionForm component with all fields in frontend/src/components/transactions/TransactionForm.tsx
- [x] T027 [US1] Create TransactionModal component wrapping form in frontend/src/components/transactions/TransactionModal.tsx
- [x] T028 [US1] Add "Add Transaction" button to account page in frontend/src/app/accounts/[id]/page.tsx
- [x] T029 [US1] Implement account pre-selection based on account type (Asset/Expense -> From, Income/Liability -> To)
- [x] T030 [US1] Implement auto-suggest transaction type based on From account type
- [x] T031 [US1] Add form validation (description required, amount range, different accounts)
- [x] T031A [US1] Implement zero-amount warning dialog per DI-004 in TransactionForm
- [x] T032 [US1] Implement optimistic UI update on transaction save (via React Query cache invalidation)
- [x] T033 [US1] Ensure all tests PASS (green phase of TDD) - 142 frontend + 532 backend tests passing
- [x] T034 [US1] Refactor while keeping tests green

**Checkpoint**: User Story 1 complete - users can add transactions from account page

---

## Phase 4: User Story 2 - Smart Amount Input with Calculator (Priority: P1) MVP

**Goal**: Users can enter arithmetic expressions in amount field that auto-calculate

**Independent Test**: Enter "50+40+10" in amount field, blur - displays 100

### Tests for User Story 2 (MANDATORY - TDD Required)

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T035 [P] [US2] Unit test for expression edge cases (division by zero, invalid syntax) in frontend/tests/lib/utils/expressionParser.test.ts (52 tests)
- [x] T036 [P] [US2] Component test for AmountInput expression handling in frontend/tests/components/transactions/TransactionForm.test.tsx (expression evaluation test)
- [x] T037 **GATE**: Get test approval from stakeholder
- [x] T038 **GATE**: Verify all tests FAIL

### Implementation for User Story 2

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T039 [US2] Implement recursive descent parser with operator precedence in frontend/src/lib/utils/expressionParser.ts
- [x] T040 [US2] Add banker's rounding (2 decimal places) to expression parser
- [x] T041 [US2] Add error state for invalid expressions in AmountInput component
- [x] T042 [US2] Add expression preview/edit toggle in AmountInput component (focus/blur behavior)
- [x] T043 [US2] Store original expression in amountExpression field on save
- [x] T044 [US2] Ensure all tests PASS (52 expression parser tests passing)
- [x] T045 [US2] Refactor while keeping tests green

**Checkpoint**: User Story 2 complete - amount calculator works

---

## Phase 5: User Story 3 - Select Date for Transaction (Priority: P1) MVP

**Goal**: Users can select transaction date via date picker with today as default

**Independent Test**: Open form - date defaults to today; select yesterday - transaction saves with correct date

### Tests for User Story 3 (MANDATORY - TDD Required)

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T046 [P] [US3] Component test for DatePicker in frontend/tests/components/transactions/TransactionForm.test.tsx (date default test)
- [x] T047 [P] [US3] Integration test for date handling in frontend/tests/components/transactions/TransactionForm.test.tsx
- [x] T048 **GATE**: Get test approval from stakeholder
- [x] T049 **GATE**: Verify all tests FAIL

### Implementation for User Story 3

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T050 [US3] Using HTML5 date input for MVP (can upgrade to shadcn/ui Calendar later)
- [ ] T051 [US3] Add "Today" quick-select button to DatePicker (P3 - future enhancement)
- [x] T052 [US3] Set default date to today on form open (implemented in TransactionForm)
- [x] T053 [US3] Implement locale-aware date formatting (using browser native)
- [x] T054 [US3] Ensure all tests PASS
- [x] T055 [US3] Refactor while keeping tests green

**Checkpoint**: User Stories 1, 2, 3 complete - basic transaction entry MVP ready

---

## Phase 6: User Story 4 - Add Description and Notes (Priority: P2)

**Goal**: Users can add required description and optional notes to transactions

**Independent Test**: Save transaction without description - shows validation error; with description and notes - both saved correctly

### Tests for User Story 4 (MANDATORY - TDD Required)

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T056 [P] [US4] Contract test for notes field in transaction response in backend/tests/contract/test_transaction_create.py
- [x] T057 [P] [US4] Component test for description/notes validation in frontend/tests/components/transactions/TransactionForm.test.tsx
- [x] T058 **GATE**: Get test approval from stakeholder
- [x] T059 **GATE**: Verify all tests FAIL

### Implementation for User Story 4

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T060 [US4] Add notes field to TransactionForm with 500 char limit
- [x] T061 [US4] Add description field validation (required, max 200 chars)
- [ ] T062 [US4] Display notes in transaction detail view (P3 - future enhancement)
- [x] T063 [US4] Ensure all tests PASS
- [x] T064 [US4] Refactor while keeping tests green

**Checkpoint**: User Story 4 complete - description and notes work

---

## Phase 7: User Story 5 - Save Transaction Template (Priority: P2)

**Goal**: Users can save transaction form values as reusable named templates

**Independent Test**: Fill form, click "Save as Template", enter name - template appears in template list

### Tests for User Story 5 (MANDATORY - TDD Required)

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T065 [P] [US5] Contract test for POST /api/ledgers/{id}/templates in backend/tests/contract/test_template_endpoints.py
- [x] T066 [P] [US5] Contract test for GET /api/ledgers/{id}/templates in backend/tests/contract/test_template_endpoints.py
- [x] T067 [P] [US5] Integration test for template creation in backend/tests/integration/test_transaction_flow.py (template tests in test_template_service.py)
- [x] T068 [P] [US5] Unit test for template service in backend/tests/contract/test_template_service.py
- [x] T069 [P] [US5] Component test for SaveTemplateDialog in frontend/tests/components/templates/SaveTemplateDialog.test.tsx
- [x] T070 **GATE**: Get test approval from stakeholder
- [x] T071 **GATE**: Verify all tests FAIL (verified before implementation)

### Implementation for User Story 5

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T072 [US5] Implement GET /api/ledgers/{id}/templates endpoint in backend/src/api/routes/templates.py
- [x] T073 [US5] Implement POST /api/ledgers/{id}/templates endpoint in backend/src/api/routes/templates.py
- [x] T074 [US5] Add template limit validation (max 50 per ledger) in template service
- [x] T075 [US5] Add unique name validation per ledger in template service
- [x] T076 [P] [US5] Create SaveTemplateDialog component in frontend/src/components/templates/SaveTemplateDialog.tsx
- [x] T077 [P] [US5] Create TemplateCard component in frontend/src/components/templates/TemplateCard.tsx
- [x] T078 [US5] Create TemplateList component in frontend/src/components/templates/TemplateList.tsx
- [x] T079 [US5] Add "Save as Template" button to TransactionForm
- [x] T080 [US5] Ensure all tests PASS (171 frontend + 532 backend tests passing)
- [x] T081 [US5] Refactor while keeping tests green

**Checkpoint**: User Story 5 complete - can save templates

---

## Phase 8: User Story 6 - Quick Apply Template (Priority: P2)

**Goal**: Users can quickly create transactions from templates via Dashboard quick-entry panel

**Independent Test**: Click template button on Dashboard, confirm - transaction saved with today's date

### Tests for User Story 6 (MANDATORY - TDD Required)

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T082 [P] [US6] Contract test for POST /api/ledgers/{id}/templates/{id}/apply in backend/tests/contract/test_template_crud.py
- [ ] T083 [P] [US6] Integration test for template apply flow in backend/tests/integration/test_template_apply.py
- [ ] T084 [P] [US6] Component test for QuickEntryPanel in frontend/tests/components/templates/QuickEntryPanel.test.tsx
- [ ] T085 **GATE**: Get test approval from stakeholder
- [ ] T086 **GATE**: Verify all tests FAIL

### Implementation for User Story 6

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [ ] T087 [US6] Implement POST /api/ledgers/{id}/templates/{id}/apply endpoint in backend/src/api/routes/templates.py
- [ ] T088 [US6] Handle deleted account reference error in apply endpoint
- [ ] T089 [US6] Create QuickEntryPanel component in frontend/src/components/templates/QuickEntryPanel.tsx
- [ ] T090 [US6] Add confirmation dialog before quick-save
- [ ] T091 [US6] Add "Edit" option in confirmation to open full form
- [ ] T092 [US6] Integrate QuickEntryPanel into Dashboard
- [ ] T093 [US6] Ensure all tests PASS
- [ ] T094 [US6] Refactor while keeping tests green

**Checkpoint**: User Story 6 complete - quick entry from Dashboard works

---

## Phase 9: User Story 7 - Manage Templates (Priority: P3)

**Goal**: Users can edit, delete, and reorder templates

**Independent Test**: Edit template amount and save - template updated; delete template - removed from list; drag-drop reorder - new order persisted

### Tests for User Story 7 (MANDATORY - TDD Required)

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T095 [P] [US7] Contract test for PATCH /api/ledgers/{id}/templates/{id} in backend/tests/contract/test_template_crud.py
- [ ] T096 [P] [US7] Contract test for DELETE /api/ledgers/{id}/templates/{id} in backend/tests/contract/test_template_crud.py
- [ ] T097 [P] [US7] Contract test for PATCH /api/ledgers/{id}/templates/reorder in backend/tests/contract/test_template_crud.py
- [ ] T098 [P] [US7] Component test for template edit/delete in frontend/tests/components/templates/TemplateList.test.tsx
- [ ] T099 **GATE**: Get test approval from stakeholder
- [ ] T100 **GATE**: Verify all tests FAIL

### Implementation for User Story 7

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [ ] T101 [US7] Implement PATCH /api/ledgers/{id}/templates/{id} endpoint in backend/src/api/routes/templates.py
- [ ] T102 [US7] Implement DELETE /api/ledgers/{id}/templates/{id} endpoint in backend/src/api/routes/templates.py
- [ ] T103 [US7] Implement PATCH /api/ledgers/{id}/templates/reorder endpoint in backend/src/api/routes/templates.py
- [ ] T104 [US7] Add delete confirmation requirement in frontend
- [ ] T105 [US7] Add template edit mode in TemplateCard
- [ ] T106 [US7] Implement drag-drop reordering with @dnd-kit in TemplateList
- [ ] T107 [US7] Ensure all tests PASS
- [ ] T108 [US7] Refactor while keeping tests green

**Checkpoint**: All user stories complete

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T109 [P] Verify edge case: zero-amount warning dialog works correctly across all entry points
- [ ] T110 [P] Add edge case handling: divide by zero error message
- [ ] T111 [P] Add edge case handling: max templates (50) error message
- [ ] T112 [P] Add edge case handling: max amount (999,999,999.99) validation
- [ ] T113 [P] Add edge case handling: deleted account in template error
- [ ] T114 Verify dark/light mode styling in all new components
- [ ] T115 Verify responsive design for mobile screens
- [ ] T116 Verify i18n for all user-facing text (zh-TW, en)
- [ ] T117 Run quickstart.md validation checklist
- [ ] T118 Performance check: transaction save < 1 second
- [ ] T119 Performance check: expression calculation < 100ms
- [ ] T120 Performance check: template list load < 500ms

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - US1, US2, US3 (P1) should be completed first as MVP
  - US4, US5, US6 (P2) can proceed after MVP
  - US7 (P3) can proceed after US5 and US6
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Expression parser shared with US1
- **User Story 3 (P1)**: Can start after Foundational (Phase 2) - DatePicker integrated in US1 form
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Extends US1 form
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - Requires template API
- **User Story 6 (P2)**: Depends on US5 (needs templates to exist)
- **User Story 7 (P3)**: Depends on US5 (needs templates to manage)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Backend before frontend (API before UI)
- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Once Foundational phase completes, US1/US2/US3 can theoretically start in parallel
- Different user stories can be worked on in parallel by different team members

---

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together:
Task: "Contract test for POST /api/ledgers/{id}/transactions in backend/tests/contract/test_transaction_create.py"
Task: "Integration test for transaction entry flow in backend/tests/integration/test_transaction_entry.py"
Task: "Unit test for expression parser in frontend/tests/lib/utils/expressionParser.test.ts"
Task: "Component test for TransactionModal in frontend/tests/components/transactions/TransactionModal.test.tsx"

# After tests pass approval, launch parallel implementation:
Task: "Create AccountSelect component in frontend/src/components/transactions/AccountSelect.tsx"
Task: "Create AmountInput component in frontend/src/components/transactions/AmountInput.tsx"
```

---

## Implementation Strategy

### MVP First (User Stories 1, 2, 3 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Add Transaction)
4. Complete Phase 4: User Story 2 (Amount Calculator)
5. Complete Phase 5: User Story 3 (Date Picker)
6. **STOP and VALIDATE**: Test MVP independently - users can add transactions with calculated amounts and dates
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational -> Foundation ready
2. Add User Stories 1+2+3 -> Test MVP -> Deploy/Demo (MVP!)
3. Add User Story 4 (Notes) -> Test -> Deploy/Demo
4. Add User Stories 5+6 (Templates) -> Test -> Deploy/Demo
5. Add User Story 7 (Template Management) -> Test -> Deploy/Demo
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Transaction Entry)
   - Developer B: User Story 2 (Calculator) + User Story 3 (Date Picker)
3. After MVP:
   - Developer A: User Story 5 (Save Template) + User Story 6 (Quick Apply)
   - Developer B: User Story 4 (Notes) + User Story 7 (Manage Templates)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
