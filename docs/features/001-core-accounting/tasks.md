---
description: "Tasks for Core Accounting System implementation"
---

# Tasks: Core Accounting System

**Input**: Design documents from `/docs/features/001-core-accounting/`
**Prerequisites**: plan.md, spec.md, research.md
**Tests**: Per MyAB Constitution Principle II (Test-First Development), tests are MANDATORY and MUST be written BEFORE implementation.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel
- **[Story]**: User Story mapping (US1, US2, US3, US4)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create project directory structure (src/myab, tests, docs) per plan.md
- [ ] T002 Create requirements-dev.txt with pytest and pytest-cov
- [ ] T003 [P] Create setup.py or pyproject.toml for package configuration
- [ ] T004 [P] Configure .gitignore for Python, SQLite, and IDE files
- [ ] T005 Create tests/conftest.py with initial database fixtures
- [ ] T006 Create docs/features/001-core-accounting/data-model.md with detailed schema
- [ ] T007 [P] Create docs/features/001-core-accounting/quickstart.md guide

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T008 Implement src/myab/persistence/database.py (SQLite connection manager)
- [ ] T009 Create src/myab/models/base.py (if needed for shared logic) or init models package
- [ ] T010 [P] Implement src/myab/validation/validators.py (DI-001 numeric validation)
- [ ] T011 Setup logging configuration in src/myab/__init__.py
- [ ] T012 Create initial DB migration/schema script in src/myab/persistence/schema.sql
- [ ] T013 Verify database connection and schema creation with a simple test in tests/unit/persistence/test_database.py

**Checkpoint**: Foundation ready - database connects, schema loads.

---

## Phase 3: User Story 1 - Create Ledger and Initial Setup (Priority: P1) 🎯 MVP

**Goal**: Users can create ledgers and manage chart of accounts (Asset, Liability, Income, Expense).

**Independent Test**: Create ledger → Add Accounts → Verify existence.

### Tests for US1 (MANDATORY - TDD Required) ⚠️

- [ ] T014 [P] [US1] Contract test for UserAccountService in tests/contract/test_user_account_service_contract.py
- [ ] T015 [P] [US1] Contract test for LedgerService in tests/contract/test_ledger_service_contract.py
- [ ] T016 [P] [US1] Contract test for AccountService in tests/contract/test_account_service_contract.py
- [ ] T017 [P] [US1] Integration test: Ledger creation and account setup in tests/integration/test_ledger_lifecycle.py
- [ ] T018 [US1] **GATE**: Verify all tests FAIL

### Implementation for US1

- [ ] T019 [P] [US1] Create UserAccount model in src/myab/models/user_account.py
- [ ] T020 [P] [US1] Create Ledger model in src/myab/models/ledger.py
- [ ] T021 [P] [US1] Create Account model in src/myab/models/account.py (with type enum)
- [ ] T022 [P] [US1] Implement UserAccountRepository in src/myab/persistence/repositories/user_account_repository.py
- [ ] T023 [P] [US1] Implement LedgerRepository in src/myab/persistence/repositories/ledger_repository.py
- [ ] T024 [P] [US1] Implement AccountRepository in src/myab/persistence/repositories/account_repository.py
- [ ] T025 [P] [US1] Implement UserAccountService in src/myab/services/user_account_service.py
- [ ] T026 [P] [US1] Implement LedgerService in src/myab/services/ledger_service.py (create default Cash/Equity)
- [ ] T027 [P] [US1] Implement AccountService in src/myab/services/account_service.py (auto-prefix logic)
- [ ] T028 [P] [US1] Create UI Main Window skeleton in src/myab/ui/main_window.py
- [ ] T029 [US1] Implement Ledger Management UI in src/myab/ui/ledger_management.py
- [ ] T030 [US1] Implement Account Management UI in src/myab/ui/account_management.py
- [ ] T031 [US1] Ensure all tests PASS and refactor

**Checkpoint**: User can start app, create ledger, add accounts.

---

## Phase 4: User Story 2 - Record Basic Transactions (Priority: P1) 🎯 MVP

**Goal**: Users can record Expense, Income, and Transfer transactions with double-entry enforcement.

**Independent Test**: Record transactions → Verify balances update correctly.

### Tests for US2 (MANDATORY - TDD Required) ⚠️

- [ ] T032 [P] [US2] Contract test for TransactionService in tests/contract/test_transaction_service_contract.py
- [ ] T033 [P] [US2] Integration test: Transaction flow and balance updates in tests/integration/test_transaction_flow.py
- [ ] T034 [P] [US2] Edge case tests (zero amount, same account transfer) in tests/unit/services/test_transaction_edge_cases.py
- [ ] T035 [US2] **GATE**: Verify all tests FAIL

### Implementation for US2

- [ ] T036 [P] [US2] Create Transaction model in src/myab/models/transaction.py
- [ ] T037 [P] [US2] Implement TransactionRepository in src/myab/persistence/repositories/transaction_repository.py
- [ ] T038 [US2] Implement TransactionService in src/myab/services/transaction_service.py (validation, balance calc)
- [ ] T039 [US2] Update AccountService to support balance calculation requests
- [ ] T040 [US2] Implement Transaction Entry UI form in src/myab/ui/transaction_entry.py
- [ ] T041 [US2] Add balance warning logic (red text) in UI for negative Asset/Liability
- [ ] T042 [US2] Ensure all tests PASS and refactor

**Checkpoint**: Full MVP functionality (Setup + Record).

---

## Phase 5: User Story 3 - View Balances and History (Priority: P2)

**Goal**: Search/Filter transactions and view current balances.

**Independent Test**: Search for known transaction → Verify result.

### Tests for US3 (MANDATORY - TDD Required) ⚠️

- [ ] T043 [P] [US3] Unit tests for search filters in tests/unit/persistence/test_transaction_search.py
- [ ] T044 [US3] **GATE**: Verify all tests FAIL

### Implementation for US3

- [ ] T045 [P] [US3] Add search/filter methods to TransactionRepository
- [ ] T046 [P] [US3] Add search methods to TransactionService
- [ ] T047 [US3] Implement Transaction List/History UI in src/myab/ui/transaction_list.py (with filters)
- [ ] T048 [US3] Update Main Window to display summary balances
- [ ] T049 [US3] Ensure all tests PASS

---

## Phase 6: User Story 4 - Multiple Ledgers and User Accounts (Priority: P3)

**Goal**: Support isolation between multiple ledgers and users.

**Independent Test**: Create Ledger A and B → Add txn to A → Verify B is unchanged.

### Tests for US4 (MANDATORY - TDD Required) ⚠️

- [ ] T050 [P] [US4] Integration test for Multi-ledger isolation in tests/integration/test_isolation.py
- [ ] T051 [US4] **GATE**: Verify all tests FAIL

### Implementation for US4

- [ ] T052 [P] [US4] Implement "Switch Ledger" functionality in LedgerService and UI
- [ ] T053 [P] [US4] Implement User Login/Switching screen in src/myab/ui/login.py
- [ ] T054 [US4] Verify data isolation enforcement in all repositories
- [ ] T055 [US4] Ensure all tests PASS

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, code cleanup, final validation.

- [ ] T056 [P] Generate API documentation from docstrings
- [ ] T057 Run full test suite and check coverage (aim for >90%)
- [ ] T058 [P] Add docstrings to all public methods
- [ ] T059 Verify 30,000 transaction performance (benchmark test)
- [ ] T060 Update README.md with usage instructions

---

## Dependencies & Execution Order

1. **Phase 1 & 2** must be done first.
2. **Phase 3 (US1)** unlocks the app usability.
3. **Phase 4 (US2)** depends on US1.
4. **Phase 5 & 6** can be done in parallel after US2.

## Implementation Strategy

- **MVP**: Complete Phase 1, 2, 3, 4.
- **Full Feature**: Complete all phases.
- **Parallelism**: Models, Repositories, and Services can often be built in parallel if contracts are agreed upon first. UI can be built in parallel with backend if mocked.
