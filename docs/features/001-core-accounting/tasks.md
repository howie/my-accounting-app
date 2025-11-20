---

description: "Task list for Core Accounting System implementation"
---

# Tasks: Core Accounting System

**Input**: Design documents from `/docs/features/001-core-accounting/`
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓

**Tests**: Per MyAB Constitution Principle II (Test-First Development), tests are MANDATORY and MUST be written BEFORE implementation. Tests must be reviewed/approved before coding begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Paths shown below follow single desktop application structure from plan.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project structure per plan.md (src/myab/, tests/, docs/)
- [ ] T002 Initialize Python project with requirements.txt and requirements-dev.txt
- [ ] T003 [P] Configure pytest in pytest.ini with test discovery settings
- [ ] T004 [P] Create .gitignore for Python (.venv/, __pycache__/, *.pyc, *.db)
- [ ] T005 [P] Create src/myab/__init__.py package initialization file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create database schema SQL in src/myab/persistence/schema.sql with all tables
- [ ] T007 Implement database connection manager in src/myab/persistence/database.py
- [ ] T008 [P] Create base repository class in src/myab/persistence/repositories/__init__.py
- [ ] T009 [P] Implement Decimal validation in src/myab/validation/validators.py
- [ ] T010 [P] Create test fixtures in tests/fixtures/sample_data.py for all entities
- [ ] T011 Create conftest.py with test_db fixture (in-memory SQLite)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Create Ledger and Initial Setup (Priority: P1) 🎯 MVP

**Goal**: Enable users to create ledgers and set up chart of accounts with predefined Cash/Equity accounts

**Independent Test**: Create ledger with initial balance → Add custom account → Verify in chart of accounts

### Tests for User Story 1 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**
> Per Constitution Principle II: Tests → Approval → Red → Green → Refactor

- [ ] T012 [P] [US1] Contract test for LedgerService.create_ledger() in tests/contract/test_ledger_service_contract.py
- [ ] T013 [P] [US1] Contract test for AccountService.create_account() in tests/contract/test_account_service_contract.py
- [ ] T014 [P] [US1] Integration test for ledger creation flow in tests/integration/test_ledger_lifecycle.py
- [ ] T015 [P] [US1] Edge case test for predefined account deletion prevention in tests/integration/test_ledger_lifecycle.py
- [ ] T016 **GATE**: Get test approval from stakeholder before proceeding to implementation
- [ ] T017 **GATE**: Run tests and verify all FAIL (proving they test the missing feature)

### Implementation for User Story 1

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [ ] T018 [P] [US1] Create UserAccount model in src/myab/models/user_account.py with password validation
- [ ] T019 [P] [US1] Create Ledger model in src/myab/models/ledger.py with name and initial balance
- [ ] T020 [P] [US1] Create Account model in src/myab/models/account.py with type validation (Asset/Liability/Income/Expense)
- [ ] T021 [US1] Create UserAccountRepository in src/myab/persistence/repositories/user_account_repository.py
- [ ] T022 [US1] Create LedgerRepository in src/myab/persistence/repositories/ledger_repository.py
- [ ] T023 [US1] Create AccountRepository in src/myab/persistence/repositories/account_repository.py
- [ ] T024 [US1] Implement UserAccountService.create_user() in src/myab/services/user_account_service.py
- [ ] T025 [US1] Implement LedgerService.create_ledger() with initial Cash account in src/myab/services/ledger_service.py
- [ ] T026 [US1] Implement AccountService.create_account() with type validation in src/myab/services/account_service.py
- [ ] T027 [US1] Add predefined account deletion prevention in AccountService.delete_account()
- [ ] T028 [US1] Ensure all tests PASS (green phase of TDD)
- [ ] T029 [US1] Refactor models/services while keeping tests green

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Record Basic Transactions (Priority: P1) 🎯 MVP

**Goal**: Enable users to record expenses, income, and transfers with automatic balance calculation

**Independent Test**: Record expense → Verify both account balances updated correctly per double-entry rules

### Tests for User Story 2 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T030 [P] [US2] Contract test for TransactionService.create_transaction() in tests/contract/test_transaction_service_contract.py
- [ ] T031 [P] [US2] Contract test for TransactionService.calculate_balance() in tests/contract/test_transaction_service_contract.py
- [ ] T032 [P] [US2] Integration test for expense transaction flow in tests/integration/test_transaction_flow.py
- [ ] T033 [P] [US2] Integration test for income transaction flow in tests/integration/test_transaction_flow.py
- [ ] T034 [P] [US2] Integration test for transfer transaction flow in tests/integration/test_transaction_flow.py
- [ ] T035 [P] [US2] Double-entry balance verification test in tests/integration/test_balance_calculations.py
- [ ] T036 [P] [US2] Edge case tests (zero amount, large amount, same-account transfer) in tests/integration/test_transaction_flow.py
- [ ] T037 **GATE**: Get test approval from stakeholder
- [ ] T038 **GATE**: Verify all tests FAIL

### Implementation for User Story 2

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [ ] T039 [P] [US2] Create Transaction model in src/myab/models/transaction.py with debit/credit sides
- [ ] T040 [US2] Create TransactionRepository in src/myab/persistence/repositories/transaction_repository.py
- [ ] T041 [US2] Implement TransactionService.create_transaction() with double-entry validation in src/myab/services/transaction_service.py
- [ ] T042 [US2] Implement TransactionService.calculate_balance() using SUM query in src/myab/services/transaction_service.py
- [ ] T043 [US2] Implement TransactionService.edit_transaction() with balance recalculation in src/myab/services/transaction_service.py
- [ ] T044 [US2] Implement TransactionService.delete_transaction() with confirmation in src/myab/services/transaction_service.py
- [ ] T045 [US2] Add transaction type validation (expense/income/transfer rules) in TransactionService
- [ ] T046 [US2] Ensure all tests PASS
- [ ] T047 [US2] Refactor while keeping tests green

**Checkpoint**: At this point, User Stories 1 AND 2 (MVP) should both work independently

---

## Phase 5: User Story 3 - View Account Balances and Transaction History (Priority: P2)

**Goal**: Enable users to view balances and search/filter transactions

**Independent Test**: Create multiple transactions → Search by keyword → Verify only matching transactions returned

### Tests for User Story 3 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T048 [P] [US3] Contract test for TransactionService.search_transactions() in tests/contract/test_transaction_service_contract.py
- [ ] T049 [P] [US3] Integration test for search by description in tests/integration/test_transaction_flow.py
- [ ] T050 [P] [US3] Integration test for filter by date range in tests/integration/test_transaction_flow.py
- [ ] T051 [P] [US3] Integration test for filter by account in tests/integration/test_transaction_flow.py
- [ ] T052 **GATE**: Get test approval from stakeholder
- [ ] T053 **GATE**: Verify all tests FAIL

### Implementation for User Story 3

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [ ] T054 [P] [US3] Implement TransactionService.search_by_description() in src/myab/services/transaction_service.py
- [ ] T055 [P] [US3] Implement TransactionService.filter_by_date_range() in src/myab/services/transaction_service.py
- [ ] T056 [P] [US3] Implement TransactionService.filter_by_account() in src/myab/services/transaction_service.py
- [ ] T057 [US3] Implement AccountService.list_accounts_with_balances() in src/myab/services/account_service.py
- [ ] T058 [US3] Ensure all tests PASS
- [ ] T059 [US3] Refactor while keeping tests green

**Checkpoint**: All three user stories (MVP + search) should now be independently functional

---

## Phase 6: User Story 4 - Multiple Ledgers and User Accounts (Priority: P3)

**Goal**: Enable users to create multiple ledgers and switch between them with complete data isolation

**Independent Test**: Create two ledgers → Add same account name to both → Verify no cross-contamination

### Tests for User Story 4 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T060 [P] [US4] Contract test for UserAccountService.create_user() in tests/contract/test_user_account_service_contract.py
- [ ] T061 [P] [US4] Contract test for LedgerService.list_ledgers() in tests/contract/test_ledger_service_contract.py
- [ ] T062 [P] [US4] Integration test for data isolation between ledgers in tests/integration/test_ledger_lifecycle.py
- [ ] T063 [P] [US4] Integration test for ledger deletion with confirmation in tests/integration/test_ledger_lifecycle.py
- [ ] T064 **GATE**: Get test approval from stakeholder
- [ ] T065 **GATE**: Verify all tests FAIL

### Implementation for User Story 4

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [ ] T066 [P] [US4] Implement UserAccountService.authenticate() in src/myab/services/user_account_service.py
- [ ] T067 [P] [US4] Implement LedgerService.list_ledgers() in src/myab/services/ledger_service.py
- [ ] T068 [US4] Implement LedgerService.switch_ledger() with context management in src/myab/services/ledger_service.py
- [ ] T069 [US4] Implement LedgerService.delete_ledger() with confirmation in src/myab/services/ledger_service.py
- [ ] T070 [US4] Add ledger-level data isolation validation in all repositories
- [ ] T071 [US4] Ensure all tests PASS
- [ ] T072 [US4] Refactor while keeping tests green

**Checkpoint**: All user stories should now be independently functional

---

## Phase 7: User Interface (Cross-Story)

**Purpose**: GUI implementation for all user stories using tkinter

**Note**: UI can be built incrementally per story or all at once after services are complete

- [ ] T073 [P] Create main window skeleton in src/myab/ui/main_window.py
- [ ] T074 [P] Create ledger management UI in src/myab/ui/ledger_management.py (for US1, US4)
- [ ] T075 [P] Create account management UI in src/myab/ui/account_management.py (for US1)
- [ ] T076 [P] Create transaction entry form in src/myab/ui/transaction_entry.py (for US2)
- [ ] T077 [P] Create transaction list view with search in src/myab/ui/transaction_list.py (for US3)
- [ ] T078 Connect UI to services with proper error handling
- [ ] T079 Add user account login/selection screen (for US4)
- [ ] T080 Manual UI testing on Windows and macOS

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T081 [P] Add unit tests for validators in tests/unit/validation/test_validators.py
- [ ] T082 [P] Add unit tests for models in tests/unit/models/
- [ ] T083 [P] Add edge case test for 30,000 transaction limit in tests/integration/test_balance_calculations.py
- [ ] T084 [P] Add edge case test for future dates in tests/integration/test_transaction_flow.py
- [ ] T085 [P] Add edge case test for negative amounts (refunds) in tests/integration/test_transaction_flow.py
- [ ] T086 Performance optimization: Add indexes on foreign keys in schema.sql
- [ ] T087 Create quickstart.md developer guide in docs/features/001-core-accounting/
- [ ] T088 Create README.md with installation and usage instructions
- [ ] T089 Run full test suite and verify 100% pass rate
- [ ] T090 Measure test coverage with pytest-cov (target: >90%)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P1 → P2 → P3)
- **UI (Phase 7)**: Depends on corresponding service layers being complete
- **Polish (Phase 8)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Depends on User Story 1 (needs ledgers and accounts to exist)
- **User Story 3 (P2)**: Depends on User Story 2 (needs transactions to search)
- **User Story 4 (P3)**: Can start after Foundational (Phase 2) - Independent of US2/US3

### Within Each User Story

- Tests (MANDATORY) MUST be written and FAIL before implementation
- Models before repositories
- Repositories before services
- Services before UI
- Integration tests verify end-to-end story flow
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Within each user story:
  - All test tasks marked [P] can run in parallel
  - All model tasks marked [P] can run in parallel
  - After Foundational phase completes:
    - User Story 1 can start immediately
    - User Story 4 can start immediately (parallel to US1)
    - User Story 2 waits for US1 ledger/account services
    - User Story 3 waits for US2 transaction service

---

## Parallel Example: User Story 2

```bash
# After US1 is complete and US2 tests are approved and failing:

# Launch all model/repository tasks for User Story 2 together:
Task: "Create Transaction model in src/myab/models/transaction.py"
Task: "Create TransactionRepository in src/myab/persistence/repositories/transaction_repository.py"

# Then service layer (sequential - depends on above):
Task: "Implement TransactionService.create_transaction()"
Task: "Implement TransactionService.calculate_balance()"
# etc.
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Ledger & Account Management)
4. Complete Phase 4: User Story 2 (Transaction Recording)
5. **STOP and VALIDATE**: Test User Stories 1+2 together as MVP
6. Build minimal UI for MVP (Phase 7, subset)
7. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Demo (ledger management!)
3. Add User Story 2 → Test independently → Demo (MVP - can track finances!)
4. Add User Story 3 → Test independently → Demo (can search/analyze!)
5. Add User Story 4 → Test independently → Demo (full multi-ledger support!)
6. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers after Foundational phase completes:

1. Developer A: User Story 1 (T012-T029)
2. Developer B: User Story 4 (T060-T072) - independent!
3. Once US1 complete:
   - Developer A: User Story 2 (T030-T047)
   - Developer B: Continues US4 or starts US3 prep
4. Stories integrate cleanly due to independent testing

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- **TDD CRITICAL**: Verify tests fail before implementing (gates T017, T038, T053, T065)
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence

---

## Task Summary

**Total Tasks**: 90
**Setup**: 5 tasks (T001-T005)
**Foundational**: 6 tasks (T006-T011)
**User Story 1** (P1): 18 tasks (T012-T029) - 6 tests + 12 implementation
**User Story 2** (P1): 18 tasks (T030-T047) - 9 tests + 9 implementation
**User Story 3** (P2): 12 tasks (T048-T059) - 6 tests + 6 implementation
**User Story 4** (P3): 13 tasks (T060-T072) - 6 tests + 7 implementation
**UI**: 8 tasks (T073-T080)
**Polish**: 10 tasks (T081-T090)

**Parallel Opportunities**: 42 tasks marked [P] can run in parallel within their phases

**MVP Scope**: Phase 1 + Phase 2 + Phase 3 + Phase 4 = 47 tasks for working accounting system

**Independent Test Criteria**:
- US1: Create ledger → Add account → Verify in chart
- US2: Record transaction → Verify both balances updated
- US3: Create transactions → Search → Verify results
- US4: Create 2 ledgers → Verify no cross-contamination
