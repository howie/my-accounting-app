# Implementation Tasks: Advanced Transactions

**Feature**: 010-advanced-transactions
**Spec**: [spec.md](./spec.md)
**Plan**: [plan.md](./plan.md)
**Status**: Pending

## Phase 1: Setup

**Goal**: Initialize project structure and prepare for feature implementation.

- [x] T001 Create feature directory structure in backend/src/api, backend/src/models, backend/src/services
- [x] T002 Create feature directory structure in frontend/src/components, frontend/src/pages
- [x] T003 [P] Create database migration script for new tables (tags, recurring_transactions, installment_plans) in backend/alembic/versions
- [x] T004 Define SQLAlchemy models for Tag, RecurringTransaction, InstallmentPlan in backend/src/models/advanced.py
- [x] T005 Update Transaction model to include relationships (tags, recurring_id, installment_id) in backend/src/models/transaction.py
- [x] T006 [P] Create Pydantic schemas for all new entities in backend/src/schemas/advanced.py

## Phase 2: Foundational

**Goal**: Establish core database connectivity and shared utilities.

- [x] T007 [P] Create backend unit tests for Tag, Recurring, and Installment services in backend/tests/unit/
- [x] T008 Approve unit tests with stakeholder (simulated) and verify they FAIL (Red Phase)
- [x] T009 Implement CRUD service for Tags in backend/src/services/tag_service.py
- [x] T010 Implement CRUD service for Recurring Transactions in backend/src/services/recurring_service.py
- [x] T011 Implement creation service for Installment Plans in backend/src/services/installment_service.py
- [x] T012 Verify all Foundational unit tests PASS (Green Phase)

## Phase 3: Transaction Tagging (Priority: P1)

**Goal**: Allow users to categorize transactions with flexible tags.
**Independent Test**: Add tags to a transaction and filter the list by those tags.

- [x] T013 [P] [US1] Write integration tests for Tag API endpoints in backend/tests/integration/test_tags_api.py
- [x] T014 [US1] Approve Tag API tests and verify they FAIL (Red Phase)
- [x] T015 [US1] Create API endpoints for Tag management (List, Create, Update, Delete) in backend/src/api/tags.py
- [x] T016 [US1] Update Transaction API to accept and return tags in backend/src/api/transactions.py
- [x] T017 [US1] Implement OR-based tag filtering logic in backend Transaction list endpoint in backend/src/services/transaction_service.py
- [x] T018 [US1] Verify Tag API integration tests PASS (Green Phase)
- [x] T019 [P] [US1] Create frontend API client functions for Tags in frontend/src/services/api.ts
- [x] T020 [US1] Create Tag management UI (List/Edit/Delete) in frontend/src/components/tags/TagManager.tsx
- [x] T021 [US1] Update Transaction Entry form to support tag selection/creation in frontend/src/components/transactions/TransactionForm.tsx
- [x] T022 [US1] Add tag filter controls to Transaction List UI in frontend/src/pages/transactions/index.tsx

## Phase 4: Recurring Transactions (Priority: P2)

**Goal**: Automate regular expenses with manual approval.
**Independent Test**: Create a recurring record and verify it prompts for approval on the due date.

- [x] T023 [P] [US2] Write integration tests for Recurring API workflow and Approval logic in backend/tests/integration/test_recurring_flow.py
- [x] T024 [US2] Approve Recurring API tests and verify they FAIL (Red Phase)
- [x] T025 [US2] Create API endpoints for Recurring Transaction templates in backend/src/api/recurring.py
- [x] T026 [US2] Implement "Check Due" logic and approval validation (DI-003) in backend/src/services/recurring_service.py
- [x] T027 [US2] Create API endpoint to list "Due" items and "Approve" (create transaction) in backend/src/api/recurring.py
- [x] T028 [US2] Verify Recurring API integration tests PASS (Green Phase)
- [x] T029 [P] [US2] Create frontend API client functions for Recurring Transactions in frontend/src/services/api.ts
- [x] T030 [US2] Create Recurring Transaction Template management UI in frontend/src/pages/settings/recurring.tsx
- [x] T031 [US2] Implement Dashboard notification component for Overdue items in frontend/src/components/dashboard/RecurringAlerts.tsx
- [x] T032 [US2] Create Approval Modal for verifying and submitting due transactions in frontend/src/components/recurring/ApprovalModal.tsx

## Phase 5: Installment Records (Priority: P3)

**Goal**: Record split payments accurately in the ledger.
**Independent Test**: Create an installment plan and verify 12 future-dated transactions appear.

- [x] T033 [P] [US3] Write integration tests for Installment generation and sum validation (DI-001) in backend/tests/integration/test_installments.py
- [x] T034 [US3] Approve Installment tests and verify they FAIL (Red Phase)
- [x] T035 [US3] Create API endpoint to create Installment Plans in backend/src/api/installments.py
- [x] T036 [US3] Implement logic to generate N future transactions with strict sum validation (DI-001) in backend/src/services/installment_service.py
- [x] T037 [US3] Implement audit linking logic (DI-002) connecting transactions to parent plan in backend/src/services/installment_service.py
- [x] T038 [US3] Verify Installment integration tests PASS (Green Phase)
- [x] T039 [P] [US3] Create frontend API client functions for Installment Plans in frontend/src/services/api.ts
- [x] T040 [US3] Create Installment Plan Entry form in frontend/src/components/installments/InstallmentForm.tsx
- [x] T041 [US3] Add "Installment Plan" view to Transaction List or separate page in frontend/src/pages/installments/index.tsx

## Phase 6: Polish & Cross-Cutting

**Goal**: Ensure consistency, data integrity, and clean UX.

- [x] T042 Ensure all new API endpoints have proper error handling and validation in backend/src/api
- [x] T043 Verify double-entry constraints are enforced for all generated transactions in backend/src/services/transaction_service.py
- [ ] T044 Update Dashboard to reflect future liabilities from installments (if applicable) in frontend/src/components/dashboard/SummaryCards.tsx
- [x] T045 Run full backend test suite and fix regressions
- [x] T046 Run frontend test suite and fix regressions
- [x] T047 Update user documentation and `quickstart.md` with new feature guides

## Implementation Strategy

- **MVP**: Complete Phase 1, 2, and 3 (Tagging) to deliver immediate value.
- **TDD Workflow**: Strictly follow Test -> Red -> Code -> Green cycle for all backend logic.
- **Incremental**: Deploy Tagging first, then Recurring, then Installments.

## Dependencies

1. **Tags (US1)**: Blocks nothing, but useful for other features.
2. **Recurring (US2)**: Depends on Transaction model updates.
3. **Installments (US3)**: Depends on Transaction model updates.
