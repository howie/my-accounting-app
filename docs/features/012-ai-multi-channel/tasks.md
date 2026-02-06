# Tasks: AI Multi-Channel Integration

**Input**: Design documents from `/docs/features/012-ai-multi-channel/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Per MyAB Constitution Principle II (Test-First Development), tests are MANDATORY and MUST be written BEFORE implementation. Tests must be reviewed/approved before coding begins.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## User Story Mapping

| Story | Priority | Title                    | Plan Phase           |
| ----- | -------- | ------------------------ | -------------------- |
| US4   | P1       | 使用者帳號綁定與管道管理 | Phase 1 (Foundation) |
| US1   | P1       | AI 助手對話記帳          | Phase 2              |
| US2   | P2       | 通訊軟體 Bot 記帳        | Phase 3              |
| US3   | P3       | Email 信用卡帳單自動匯入 | Phase 4              |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install dependencies, create shared models and DB migrations

- [x] T001 Add bot and email dependencies to backend/pyproject.toml (python-telegram-bot, line-bot-sdk, slack-bolt, google-api-python-client, pdfplumber, apscheduler, slowapi)
- [x] T002 Add new environment variables to backend/src/core/config.py (TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, LINE_CHANNEL_SECRET, LINE_CHANNEL_ACCESS_TOKEN, SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_APP_TOKEN, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, ENCRYPTION_KEY)
- [x] T003 [P] Create ChannelType enum and ChannelBinding model in backend/src/models/channel_binding.py per data-model.md
- [x] T004 [P] Create ChannelMessageLog model in backend/src/models/channel_message_log.py per data-model.md
- [x] T005 [P] Create EmailAuthorization model in backend/src/models/email_authorization.py per data-model.md
- [x] T006 [P] Create EmailImportBatch model in backend/src/models/email_import_batch.py per data-model.md
- [x] T007 Add source_channel (VARCHAR(20), nullable) and channel_message_id (UUID, nullable) columns to Transaction model in backend/src/models/transaction.py
- [x] T008 Register new models in backend/src/models/**init**.py and generate Alembic migration
- [x] T009 [P] Create channel binding Pydantic schemas in backend/src/schemas/channel.py (ChannelBindingRead, GenerateCodeRequest, GenerateCodeResponse)
- [x] T010 [P] Create email import Pydantic schemas in backend/src/schemas/email_import.py (EmailAuthorizationRead, EmailImportBatchRead, EmailImportBatchDetail, ParsedTransaction, ConfirmImportRequest)
- [x] T011 [P] Configure SlowAPI rate limiting middleware in backend/src/api/main.py (30 req/min per user for webhook endpoints)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core services that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T012 Create BotMessageHandler in backend/src/services/bot_message_handler.py — shared message processing that wraps ChatService: accept (user_id, text, channel_type, ledger_id) → resolve ChannelBinding → call ChatService.chat() → return formatted reply + log to ChannelMessageLog
- [x] T013 Add User.channel_bindings and User.email_authorizations relationships to backend/src/models/user.py

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 4 — 使用者帳號綁定與管道管理 (Priority: P1) 🎯 MVP

**Goal**: 使用者可在設定頁面產生 OTP 驗證碼，在 Bot 中輸入驗證碼完成帳號綁定，並管理已綁定的管道

**Independent Test**: 在設定頁面產生驗證碼 → 驗證碼正確建立 → 呼叫 verify API 完成綁定 → 管道列表顯示綁定記錄 → 解除綁定後記錄標記為 inactive

### Tests for US4 (MANDATORY — TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**
> Per Constitution Principle II: Tests → Approval → Red → Green → Refactor

- [x] T014 [P] [US4] Contract tests for channel binding API in backend/tests/contract/test_channel_binding_api.py — test list bindings, generate code, unbind endpoints per contracts/channel-binding-api.yaml
- [x] T015 [P] [US4] Unit tests for ChannelBindingService in backend/tests/unit/test_channel_binding_service.py — test OTP generation (6 digits, 5 min TTL), OTP verification (valid/expired/wrong code), bind/unbind logic, duplicate binding rejection
- [x] T016 [P] [US4] Integration test for binding flow in backend/tests/integration/test_channel_binding_flow.py — test full flow: generate code → verify code → binding created → query binding → unbind → binding inactive
- [x] T017 **GATE**: Get test approval from stakeholder before proceeding to implementation
- [x] T018 **GATE**: Verify all US4 tests FAIL (proving they test the missing feature)

### Implementation for US4

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T019 [US4] Implement ChannelBindingService in backend/src/services/channel_binding_service.py — OTP generation (6-digit, 5 min TTL, in-memory dict), OTP verification, create binding, list bindings, unbind (soft delete), validate unique active binding per external_user_id+channel_type
- [x] T020 [US4] Implement channel binding API routes in backend/src/api/routes/channels.py — GET /api/v1/channels/bindings, POST /api/v1/channels/bindings/generate-code, POST /api/v1/channels/bindings/verify-code, DELETE /api/v1/channels/bindings/{binding_id} per contracts/channel-binding-api.yaml
- [x] T021 [US4] Register channel routes in backend/src/api/routes/**init**.py
- [x] T022 [P] [US4] Create frontend API client in frontend/src/lib/api/channels.ts — listBindings(), generateCode(), unbindChannel()
- [x] T023 [P] [US4] Create useChannelBindings hook in frontend/src/lib/hooks/useChannelBindings.ts — TanStack Query queries and mutations
- [x] T024 [US4] Create ChannelBindingList component in frontend/src/components/channels/ChannelBindingList.tsx — display bound channels with status, last used time, unbind button
- [x] T025 [US4] Create BindingCodeDialog component in frontend/src/components/channels/BindingCodeDialog.tsx — select channel type, generate and display 6-digit OTP with countdown timer
- [x] T026 [US4] Create UnbindDialog component in frontend/src/components/channels/UnbindDialog.tsx — confirmation dialog for unbinding
- [x] T027 [US4] Create channel management settings page in frontend/src/app/settings/channels/page.tsx — compose ChannelBindingList + BindingCodeDialog + UnbindDialog
- [x] T028 [US4] Add "管道綁定" navigation item to settings sidebar in frontend/src/components/settings/SettingsNav.tsx + i18n keys
- [x] T029 [US4] Ensure all US4 tests PASS (green phase of TDD) — 31/31 pass, 790 total pass
- [x] T030 [US4] Refactor — no refactoring needed, code is clean

**Checkpoint**: Users can bind/unbind channels via settings page. Channel binding foundation ready for bots.

---

## Phase 4: User Story 1 — AI 助手對話記帳 (Priority: P1)

**Goal**: 使用者透過 ChatGPT、Gemini、Claude 以自然語言進行記帳操作，交易正確建立且可在主應用中查看

**Independent Test**: 透過 ChatGPT GPT Actions 或 Gemini Extension 輸入「午餐花了 120 元」→ 交易建立成功 → 在 web UI 看到新交易

### Tests for US1 (MANDATORY — TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [x] T031 [P] [US1] Unit test for OpenAPI spec generation in backend/tests/unit/test_openapi_spec.py — verify generated spec contains required endpoints (createTransaction, listTransactions, listAccounts), correct auth scheme, and valid OpenAPI 3.1 format
- [x] T032 [P] [US1] Integration test for AI assistant flow in backend/tests/integration/test_ai_assistant_flow.py — simulate external API call with API token auth → create transaction → verify transaction exists
- [x] T033 **GATE**: Get test approval from stakeholder
- [x] T034 **GATE**: Verify all US1 tests FAIL (13 failed, 3 passed)

### Implementation for US1

> **PREREQUISITE**: All tests above must be written, approved, and failing

- [x] T035 [US1] Create OpenAPI spec export in backend/src/api/openapi_export.py + GET /api/v1/openapi-gpt-actions endpoint — filter to ledger/account/transaction endpoints, add Bearer auth scheme
- [x] T036 [US1] Create GPT system prompt template in docs/features/012-ai-multi-channel/prompts/chatgpt-system-prompt.md — accounting assistant persona, available operations, response format in Traditional Chinese
- [x] T037 [P] [US1] Create Gemini Extension function declarations in docs/features/012-ai-multi-channel/prompts/gemini-config.md — map to existing REST API endpoints
- [x] T038 [P] [US1] Document Claude MCP server config in docs/features/012-ai-multi-channel/prompts/claude-mcp-config.md — existing MCP server (Feature 007) already supports all operations
- [x] T039 [US1] Ensure all US1 tests PASS — 16/16 pass, 806 total pass
- [x] T040 [US1] Refactor — no refactoring needed

**Checkpoint**: AI assistants (ChatGPT/Gemini/Claude) can create and query transactions via API/MCP.

---

## Phase 5: User Story 2 — 通訊軟體 Bot 記帳 (Priority: P2)

**Goal**: 使用者透過 Telegram、LINE、Slack Bot 以文字/語音訊息進行記帳，Bot 回覆確認訊息

**Independent Test**: 傳送文字訊息「咖啡 85 元」給 Telegram Bot → Bot 回覆確認 → 交易建立在系統中

### Tests for US2 (MANDATORY — TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T041 [P] [US2] Contract tests for webhook endpoints in backend/tests/contract/test_webhook_api.py — test Telegram/LINE/Slack webhook endpoints: valid signature → 200, invalid signature → 401, rate limited → 429
- [ ] T042 [P] [US2] Unit tests for Telegram adapter in backend/tests/unit/test_telegram_adapter.py — test signature verification, text message parsing, voice message handling, binding verification via OTP, ambiguous input triggering clarification prompt (FR-009), LINE API 429 quota exhaustion handling
- [ ] T043 [P] [US2] Unit tests for LINE adapter in backend/tests/unit/test_line_adapter.py — test HMAC-SHA256 verification, text event parsing, binding verification
- [ ] T044 [P] [US2] Unit tests for Slack adapter in backend/tests/unit/test_slack_adapter.py — test signature verification, event parsing, slash command handling, url_verification challenge
- [ ] T045 [P] [US2] Integration test for bot-to-transaction flow in backend/tests/integration/test_telegram_webhook.py — simulate Telegram webhook → BotMessageHandler → ChatService → transaction created → response sent → ChannelMessageLog recorded
- [ ] T046 **GATE**: Get test approval from stakeholder
- [ ] T047 **GATE**: Verify all US2 tests FAIL

### Implementation for US2

> **PREREQUISITE**: All tests above must be written, approved, and failing

#### Telegram Bot (first priority)

- [ ] T048 [US2] Create Telegram adapter in backend/src/bots/telegram_adapter.py — webhook signature verification (X-Telegram-Bot-Api-Secret-Token), parse Update object, extract text/voice message, resolve ChannelBinding, delegate to BotMessageHandler, format reply
- [ ] T049 [US2] Add voice message handling to Telegram adapter — download OGG file via getFile API, send to LLM provider for speech-to-text (Gemini audio input or fallback), pass transcribed text to BotMessageHandler
- [ ] T050 [US2] Add OTP binding flow to Telegram adapter — detect 6-digit code in message, call ChannelBindingService.verify_code(), reply with binding success/failure

#### LINE Bot

- [ ] T051 [US2] Create LINE adapter in backend/src/bots/line_adapter.py — HMAC-SHA256 signature verification (X-Line-Signature), parse webhook events (MessageEvent), extract text, resolve ChannelBinding, delegate to BotMessageHandler, reply via LINE Reply API
- [ ] T052 [US2] Add OTP binding flow to LINE adapter — same pattern as Telegram

#### Slack Bot

- [ ] T053 [US2] Create Slack adapter in backend/src/bots/slack_adapter.py — HMAC-SHA256 signature verification (X-Slack-Signature + timestamp), handle url_verification challenge, parse event callbacks and slash commands, resolve ChannelBinding, delegate to BotMessageHandler
- [ ] T054 [US2] Add OTP binding flow to Slack adapter — same pattern as Telegram

#### Webhook Routes

- [ ] T055 [US2] Create webhook routes in backend/src/api/routes/webhooks.py — POST /webhooks/telegram, POST /webhooks/line, POST /webhooks/slack, each calling respective adapter with rate limiting
- [ ] T056 [US2] Register webhook routes in backend/src/api/routes/**init**.py (note: webhook routes mount at /webhooks, not /api/v1)
- [ ] T057 [US2] Ensure all US2 tests PASS
- [ ] T058 [US2] Refactor while keeping tests green

**Checkpoint**: Telegram/LINE/Slack bots can receive messages, verify binding, create transactions, and reply with confirmations.

---

## Phase 6: User Story 3 — Email 信用卡帳單自動匯入 (Priority: P3)

**Goal**: 系統定期掃描 Gmail，解析信用卡帳單 email，產生預覽供使用者確認後批次匯入交易

**Independent Test**: 連結 Gmail → 手動觸發掃描 → 系統找到帳單 email → 預覽頁顯示解析出的交易 → 確認匯入 → 交易建立在系統中

### Tests for US3 (MANDATORY — TDD Required) ⚠️

> **CRITICAL: Write these tests FIRST, get approval, ensure they FAIL, THEN implement**

- [ ] T059 [P] [US3] Contract tests for email import API in backend/tests/contract/test_email_import_api.py — test list authorizations, OAuth callback, list batches, get batch detail, confirm import, trigger scan per contracts/email-import-api.yaml
- [ ] T060 [P] [US3] Unit tests for email parser service in backend/tests/unit/test_email_parser_service.py — test HTML email parsing, PDF attachment parsing, transaction extraction (date, merchant, amount), confidence scoring, duplicate detection (message_id + period_hash)
- [ ] T061 [P] [US3] Unit tests for email import service in backend/tests/unit/test_email_import_service.py — test batch creation, user confirmation flow, transaction override application, batch status transitions (PARSED → PENDING_CONFIRMATION → IMPORTING → COMPLETED/FAILED)
- [ ] T062 [P] [US3] Integration test for email import flow in backend/tests/integration/test_email_import_flow.py — test full flow: OAuth → scan → parse → preview → confirm → transactions created with source_channel="email-import"
- [ ] T063 **GATE**: Get test approval from stakeholder
- [ ] T064 **GATE**: Verify all US3 tests FAIL

### Implementation for US3

> **PREREQUISITE**: All tests above must be written, approved, and failing

#### Gmail OAuth2

- [ ] T065 [US3] Implement Gmail OAuth2 service in backend/src/services/email_service.py — generate auth URL (gmail.readonly scope), handle OAuth callback, exchange code for tokens, encrypt and store refresh token, refresh access token when expired
- [ ] T066 [US3] Create email import API routes in backend/src/api/routes/email_import.py — GET /api/v1/email/authorizations, GET /api/v1/email/authorizations/gmail/auth-url, GET /api/v1/email/authorizations/gmail/callback, DELETE /api/v1/email/authorizations/{auth_id}, GET /api/v1/email/import-batches, GET /api/v1/email/import-batches/{batch_id}, POST /api/v1/email/import-batches/{batch_id}/confirm, POST /api/v1/email/scan per contracts/email-import-api.yaml
- [ ] T067 [US3] Register email import routes in backend/src/api/routes/**init**.py

#### Email Parsing

- [ ] T068 [US3] Implement email parser service in backend/src/services/email_parser_service.py — scan Gmail inbox with filters (sender, subject keywords for Taiwan bank credit card statements), parse HTML email body and PDF attachments via LLM, extract structured transaction data (date, merchant, amount, currency), assign confidence score, use category_suggester for account mapping
- [ ] T069 [US3] Implement email import service in backend/src/services/email_import_service.py — create EmailImportBatch from parsed results, apply user overrides from ConfirmImportRequest, batch-create transactions with source_channel="email-import", duplicate detection via email_message_id + statement_period_hash

#### Background Scheduling

- [ ] T070 [US3] Configure APScheduler in backend/src/api/main.py lifespan — add periodic job to scan authorized Gmail accounts (default: every 6 hours), configurable via GMAIL_SCAN_INTERVAL env var

#### Frontend

- [ ] T071 [P] [US3] Create frontend API client in frontend/src/lib/api/emailImport.ts — listAuthorizations(), getAuthUrl(), revokeAuth(), listBatches(), getBatchDetail(), confirmImport(), triggerScan()
- [ ] T072 [P] [US3] Create useEmailImport hook in frontend/src/lib/hooks/useEmailImport.ts — TanStack Query queries and mutations
- [ ] T073 [US3] Create EmailAuthCard component in frontend/src/components/email-import/EmailAuthCard.tsx — show connected Gmail account, connect/disconnect buttons, last sync time
- [ ] T074 [US3] Create ImportBatchList component in frontend/src/components/email-import/ImportBatchList.tsx — list import batches with status badges, parsed/imported counts, click to view detail
- [ ] T075 [US3] Create ImportPreview component in frontend/src/components/email-import/ImportPreview.tsx — table of parsed transactions with editable from/to accounts, skip checkbox, confidence indicator, needs_review highlight
- [ ] T076 [US3] Create ImportConfirmDialog component in frontend/src/components/email-import/ImportConfirmDialog.tsx — summary of transactions to import, confirm/cancel buttons
- [ ] T077 [US3] Create email settings page in frontend/src/app/settings/email/page.tsx — compose EmailAuthCard + ImportBatchList + ImportPreview + ImportConfirmDialog
- [ ] T078 [US3] Add "Email 匯入" navigation item to settings sidebar in frontend/src/components/settings/SettingsNav.tsx
- [ ] T079 [US3] Ensure all US3 tests PASS
- [ ] T080 [US3] Refactor while keeping tests green

**Checkpoint**: Gmail connected, credit card statements auto-parsed, preview and batch import working.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T081 [P] Add comprehensive error messages for all channel operations — user-friendly error responses in Traditional Chinese for all bot/email/binding failures
- [ ] T082 [P] Add channel source filtering to transaction list — frontend filter option to show transactions by source_channel in frontend/src/components/filters/TransactionFilters.tsx
- [ ] T083 Verify data integrity compliance — all channel-created transactions maintain double-entry bookkeeping, audit trails include source_channel in AuditLog.extra_data
- [ ] T084 Security hardening — review all webhook signature verifications, ensure ENCRYPTION_KEY is used for OAuth tokens, verify rate limiting works correctly
- [ ] T085 [P] Update quickstart.md with actual deployment steps and verified bot setup instructions in docs/features/012-ai-multi-channel/quickstart.md
- [ ] T086 Run end-to-end validation — test complete flows from binding through transaction creation for each channel type
- [ ] T087 [P] Implement channel authorization expiry detection and user notification in backend/src/services/channel_binding_service.py — periodic check for expired bot tokens and email OAuth tokens, notify user via available channel or email to re-authorize (FR-013)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US4 — Binding (Phase 3)**: Depends on Phase 2 — BLOCKS US2 (bots need binding to work)
- **US1 — AI Assistants (Phase 4)**: Depends on Phase 2 — independent of US4
- **US2 — Messaging Bots (Phase 5)**: Depends on Phase 2 + Phase 3 (US4) — bots need channel binding
- **US3 — Email Import (Phase 6)**: Depends on Phase 2 — independent of US4, US1, US2
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

```
Phase 1 (Setup) → Phase 2 (Foundation)
                       │
                       ├──→ Phase 3 (US4: Binding) ──→ Phase 5 (US2: Bots)
                       │
                       ├──→ Phase 4 (US1: AI Assistants)  [independent]
                       │
                       └──→ Phase 6 (US3: Email Import)   [independent]

                       All ──→ Phase 7 (Polish)
```

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Services before API routes
- Backend before frontend
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- Phase 1: T003, T004, T005, T006 (all models) can run in parallel
- Phase 1: T009, T010, T011 (schemas + middleware) can run in parallel
- After Phase 2: US1 (Phase 4) and US3 (Phase 6) can start in parallel with US4 (Phase 3)
- Within US2: T041–T045 (all test files) can run in parallel
- Within US2: Telegram, LINE, Slack adapters can be implemented sequentially (shared patterns)
- Within US3: T059–T062 (all test files) can run in parallel
- Within US3: T071, T072 (frontend API + hook) can run in parallel with backend work

---

## Parallel Example: Phase 1 Setup

```bash
# Launch all model files in parallel:
Task: "Create ChannelBinding model in backend/src/models/channel_binding.py"
Task: "Create ChannelMessageLog model in backend/src/models/channel_message_log.py"
Task: "Create EmailAuthorization model in backend/src/models/email_authorization.py"
Task: "Create EmailImportBatch model in backend/src/models/email_import_batch.py"

# Launch all schema files in parallel:
Task: "Create channel schemas in backend/src/schemas/channel.py"
Task: "Create email import schemas in backend/src/schemas/email_import.py"
Task: "Configure SlowAPI rate limiting in backend/src/api/main.py"
```

## Parallel Example: US2 Tests

```bash
# Launch all US2 test files in parallel:
Task: "Contract tests for webhooks in backend/tests/contract/test_webhook_api.py"
Task: "Unit tests for Telegram adapter in backend/tests/unit/test_telegram_adapter.py"
Task: "Unit tests for LINE adapter in backend/tests/unit/test_line_adapter.py"
Task: "Unit tests for Slack adapter in backend/tests/unit/test_slack_adapter.py"
Task: "Integration test for bot flow in backend/tests/integration/test_telegram_webhook.py"
```

---

## Implementation Strategy

### MVP First (US4 + US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US4 (Channel Binding)
4. Complete Phase 4: US1 (AI Assistants)
5. **STOP and VALIDATE**: Test binding + AI assistant flow independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add US4 (Binding) → Settings page shows channel management → Deploy
3. Add US1 (AI Assistants) → ChatGPT/Gemini can create transactions → Deploy
4. Add US2 (Bots) → Telegram/LINE/Slack bots work → Deploy
5. Add US3 (Email) → Gmail auto-import works → Deploy
6. Each story adds value without breaking previous stories

---

## Summary

| Metric                        | Count                |
| ----------------------------- | -------------------- |
| Total Tasks                   | 87                   |
| Phase 1 (Setup)               | 11                   |
| Phase 2 (Foundation)          | 2                    |
| Phase 3 (US4 — Binding)       | 17                   |
| Phase 4 (US1 — AI Assistants) | 10                   |
| Phase 5 (US2 — Bots)          | 18                   |
| Phase 6 (US3 — Email Import)  | 22                   |
| Phase 7 (Polish)              | 7                    |
| Parallel Opportunities        | 28 tasks marked [P]  |
| MVP Scope                     | US4 + US1 (40 tasks) |

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
