# Tasks: 資料匯入功能

**Input**: Design documents from `/docs/features/006-data-import/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

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

**Purpose**: Project initialization and basic structure

- [x] T001 Create database migration for import_sessions table in backend/alembic/versions/
- [x] T002 [P] Create ImportSession model in backend/src/models/import_session.py
- [x] T003 [P] Create test fixtures directory with sample CSV files in backend/tests/fixtures/csv/
- [x] T004 [P] Add i18n translations for import feature in frontend/messages/zh-TW.json and frontend/messages/en.json
- [x] T005 Update Ledger model to add import_sessions relationship in backend/src/models/ledger.py
- [x] T006 Run migration and verify import_sessions table created

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T007 [P] Create data_import schemas (request/response types) in backend/src/schemas/data_import.py
- [x] T008 [P] Create base CSV parser utility in backend/src/services/csv_parser.py with encoding detection (UTF-8/Big5)
- [x] T009 [P] Create import API router scaffold in backend/src/api/import_routes.py
- [x] T010 Register import router in main FastAPI app in backend/src/main.py
- [x] T011 [P] Create import API client in frontend/src/lib/api/import.ts

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 + 2 - MyAB CSV 匯入 & 批次匯入入口 (Priority: P1) 🎯 MVP

**Goal**: 使用者可從 Sidebar 進入匯入頁面，上傳 MyAB CSV 檔案並匯入交易到系統

**Independent Test**: 準備 MyAB 匯出的 CSV 檔案，從入口進入匯入頁面，執行匯入流程，驗證交易資料正確寫入系統

### Tests for User Story 1+2 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**
> Per Constitution Principle II: Tests → Approval → Red → Green → Refactor

- [x] T012 [P] [US1] Unit test for MyAB CSV parser in backend/tests/unit/test_csv_parser.py
- [x] T013 [P] [US1] Unit test for date format parsing (yyyy/MM/dd, yyyy-MM-dd, MM/dd/yyyy) in backend/tests/unit/test_csv_parser.py
- [x] T014 [P] [US1] Unit test for amount format parsing (with/without thousand separators) in backend/tests/unit/test_csv_parser.py
- [x] T015 [P] [US1] Unit test for duplicate detection algorithm in backend/tests/unit/test_import_service.py
- [x] T016 [P] [US1] Integration test for import preview endpoint in backend/tests/integration/test_import_api.py
- [x] T017 [P] [US1] Integration test for import execute endpoint in backend/tests/integration/test_import_api.py
- [x] T018 [P] [US1] Integration test for atomic rollback on failure in backend/tests/integration/test_import_api.py
- [x] T019 **GATE**: Get test approval from stakeholder before proceeding to implementation
- [x] T020 **GATE**: Verify all tests FAIL (proving they test the missing feature)

### Implementation for User Story 1+2

> **PREREQUISITE**: All tests above must be written, approved, and failing

#### Backend Implementation

- [x] T021 [P] [US1] Implement MyAB CSV parser with 9-column format in backend/src/services/csv_parser.py
- [x] T022 [P] [US1] Implement account prefix parsing (A-, L-, I-, E-) in backend/src/services/csv_parser.py
- [x] T023 [US1] Implement duplicate detection service in backend/src/services/import_service.py
- [x] T024 [US1] Implement account mapping logic (existing vs new) in backend/src/services/import_service.py
- [x] T025 [US1] Implement import preview endpoint (POST /api/ledgers/{id}/import/preview) in backend/src/api/import_routes.py
- [x] T026 [US1] Implement import execute endpoint with atomic transaction in backend/src/api/import_routes.py
- [x] T027 [US1] Add audit trail logging for imported transactions in backend/src/services/import_service.py
- [x] T028 [US1] Implement file size validation (max 10MB) in backend/src/api/import_routes.py
- [x] T029 [US1] Implement transaction limit validation (max 2000) in backend/src/services/import_service.py

#### Frontend Implementation

- [x] T030 [P] [US2] Add "批次匯入" menu entry in Sidebar in frontend/src/components/layout/Sidebar.tsx
- [x] T031 [P] [US2] Create import page route in frontend/src/app/ledgers/[id]/import/page.tsx
- [x] T032 [P] [US1] Create ImportTypeSelector component (integrated in FileUploader) in frontend/src/components/import/FileUploader.tsx
- [x] T033 [P] [US1] Create CsvUploader component (as FileUploader) in frontend/src/components/import/FileUploader.tsx
- [x] T034 [US1] Create ImportPreview component showing transactions in frontend/src/components/import/ImportPreview.tsx
- [x] T035 [US1] Create AccountMapper component (integrated in ImportPreview) in frontend/src/components/import/ImportPreview.tsx
- [x] T036 [US1] Create ImportConfirmation component (integrated in page.tsx) in frontend/src/app/ledgers/[id]/import/page.tsx
- [x] T037 [US1] Integrate all import components in import page with state management
- [x] T038 [US1] Add progress indicator for large imports in frontend/src/components/import/ImportProgress.tsx

#### Verification

- [x] T039 [US1] Ensure all backend tests PASS (green phase of TDD)
- [x] T040 [US1] Manual verification: upload MyAB CSV and complete import flow
- [x] T041 [US1] Verify audit log entries created for imported transactions
- [x] T042 [US1] Refactor while keeping tests green

**Checkpoint**: MyAB CSV import fully functional. Users can import from MyAB to the system.

---

## Phase 4: User Story 3 - 信用卡帳單 CSV 匯入 (Priority: P2)

**Goal**: 使用者可上傳銀行信用卡帳單 CSV，系統自動建議支出分類後匯入

**Independent Test**: 準備銀行信用卡帳單 CSV，選擇銀行類型，驗證系統正確解析並建議分類

### Tests for User Story 3 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T043 [P] [US3] Unit test for credit card CSV parser (multiple banks) in backend/tests/unit/test_csv_parser.py
- [x] T044 [P] [US3] Unit test for category suggestion service in backend/tests/unit/test_category_suggester.py
- [x] T045 [P] [US3] Unit test for bank config loading in backend/tests/unit/test_csv_parser.py
- [x] T046 [P] [US3] Integration test for credit card import preview in backend/tests/integration/test_import_api.py
- [x] T047 [P] [US3] Integration test for credit card import execute in backend/tests/integration/test_import_api.py
- [x] T048 **GATE**: Get test approval from stakeholder
- [x] T049 **GATE**: Verify all tests FAIL

### Implementation for User Story 3

> **PREREQUISITE**: All tests above must be written, approved, and failing

#### Backend Implementation

- [x] T050 [P] [US3] Create bank CSV config definitions in backend/src/services/bank_configs.py
- [x] T051 [P] [US3] Create category suggestion rules in backend/src/services/category_suggester.py
- [x] T052 [US3] Implement credit card CSV parser with bank-specific configs in backend/src/services/csv_parser.py
- [x] T053 [US3] Implement category suggestion service with keyword matching in backend/src/services/category_suggester.py
- [x] T054 [US3] Add credit card import type to preview endpoint in backend/src/api/import_routes.py
- [x] T055 [US3] Implement GET /api/import/banks endpoint to list supported banks in backend/src/api/import_routes.py

#### Frontend Implementation

- [x] T056 [P] [US3] Create BankSelector component in frontend/src/components/import/BankSelector.tsx
- [x] T057 [US3] Update ImportTypeSelector to handle credit card flow (integrated in FileUploader) in frontend/src/components/import/FileUploader.tsx
- [x] T058 [US3] Create CategoryEditor component for adjusting suggestions in frontend/src/components/import/CategoryEditor.tsx
- [x] T059 [US3] Update ImportPreview to show category suggestions in frontend/src/components/import/ImportPreview.tsx
- [x] T060 [US3] Integrate credit card flow in import page

#### Verification

- [x] T061 [US3] Ensure all backend tests PASS
- [x] T062 [US3] Manual verification: upload credit card CSV from each supported bank
- [x] T063 [US3] Verify category suggestions accuracy meets 70% target
- [x] T064 [US3] Refactor while keeping tests green

**Checkpoint**: Credit card import fully functional. All import types now available.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T065 [P] Add loading states and error boundaries to all import components
- [x] T066 [P] Add progress polling for large imports (>1000 transactions)
- [x] T067 [P] Create import history page in frontend/src/app/ledgers/[id]/import/history/page.tsx
- [x] T068 [P] Implement GET /api/ledgers/{id}/import/history endpoint in backend/src/api/import_routes.py
- [x] T069 Performance testing: verify 2000 transactions import < 30 seconds
- [x] T070 Verify data integrity compliance (double-entry, audit trails) across all import types
- [ ] T071 [P] Add frontend unit tests for import components in frontend/tests/components/import/
- [x] T072 Run quickstart.md validation checklist
- [x] T073 Update API documentation with import endpoints (contracts/import-api.yaml)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories 1+2 (Phase 3)**: Depends on Foundational phase completion
- **User Story 3 (Phase 4)**: Depends on Foundational; can run in parallel with Phase 3 if team allows
- **Polish (Phase 5)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1+2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Builds on Phase 3 parser infrastructure but independently testable

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before endpoints
- Backend before frontend integration
- Core implementation before UI polish
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- All tests for a user story marked [P] can run in parallel
- Backend and frontend implementation can proceed in parallel within a story
- Phase 3 and Phase 4 can run in parallel with separate developers

---

## Parallel Example: User Story 1+2

```bash
# Launch all tests for User Story 1+2 together:
Task: "Unit test for MyAB CSV parser in backend/tests/unit/test_csv_parser.py"
Task: "Unit test for date format parsing in backend/tests/unit/test_csv_parser.py"
Task: "Unit test for amount format parsing in backend/tests/unit/test_csv_parser.py"
Task: "Unit test for duplicate detection in backend/tests/unit/test_import_service.py"
Task: "Integration test for import preview in backend/tests/integration/test_import_api.py"
Task: "Integration test for import execute in backend/tests/integration/test_import_api.py"

# Launch backend models/services in parallel:
Task: "Implement MyAB CSV parser in backend/src/services/csv_parser.py"
Task: "Implement account prefix parsing in backend/src/services/csv_parser.py"

# Launch frontend components in parallel:
Task: "Add batch import menu entry in frontend/src/components/Sidebar.tsx"
Task: "Create import page route in frontend/src/app/[locale]/ledgers/[ledgerId]/import/page.tsx"
Task: "Create ImportTypeSelector component"
Task: "Create CsvUploader component"
```

---

## Implementation Strategy

### MVP First (User Story 1+2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Stories 1+2 (MyAB CSV import + entry point)
4. **STOP and VALIDATE**: Test MyAB import end-to-end
5. Deploy/demo if ready - users can now migrate from MyAB

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Stories 1+2 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 3 → Test independently → Deploy/Demo (Full feature!)
4. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Stories 1+2 backend
   - Developer B: User Stories 1+2 frontend
   - Or: Developer A: User Stories 1+2, Developer B: User Story 3
3. Stories complete and integrate independently

---

## Summary

| Phase             | Tasks        | Parallel              | Story |
| ----------------- | ------------ | --------------------- | ----- |
| 1. Setup          | T001-T006    | 4                     | -     |
| 2. Foundational   | T007-T011    | 4                     | -     |
| 3. User Story 1+2 | T012-T042    | 12                    | MVP   |
| 4. User Story 3   | T043-T064    | 8                     | P2    |
| 5. Polish         | T065-T073    | 5                     | -     |
| **Total**         | **73 tasks** | **33 parallelizable** |       |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- MVP scope: Phase 1 + 2 + 3 (MyAB import) - core value delivered
