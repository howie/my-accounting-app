# Tasks: Gmail 信用卡帳單自動掃描匯入

**Input**: Design documents from `/docs/features/011-gmail-cc-statement-import/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/gmail-import-api.yaml

**Tests**: Per MyAB Constitution Principle II (Test-First Development), tests are MANDATORY and MUST be written BEFORE implementation.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1, US2, etc.)
- All paths relative to repository root

## User Story Mapping

| ID  | Story                               | Priority | Description                    |
| --- | ----------------------------------- | -------- | ------------------------------ |
| US1 | 連接 Gmail 帳號並授權               | P1       | Gmail OAuth2 connection        |
| US2 | 手動觸發帳單掃描與預覽              | P1       | Manual scan and preview        |
| US3 | 確認匯入帳單到記帳系統              | P1       | Confirm import to accounting   |
| US4 | 設定支援的銀行與 PDF 密碼           | P2       | Bank and password settings     |
| US5 | 定期自動掃描排程                    | P3       | Scheduled auto-scan            |
| US6 | 可擴充的銀行 Parser 架構            | P2       | Extensible parser architecture |
| US7 | 掃描歷史紀錄                        | P3       | Scan history                   |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependencies, and base configuration

- [x] T001 Add Python dependencies to backend/pyproject.toml: google-api-python-client, google-auth-oauthlib, pdfplumber, pikepdf, cryptography, APScheduler
- [x] T002 [P] Create directory structure: backend/src/services/bank_parsers/, backend/tests/unit/test_bank_parsers/, backend/tests/fixtures/pdf/
- [x] T003 [P] Add environment variables to backend/.env.example: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GMAIL_ENCRYPTION_KEY
- [x] T004 [P] Create frontend directory structure: frontend/src/app/[locale]/ledgers/[ledgerId]/gmail-import/, frontend/src/components/gmail-import/
- [x] T005 [P] Add TypeScript types for Gmail import API in frontend/src/lib/api/gmail-import.ts (stubs)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Database & Models

- [x] T006 Create Alembic migration for gmail_connections table in backend/alembic/versions/
- [x] T007 [P] Create GmailConnection model in backend/src/models/gmail_connection.py
- [x] T008 [P] Create UserBankSetting model in backend/src/models/user_bank_setting.py
- [x] T009 [P] Create StatementScanJob model in backend/src/models/gmail_scan.py
- [x] T010 [P] Create DiscoveredStatement model in backend/src/models/gmail_scan.py
- [x] T011 Extend ImportType enum with GMAIL_CC value in backend/src/schemas/data_import.py
- [x] T012 Add email_message_id field to ImportSession model in backend/src/models/import_session.py
- [ ] T013 Run migration: alembic upgrade head

### Encryption Utilities

- [x] T014 Create credential encryption utility in backend/src/services/encryption.py (Fernet-based encrypt/decrypt for tokens and passwords)

### Base Parser Architecture (US6 Foundational)

- [x] T015 Create abstract BankStatementParser base class in backend/src/services/bank_parsers/base.py
- [x] T016 Create parser registry with @register_parser decorator in backend/src/services/bank_parsers/__init__.py
- [x] T017 Create ParsedStatementTransaction dataclass in backend/src/services/bank_parsers/base.py

### API Schemas

- [x] T018 Create Gmail import schemas in backend/src/schemas/gmail_import.py (GmailConnectionResponse, ScanJobResponse, StatementPreviewResponse, etc.)

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - 連接 Gmail 帳號並授權 (Priority: P1) 🎯 MVP

**Goal**: User can connect Gmail via OAuth2 and see connection status

**Independent Test**: Complete OAuth2 flow, verify connection appears in settings page

### Tests for User Story 1 (MANDATORY - TDD Required) ⚠️

- [ ] T019 [P] [US1] Unit test for GmailService.get_auth_url() in backend/tests/unit/test_gmail_service.py
- [ ] T020 [P] [US1] Unit test for GmailService.handle_callback() in backend/tests/unit/test_gmail_service.py
- [ ] T021 [P] [US1] Unit test for GmailService.disconnect() in backend/tests/unit/test_gmail_service.py
- [ ] T022 [P] [US1] Unit test for credential encryption/decryption in backend/tests/unit/test_encryption.py
- [ ] T023 [P] [US1] Integration test for OAuth2 flow in backend/tests/integration/test_gmail_auth.py
- [ ] T024 [P] [US1] API contract test for /gmail/auth/connect endpoint in backend/tests/contract/test_gmail_auth_api.py
- [ ] T025 [P] [US1] API contract test for /gmail/connection GET/DELETE in backend/tests/contract/test_gmail_auth_api.py
- [ ] T026 **GATE**: Get test approval from stakeholder before proceeding
- [ ] T027 **GATE**: Verify all tests FAIL (proving they test the missing feature)

### Implementation for User Story 1

- [x] T028 [US1] Implement GmailService class in backend/src/services/gmail_service.py (get_auth_url, handle_callback, get_connection, disconnect)
- [x] T029 [US1] Implement token encryption/decryption in GmailService using encryption.py
- [x] T030 [US1] Implement auto-refresh token logic in GmailService
- [x] T031 [US1] Create gmail_import_routes.py in backend/src/api/routes/ with OAuth2 endpoints
- [x] T032 [US1] Register routes in backend/src/api/routes/__init__.py
- [ ] T033 [US1] Ensure all tests PASS
- [ ] T034 [US1] Refactor while keeping tests green

### Frontend for User Story 1

- [x] T035 [P] [US1] Create GmailConnectButton component in frontend/src/components/gmail-import/GmailConnectButton.tsx
- [x] T036 [P] [US1] Create gmail-import API client functions in frontend/src/lib/api/gmail-import.ts (connect, getStatus, disconnect)
- [x] T037 [US1] Create Gmail settings page in frontend/src/app/[locale]/ledgers/[ledgerId]/gmail-import/settings/page.tsx
- [ ] T038 [P] [US1] Component test for GmailConnectButton in frontend/tests/components/gmail-import/GmailConnectButton.test.tsx

**Checkpoint**: Gmail connection fully functional - user can connect/disconnect Gmail

---

## Phase 4: User Story 2 - 手動觸發帳單掃描與預覽 (Priority: P1)

**Goal**: User can trigger scan, see found statements, preview transaction details

**Independent Test**: Trigger scan, verify statements found, view parsed transactions

### Tests for User Story 2 (MANDATORY - TDD Required) ⚠️

- [ ] T039 [P] [US2] Unit test for GmailService.search_statements() in backend/tests/unit/test_gmail_service.py
- [ ] T040 [P] [US2] Unit test for GmailService.download_attachment() in backend/tests/unit/test_gmail_service.py
- [ ] T041 [P] [US2] Unit test for PdfParser.decrypt() in backend/tests/unit/test_pdf_parser.py
- [ ] T042 [P] [US2] Unit test for PdfParser.extract_text() in backend/tests/unit/test_pdf_parser.py
- [ ] T043 [P] [US2] Unit test for CtbcParser (中國信託) in backend/tests/unit/test_bank_parsers/test_ctbc_parser.py
- [ ] T044 [P] [US2] Unit test for CathayParser (國泰世華) in backend/tests/unit/test_bank_parsers/test_cathay_parser.py
- [ ] T045 [P] [US2] Unit test for GmailImportService.execute_scan() in backend/tests/unit/test_gmail_import_service.py
- [ ] T046 [P] [US2] Integration test for scan → parse → preview flow in backend/tests/integration/test_gmail_scan.py
- [ ] T047 [P] [US2] API contract test for POST /ledgers/{id}/gmail/scan in backend/tests/contract/test_gmail_scan_api.py
- [ ] T048 [P] [US2] API contract test for GET /gmail/scan/{id}/statements in backend/tests/contract/test_gmail_scan_api.py
- [ ] T049 [P] [US2] API contract test for GET /gmail/statements/{id}/preview in backend/tests/contract/test_gmail_scan_api.py
- [ ] T050 **GATE**: Get test approval from stakeholder
- [ ] T051 **GATE**: Verify all tests FAIL

### Implementation for User Story 2

- [x] T052 [US2] Create PdfParser class in backend/src/services/pdf_parser.py (decrypt with pikepdf, extract text with pdfplumber)
- [x] T053 [US2] Implement GmailService.search_statements() for bank-specific email search
- [x] T054 [US2] Implement GmailService.download_attachment() for PDF download
- [x] T055 [P] [US2] Create CtbcParser in backend/src/services/bank_parsers/ctbc_parser.py
- [x] T056 [P] [US2] Create FubonParser in backend/src/services/bank_parsers/fubon_parser.py
- [x] T057 [P] [US2] Create CathayParser in backend/src/services/bank_parsers/cathay_parser.py
- [x] T058 [P] [US2] Create DbsParser in backend/src/services/bank_parsers/dbs_parser.py
- [x] T059 [P] [US2] Create HsbcParser in backend/src/services/bank_parsers/hsbc_parser.py
- [x] T060 [P] [US2] Create HncbParser in backend/src/services/bank_parsers/hncb_parser.py
- [x] T061 [P] [US2] Create EsunParser in backend/src/services/bank_parsers/esun_parser.py
- [x] T062 [P] [US2] Create SinopacParser in backend/src/services/bank_parsers/sinopac_parser.py
- [x] T063 [US2] Create GmailImportService class in backend/src/services/gmail_import_service.py (execute_scan orchestration)
- [x] T064 [US2] Implement statement discovery and tracking in GmailImportService
- [x] T065 [US2] Implement PDF parsing with parser registry in GmailImportService
- [x] T066 [US2] Add scan and preview endpoints to backend/src/api/routes/gmail_import_routes.py
- [ ] T067 [US2] Integrate CategorySuggester for transaction category suggestions
- [ ] T068 [US2] Ensure all tests PASS
- [ ] T069 [US2] Refactor while keeping tests green

### Frontend for User Story 2

- [x] T070 [P] [US2] Create ScanProgressIndicator component in frontend/src/components/gmail-import/ScanProgressIndicator.tsx
- [x] T071 [P] [US2] Create StatementList component in frontend/src/components/gmail-import/StatementList.tsx
- [x] T072 [P] [US2] Create StatementPreview component in frontend/src/components/gmail-import/StatementPreview.tsx
- [x] T073 [US2] Add scan API functions to frontend/src/lib/api/gmail-import.ts (triggerScan, getScanStatus, getStatements, getPreview)
- [x] T074 [US2] Create Gmail import main page in frontend/src/app/[locale]/ledgers/[ledgerId]/gmail-import/page.tsx
- [ ] T075 [P] [US2] Component test for StatementPreview in frontend/tests/components/gmail-import/StatementPreview.test.tsx

**Checkpoint**: Scan and preview functional - user can find and view statements

---

## Phase 5: User Story 3 - 確認匯入帳單到記帳系統 (Priority: P1)

**Goal**: User can confirm import, transactions created in ledger

**Independent Test**: Preview statement, confirm import, verify transactions in ledger

### Tests for User Story 3 (MANDATORY - TDD Required) ⚠️

- [ ] T076 [P] [US3] Unit test for GmailImportService.import_statement() in backend/tests/unit/test_gmail_import_service.py
- [ ] T077 [P] [US3] Unit test for duplicate detection in import flow in backend/tests/unit/test_gmail_import_service.py
- [ ] T078 [P] [US3] Unit test for atomic import rollback in backend/tests/unit/test_gmail_import_service.py
- [ ] T079 [P] [US3] Integration test for import → transaction creation in backend/tests/integration/test_gmail_import.py
- [ ] T080 [P] [US3] API contract test for POST /ledgers/{id}/gmail/statements/{id}/import in backend/tests/contract/test_gmail_import_api.py
- [ ] T081 [P] [US3] Edge case test for category override during import in backend/tests/unit/test_gmail_import_service.py
- [ ] T082 **GATE**: Get test approval from stakeholder
- [ ] T083 **GATE**: Verify all tests FAIL

### Implementation for User Story 3

- [x] T084 [US3] Implement GmailImportService.import_statement() with ImportService integration
- [x] T085 [US3] Implement category override handling in import flow
- [x] T086 [US3] Implement transaction skip handling for duplicates
- [x] T087 [US3] Add audit trail logging for Gmail imports (source="gmail-statement-import")
- [x] T088 [US3] Update DiscoveredStatement.import_status after successful import
- [x] T089 [US3] Add import endpoint to backend/src/api/routes/gmail_import_routes.py
- [ ] T090 [US3] Ensure all tests PASS
- [ ] T091 [US3] Refactor while keeping tests green

### Frontend for User Story 3

- [x] T092 [US3] Add import confirmation UI to StatementPreview component
- [ ] T093 [US3] Add category editing UI to StatementPreview component
- [x] T094 [US3] Add duplicate warning display to StatementPreview component
- [x] T095 [US3] Add importStatement function to frontend/src/lib/api/gmail-import.ts
- [x] T096 [US3] Add success/error feedback after import

**Checkpoint**: P1 Complete - Full scan → preview → import flow functional (MVP!)

---

## Phase 6: User Story 4 - 設定支援的銀行與 PDF 密碼 (Priority: P2)

**Goal**: User can configure which banks to scan and set PDF passwords

**Independent Test**: Enable bank, set password, verify saved (password masked)

### Tests for User Story 4 (MANDATORY - TDD Required) ⚠️

- [ ] T097 [P] [US4] Unit test for UserBankSetting CRUD in backend/tests/unit/test_user_bank_setting.py
- [ ] T098 [P] [US4] Unit test for password encryption in UserBankSetting in backend/tests/unit/test_user_bank_setting.py
- [ ] T099 [P] [US4] API contract test for GET /gmail/banks in backend/tests/contract/test_gmail_banks_api.py
- [ ] T100 [P] [US4] API contract test for GET/PUT /gmail/banks/settings in backend/tests/contract/test_gmail_banks_api.py
- [ ] T101 **GATE**: Get test approval from stakeholder
- [ ] T102 **GATE**: Verify all tests FAIL

### Implementation for User Story 4

- [x] T103 [US4] Implement bank listing from parser registry in GmailImportService
- [x] T104 [US4] Implement UserBankSetting service for CRUD operations
- [x] T105 [US4] Implement password encryption on save, never expose in response
- [x] T106 [US4] Add bank settings endpoints to backend/src/api/routes/gmail_import_routes.py
- [ ] T107 [US4] Ensure all tests PASS
- [ ] T108 [US4] Refactor while keeping tests green

### Frontend for User Story 4

- [x] T109 [P] [US4] Create BankSettingsPanel component in frontend/src/components/gmail-import/BankSettingsPanel.tsx
- [x] T110 [US4] Add bank settings to Gmail settings page
- [x] T111 [US4] Add getBanks, getBankSettings, updateBankSettings to frontend/src/lib/api/gmail-import.ts

**Checkpoint**: Bank configuration functional - user can enable/disable banks and set passwords

---

## Phase 7: User Story 5 - 定期自動掃描排程 (Priority: P3)

**Goal**: User can configure automatic scanning schedule

**Independent Test**: Enable weekly schedule, verify next scan time shown, wait for scheduled run

### Tests for User Story 5 (MANDATORY - TDD Required) ⚠️

- [ ] T112 [P] [US5] Unit test for GmailScheduler.schedule_scan() in backend/tests/unit/test_gmail_scheduler.py
- [ ] T113 [P] [US5] Unit test for GmailScheduler.cancel_scan() in backend/tests/unit/test_gmail_scheduler.py
- [ ] T114 [P] [US5] API contract test for GET/PUT /gmail/schedule in backend/tests/contract/test_gmail_schedule_api.py
- [ ] T115 **GATE**: Get test approval from stakeholder
- [ ] T116 **GATE**: Verify all tests FAIL

### Implementation for User Story 5

- [x] T117 [US5] Create GmailScheduler class in backend/src/services/gmail_scheduler.py (APScheduler integration)
- [x] T118 [US5] Implement schedule configuration persistence in GmailConnection model
- [x] T119 [US5] Implement scheduled job execution calling GmailImportService.execute_scan()
- [x] T120 [US5] Add schedule endpoints to backend/src/api/routes/gmail_import_routes.py
- [x] T121 [US5] Initialize scheduler on app startup in backend/src/api/main.py
- [ ] T122 [US5] Ensure all tests PASS
- [ ] T123 [US5] Refactor while keeping tests green

### Frontend for User Story 5

- [x] T124 [P] [US5] Create ScheduleSettings component in frontend/src/components/gmail-import/ScheduleSettings.tsx
- [x] T125 [US5] Add schedule settings to Gmail settings page
- [x] T126 [US5] Add getSchedule, updateSchedule to frontend/src/lib/api/gmail-import.ts

**Checkpoint**: Scheduling functional - user can configure auto-scan schedule

---

## Phase 8: User Story 7 - 掃描歷史紀錄 (Priority: P3)

**Goal**: User can view past scan history and statement import status

**Independent Test**: Run multiple scans, view history page, see all past scans with results

### Tests for User Story 7 (MANDATORY - TDD Required) ⚠️

- [ ] T127 [P] [US7] Unit test for scan history query in backend/tests/unit/test_gmail_import_service.py
- [ ] T128 [P] [US7] API contract test for GET /gmail/scan/history in backend/tests/contract/test_gmail_history_api.py
- [ ] T129 **GATE**: Get test approval from stakeholder
- [ ] T130 **GATE**: Verify all tests FAIL

### Implementation for User Story 7

- [x] T131 [US7] Implement scan history query in GmailImportService (paginated, with statement counts)
- [x] T132 [US7] Add history endpoint to backend/src/api/routes/gmail_import_routes.py
- [ ] T133 [US7] Ensure all tests PASS
- [ ] T134 [US7] Refactor while keeping tests green

### Frontend for User Story 7

- [x] T135 [P] [US7] Create ScanHistoryTable component in frontend/src/components/gmail-import/ScanHistoryTable.tsx
- [x] T136 [US7] Create scan history page in frontend/src/app/[locale]/ledgers/[ledgerId]/gmail-import/history/page.tsx
- [x] T137 [US7] Add getScanHistory to frontend/src/lib/api/gmail-import.ts

**Checkpoint**: History functional - user can view all past scans and import status

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements across all user stories

- [ ] T138 [P] Add sample PDF fixtures for each bank parser to backend/tests/fixtures/pdf/
- [ ] T139 [P] Add LLM fallback parsing support to PdfParser (optional, based on env config)
- [ ] T140 [P] Add navigation links to Gmail import pages in sidebar
- [ ] T141 Verify all parsers handle edge cases: foreign currency transactions, installments, refunds
- [ ] T142 [P] Add i18n translations for Gmail import UI strings
- [ ] T143 Verify data integrity: double-entry balance, audit trails for all imports
- [ ] T144 Security review: OAuth2 state validation, credential encryption, no plaintext secrets
- [ ] T145 [P] Update quickstart.md with actual usage examples
- [ ] T146 Performance test: scan 3 banks in under 60 seconds
- [ ] T147 Run full test suite and fix any failures

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies - can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 - BLOCKS all user stories
- **Phase 3-8 (User Stories)**: All depend on Phase 2 completion
- **Phase 9 (Polish)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 2 (Foundational) ─┬──> US1 (Gmail Connection) ─┬──> US2 (Scan & Preview) ──> US3 (Import)
                        │                             │
                        │                             └──> US4 (Bank Settings)
                        │
                        └──> US5 (Scheduling) [can start after US1]
                        └──> US7 (History) [can start after US2]
```

- **US1**: Can start after Phase 2 - No story dependencies
- **US2**: Depends on US1 (needs Gmail connection to scan)
- **US3**: Depends on US2 (needs parsed statements to import)
- **US4**: Can start after Phase 2 - Optional enhancement for US2
- **US5**: Depends on US1 (needs Gmail connection for scheduling)
- **US7**: Depends on US2 (needs scan jobs to show history)

### Parallel Opportunities

**Within Phase 2**:
```bash
# All models can be created in parallel:
T007 GmailConnection model
T008 UserBankSetting model
T009 StatementScanJob model
T010 DiscoveredStatement model
```

**Within US2 (Bank Parsers)**:
```bash
# All bank parsers can be created in parallel:
T055 CtbcParser
T056 FubonParser
T057 CathayParser
T058 DbsParser
T059 HsbcParser
T060 HncbParser
T061 EsunParser
T062 SinopacParser
```

**Cross-Story Parallelism** (with multiple developers):
```bash
# After Phase 2, multiple stories can progress:
Developer A: US1 (Gmail Connection) → US2 (Scan) → US3 (Import)
Developer B: US4 (Bank Settings) + US5 (Scheduling)
Developer C: US7 (History) [after US2 models exist]
```

---

## Implementation Strategy

### MVP First (P1 Stories Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL)
3. Complete Phase 3: US1 - Gmail Connection
4. Complete Phase 4: US2 - Scan & Preview
5. Complete Phase 5: US3 - Confirm Import
6. **STOP and VALIDATE**: Test full flow end-to-end
7. Deploy/demo if ready (MVP complete!)

### Incremental Delivery

| Milestone | Stories Included           | User Value                              |
| --------- | -------------------------- | --------------------------------------- |
| MVP       | US1 + US2 + US3            | Full scan → preview → import flow       |
| v1.1      | + US4                      | Custom bank settings and passwords      |
| v1.2      | + US5 + US7                | Automatic scheduling + history tracking |
| v1.3      | Polish                     | LLM fallback, performance, edge cases   |

### Suggested MVP Scope

**Minimum viable product = US1 + US2 + US3** (Phases 3-5)

This delivers the core value: connect Gmail, scan statements, import transactions. Bank settings (US4) can use hardcoded defaults initially.

---

## Task Summary

| Phase             | Task Range  | Count | Parallel Tasks |
| ----------------- | ----------- | ----- | -------------- |
| Phase 1: Setup    | T001-T005   | 5     | 4              |
| Phase 2: Found.   | T006-T018   | 13    | 8              |
| Phase 3: US1      | T019-T038   | 20    | 14             |
| Phase 4: US2      | T039-T075   | 37    | 24             |
| Phase 5: US3      | T076-T096   | 21    | 8              |
| Phase 6: US4      | T097-T111   | 15    | 6              |
| Phase 7: US5      | T112-T126   | 15    | 4              |
| Phase 8: US7      | T127-T137   | 11    | 4              |
| Phase 9: Polish   | T138-T147   | 10    | 5              |
| **Total**         |             | **147**| **77**        |

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- Each user story independently completable and testable
- Verify tests FAIL before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Bank parsers (T055-T062) can all run in parallel
- Test fixtures needed for each bank - collect sample PDFs
