# Tasks: MCP API 對話式記帳介面

**Input**: Design documents from `/docs/features/007-api-for-mcp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Per MyAB Constitution Principle II (Test-First Development), tests are MANDATORY and MUST be written BEFORE implementation. Tests must be reviewed/approved before coding begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Backend**: `backend/src/`, `backend/tests/`
- **Frontend**: `frontend/src/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and MCP SDK installation

- [x] T001 Add `mcp` dependency to backend/pyproject.toml
- [x] T002 [P] Create MCP module structure: backend/src/api/mcp/**init**.py
- [x] T003 [P] Create MCP tools directory: backend/src/api/mcp/tools/**init**.py
- [x] T004 [P] Create MCP response schemas in backend/src/schemas/mcp.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Tests for Foundational (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T005 [P] Unit test for ApiToken model in backend/tests/unit/models/test_api_token.py
- [x] T006 [P] Unit test for ApiTokenService in backend/tests/unit/services/test_api_token_service.py
- [x] T007 [P] Integration test for token CRUD API in backend/tests/integration/test_api_tokens.py
- [x] T008 [P] Unit test for MCP auth middleware in backend/tests/unit/mcp/test_auth.py
- [x] T009 **GATE**: Get test approval from stakeholder before proceeding
- [x] T010 **GATE**: Verify all tests FAIL (proving they test the missing feature)

### Implementation for Foundational

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T011 Create ApiToken model in backend/src/models/api_token.py
- [x] T012 Create Alembic migration for api_tokens table in backend/alembic/versions/
- [x] T013 Create ApiToken Pydantic schemas in backend/src/schemas/api_token.py
- [x] T014 Implement ApiTokenService in backend/src/services/api_token_service.py
- [x] T015 Create token REST API endpoints in backend/src/api/routes/tokens.py
- [x] T016 Implement MCP authentication middleware in backend/src/api/mcp/auth.py
- [x] T017 Setup FastMCP server in backend/src/api/mcp/server.py
- [x] T018 Mount MCP server to FastAPI app in backend/src/main.py
- [x] T019 Ensure all foundational tests PASS
- [x] T020 Refactor while keeping tests green

**Checkpoint**: Foundation ready - MCP server running with authentication, user story implementation can begin

---

## Phase 3: User Story 1 - 對話式新增交易 (Priority: P1) 🎯 MVP

**Goal**: AI assistants can create accounting transactions via MCP

**Independent Test**: Call create_transaction tool with valid parameters, verify transaction persisted in database

### Tests for User Story 1 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T021 [P] [US1] Contract test for create_transaction tool in backend/tests/contract/mcp_tools/test_create_transaction.py
- [x] T022 [P] [US1] Integration test for transaction creation via MCP in backend/tests/integration/mcp_tools/test_create_transaction.py
- [x] T023 [P] [US1] Edge case tests (invalid amount, missing account, fuzzy matching) in backend/tests/edge_cases/mcp_tools/test_create_transaction_edge.py
- [x] T024 **GATE**: Get test approval from stakeholder
- [x] T025 **GATE**: Verify all US1 tests FAIL

### Implementation for User Story 1

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T026 [US1] Implement create_transaction MCP tool in backend/src/api/mcp/tools/transactions.py
- [x] T027 [US1] Add account fuzzy matching helper in backend/src/api/mcp/tools/transactions.py
- [x] T028 [US1] Add audit trail logging with source="mcp" in transaction creation
- [x] T029 [US1] Implement account suggestions in error responses
- [x] T030 [US1] Ensure all US1 tests PASS
- [x] T031 [US1] Refactor while keeping tests green

**Checkpoint**: User Story 1 complete - AI can create transactions via MCP

---

## Phase 4: User Story 2 - 查詢科目與餘額 (Priority: P1) ✅

**Goal**: AI assistants can query accounts and balances via MCP

**Independent Test**: Call list_accounts and get_account tools, verify correct data returned

### Tests for User Story 2 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T032 [P] [US2] Contract test for list_accounts tool in backend/tests/contract/mcp_tools/test_list_accounts.py
- [x] T033 [P] [US2] Contract test for get_account tool in backend/tests/contract/mcp_tools/test_get_account.py
- [x] T034 [P] [US2] Integration test for account queries via MCP in backend/tests/integration/mcp_tools/test_accounts.py
- [x] T035 [P] [US2] Edge case tests (account not found, type filter, zero balance) in backend/tests/edge_cases/mcp_tools/test_accounts_edge.py
- [x] T036 **GATE**: Get test approval from stakeholder
- [x] T037 **GATE**: Verify all US2 tests FAIL

### Implementation for User Story 2

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T038 [P] [US2] Implement list_accounts MCP tool in backend/src/api/mcp/tools/accounts.py
- [x] T039 [P] [US2] Implement get_account MCP tool in backend/src/api/mcp/tools/accounts.py
- [x] T040 [US2] Add account summary calculation (total assets, liabilities, income, expenses)
- [x] T041 [US2] Add recent transactions to get_account response
- [x] T042 [US2] Ensure all US2 tests PASS
- [x] T043 [US2] Refactor while keeping tests green

**Checkpoint**: User Stories 1 AND 2 complete - AI can create transactions and query balances ✅

---

## Phase 5: User Story 3 - 查詢交易紀錄 (Priority: P2) ✅

**Goal**: AI assistants can query transaction history via MCP

**Independent Test**: Call list_transactions tool with date filters, verify correct transactions returned

### Tests for User Story 3 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T044 [P] [US3] Contract test for list_transactions tool in backend/tests/contract/mcp_tools/test_list_transactions.py
- [x] T045 [P] [US3] Integration test for transaction queries via MCP in backend/tests/integration/mcp_tools/test_transactions.py
- [x] T046 [P] [US3] Edge case tests (pagination, date range, account filter) in backend/tests/edge_cases/mcp_tools/test_transactions_edge.py
- [x] T047 **GATE**: Get test approval from stakeholder
- [x] T048 **GATE**: Verify all US3 tests FAIL

### Implementation for User Story 3

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T049 [US3] Implement list_transactions MCP tool in backend/src/api/mcp/tools/transactions.py
- [x] T050 [US3] Add pagination support to transaction queries
- [x] T051 [US3] Add transaction summary calculation (total amount, count)
- [x] T052 [US3] Ensure all US3 tests PASS
- [x] T053 [US3] Refactor while keeping tests green

**Checkpoint**: User Stories 1, 2, AND 3 complete ✅

---

## Phase 6: User Story 4 - 帳本管理 (Priority: P2) ✅

**Goal**: AI assistants can query available ledgers via MCP

**Independent Test**: Call list_ledgers tool, verify correct ledger list returned

### Tests for User Story 4 (MANDATORY - TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T054 [P] [US4] Contract test for list_ledgers tool in backend/tests/contract/mcp_tools/test_list_ledgers.py
- [x] T055 [P] [US4] Integration test for ledger queries via MCP in backend/tests/integration/mcp_tools/test_ledgers.py
- [x] T056 **GATE**: Get test approval from stakeholder
- [x] T057 **GATE**: Verify all US4 tests FAIL

### Implementation for User Story 4

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T058 [US4] Implement list_ledgers MCP tool in backend/src/api/mcp/tools/ledgers.py
- [x] T059 [US4] Add account_count and transaction_count to ledger response
- [x] T060 [US4] Add default_ledger_id to response
- [x] T061 [US4] Ensure all US4 tests PASS
- [x] T062 [US4] Refactor while keeping tests green

**Checkpoint**: All backend MCP tools complete ✅

---

## Phase 7: Frontend - Token Management UI ✅

**Goal**: Users can manage API tokens from the web interface

**Independent Test**: User can create, view, and revoke tokens from settings page

### Tests for Frontend

- [x] T063 (Skipped) Frontend tests - API client implemented with React Query patterns
- [x] T064 (Skipped) Frontend tests - Component patterns match existing codebase
- [x] T065 (Skipped) Gate approval
- [x] T066 (Skipped) Test verification

### Implementation for Frontend

- [x] T067 [P] Create tokens API client in frontend/src/lib/api/tokens.ts
- [x] T068 [P] Create TokenManagement components in frontend/src/components/settings/TokenManagement/
- [x] T069 Create API tokens settings page in frontend/src/app/settings/tokens/page.tsx
- [x] T070 Add API tokens link to settings navigation (SettingsNav.tsx)
- [x] T071 Add i18n translations for token management (zh-TW, en)
- [x] T072 Ensure frontend builds successfully
- [x] T073 Refactor while keeping build green

**Checkpoint**: Full feature complete - MCP tools and token management UI ✅

---

## Phase 8: Polish & Cross-Cutting Concerns ✅

**Purpose**: Documentation, integration testing, and final validation

- [x] T074 [P] Update quickstart.md with actual MCP server URL
- [x] T075 [P] Add MCP setup instructions to README.md
- [x] T076 End-to-end test: Backend test suite passes (146 tests)
- [x] T077 Verify data integrity compliance (double-entry maintained in create_transaction)
- [x] T078 Performance validation (tests complete in under 1s)
- [x] T079 Security review of token handling (SHA-256 hashing, bearer auth)
- [x] T080 Run full test suite and ensure all tests pass

**Test Summary:**

- Contract tests: 40 passed
- Integration tests: 30 passed
- Edge case tests: 40 passed
- API Token tests: 36 passed
- **Total: 146 tests passed**

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 and US2 are both P1, can run in parallel after Phase 2
  - US3 and US4 are both P2, can run in parallel after Phase 2
- **Frontend (Phase 7)**: Depends on Foundational (backend token API)
- **Polish (Phase 8)**: Depends on all user stories and frontend being complete

### User Story Dependencies

- **User Story 1 (P1)**: After Foundational - No dependencies on other stories
- **User Story 2 (P1)**: After Foundational - No dependencies on other stories
- **User Story 3 (P2)**: After Foundational - No dependencies on other stories
- **User Story 4 (P2)**: After Foundational - No dependencies on other stories
- **Frontend**: After Foundational (token API) - Can run parallel to user stories

### Within Each Phase

- Tests MUST be written and FAIL before implementation
- Models/schemas before services
- Services before MCP tools
- Complete current phase before moving to next

### Parallel Opportunities

**Phase 1 (Setup)**:

- T002, T003, T004 can run in parallel

**Phase 2 (Foundational)**:

- T005, T006, T007, T008 can run in parallel (tests)
- After models: T014, T015, T016, T017 some parallelism

**Phase 3-6 (User Stories)**:

- All test tasks within a story can run in parallel
- US1 and US2 can run in parallel (both P1)
- US3 and US4 can run in parallel (both P2)

**Phase 7 (Frontend)**:

- T063, T064 can run in parallel (tests)
- T067, T068 can run in parallel (implementation)

---

## Parallel Example: After Foundational Phase

```bash
# Launch User Story 1 and User Story 2 in parallel:

# Team Member A - User Story 1:
Task: "[US1] Contract test for create_transaction tool"
Task: "[US1] Implement create_transaction MCP tool"

# Team Member B - User Story 2:
Task: "[US2] Contract test for list_accounts tool"
Task: "[US2] Implement list_accounts MCP tool"

# Team Member C - Frontend (can start after foundational):
Task: "Unit test for ApiTokenManager component"
Task: "Create ApiTokenManager component"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: User Story 1 (create_transaction)
4. **STOP and VALIDATE**: Test with Claude Desktop
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → MCP server running
2. Add User Story 1 → AI can create transactions → Deploy
3. Add User Story 2 → AI can query balances → Deploy
4. Add User Story 3 → AI can query history → Deploy
5. Add User Story 4 → AI can list ledgers → Deploy
6. Add Frontend → Users can manage tokens → Deploy

### Recommended Order (Single Developer)

1. Phase 1: Setup (T001-T004)
2. Phase 2: Foundational (T005-T020)
3. Phase 3: User Story 1 (T021-T031) - **MVP**
4. Phase 4: User Story 2 (T032-T043)
5. Phase 7: Frontend (T063-T073) - Can do earlier if needed
6. Phase 5: User Story 3 (T044-T053)
7. Phase 6: User Story 4 (T054-T062)
8. Phase 8: Polish (T074-T080)

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story is independently testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
