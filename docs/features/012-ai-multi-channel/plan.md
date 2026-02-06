# Implementation Plan: AI Multi-Channel Integration

**Branch**: `012-ai-multi-channel` | **Date**: 2026-02-06 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/012-ai-multi-channel/spec.md`

## Summary

讓使用者透過多種管道（ChatGPT、Gemini、Claude、Telegram、LINE、Slack）以自然語言進行記帳操作，並支援 Email 信用卡帳單自動匯入。技術方案是在現有 FastAPI backend 上新增 webhook endpoints 和 bot adapters，複用現有 ChatService + LLM provider 架構處理自然語言意圖解析，以 OTP 驗證碼完成帳號綁定，以 Gmail OAuth2 + LLM 解析完成帳單匯入。

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend)
**Primary Dependencies**: FastAPI, SQLModel, python-telegram-bot, line-bot-sdk, slack-bolt, google-api-python-client, APScheduler, pdfplumber
**Storage**: PostgreSQL 16 (Supabase) — 新增 4 個表
**Testing**: pytest (backend), vitest (frontend)
**Target Platform**: Linux server (cloud deployment via Feature 011)
**Project Type**: Web application (backend + frontend)
**Performance Goals**: Bot 回覆 < 10 秒, 記帳建立 < 5 秒, Email 解析準確率 > 85%
**Constraints**: LINE 免費方案 500 msg/月, 所有 bot/email 服務免費方案
**Scale/Scope**: 個人記帳, < 500 msg/月 across all channels

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - 所有管道的交易金額經過相同的驗證邏輯（DI-001, 0.01~9,999,999.99, 2 decimal places）
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - ChannelMessageLog 記錄所有原始訊息 + 解析結果 + 交易關聯（DI-002）
  - Transaction.source_channel 記錄來源管道
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - Email 匯入需使用者明確確認才匯入（DI-004）
  - Bot 記帳建立後回覆確認訊息
- [x] Is input validation enforced (amounts, dates, account references)?
  - 所有管道共用現有的 transaction validation（ChatService tool calling）
- [x] Are destructive operations reversible?
  - 管道綁定使用 soft delete（is_active flag + unbound_at）
  - Email 授權撤銷不刪除歷史匯入記錄

**Violations**: None

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
  - 每個 Phase 先寫 contract + unit tests
- [x] Will tests be reviewed/approved before coding?
  - 遵循 TDD 流程：Tests → Review → Red → Green → Refactor
- [x] Are contract tests planned for service boundaries?
  - Webhook endpoints、ChannelBindingService、BotMessageHandler、EmailImportService 各有 contract tests
- [x] Are integration tests planned for multi-account transactions?
  - Bot → ChatService → TransactionService 完整流程測試
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - 語音轉文字失敗、LLM 解析失敗、重複帳單偵測、無效驗證碼

**Violations**: None

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - 所有管道建立交易都經過 ChatService → create_transaction tool → TransactionService，複式記帳邏輯不變
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - 不改變現有 transaction 不可變性設計
- [x] Are calculations traceable to source transactions?
  - ChannelMessageLog.transaction_id + Transaction.source_channel + Transaction.channel_message_id 提供完整追溯鏈
- [x] Are timestamps tracked (created, modified, business date)?
  - ChannelMessageLog.created_at、EmailImportBatch.created_at/completed_at/user_confirmed_at
- [x] Is change logging implemented (who, what, when, why)?
  - 現有 AuditLog.extra_data 可存入 channel source 資訊

**Violations**: None

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
  - 使用者需求明確：在日常工具中記帳，減少摩擦力
- [x] Is the design clear over clever (human-auditable)?
  - 每個 bot adapter 職責單一（webhook 驗證 + 格式轉換），共用 BotMessageHandler 處理業務邏輯
- [x] Are abstractions minimized (especially for financial calculations)?
  - 不新增財務計算邏輯，完全複用現有 ChatService + tool calling
- [x] Are complex business rules documented with accounting references?
  - Email 帳單解析的 LLM prompt 會包含明確的欄位提取規則

**Violations**: None

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
  - 所有管道最終都呼叫同一個 TransactionService，計算邏輯一致
- [x] Is data format compatible between desktop and web?
  - 新增的 channel 欄位不影響現有資料格式
- [x] Are platform-specific features clearly documented?
  - 語音記帳僅限 Telegram（spec 已明確）
- [x] Do workflows follow consistent UX patterns?
  - 所有 bot 的綁定流程一致（OTP 驗證碼）
  - 所有 bot 的記帳回覆格式一致
- [x] Does cloud sync maintain transaction ordering?
  - 透過管道建立的交易使用 created_at 排序，與 web 建立的交易一致

**Violations**: None

**Overall Assessment**: PASS

## Project Structure

### Documentation (this feature)

```text
docs/features/012-ai-multi-channel/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research decisions
├── data-model.md        # Data model for new entities
├── quickstart.md        # Quick start guide
├── contracts/           # API contracts
│   ├── channel-binding-api.yaml
│   ├── webhook-api.yaml
│   └── email-import-api.yaml
├── checklists/          # Quality checklists
│   └── requirements.md
├── tasks.md             # Task breakdown (via /speckit.tasks)
└── issues/              # Issue tracking
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── models/
│   │   ├── channel_binding.py       # ChannelBinding model
│   │   ├── channel_message_log.py   # ChannelMessageLog model
│   │   ├── email_authorization.py   # EmailAuthorization model
│   │   └── email_import_batch.py    # EmailImportBatch model
│   ├── schemas/
│   │   ├── channel.py               # Channel binding schemas
│   │   ├── webhook.py               # Webhook schemas
│   │   └── email_import.py          # Email import schemas
│   ├── services/
│   │   ├── channel_binding_service.py   # Binding CRUD + OTP
│   │   ├── bot_message_handler.py       # Shared NLP → action handler
│   │   ├── email_service.py             # Gmail OAuth2 + email reading
│   │   ├── email_parser_service.py      # LLM-based bill parsing
│   │   └── email_import_service.py      # Batch import orchestration
│   ├── bots/
│   │   ├── telegram_adapter.py      # Telegram webhook + message adapter
│   │   ├── line_adapter.py          # LINE webhook + message adapter
│   │   └── slack_adapter.py         # Slack webhook + message adapter
│   └── api/
│       └── routes/
│           ├── channels.py          # Channel binding routes
│           ├── webhooks.py          # Bot webhook routes
│           └── email_import.py      # Email import routes
└── tests/
    ├── unit/
    │   ├── test_channel_binding_service.py
    │   ├── test_bot_message_handler.py
    │   ├── test_email_parser_service.py
    │   └── test_email_import_service.py
    ├── integration/
    │   ├── test_telegram_webhook.py
    │   ├── test_line_webhook.py
    │   ├── test_slack_webhook.py
    │   └── test_email_import_flow.py
    └── contract/
        ├── test_channel_binding_api.py
        ├── test_webhook_api.py
        └── test_email_import_api.py

frontend/
├── src/
│   ├── app/
│   │   └── settings/
│   │       ├── channels/
│   │       │   └── page.tsx         # Channel management settings page
│   │       └── email/
│   │           └── page.tsx         # Email authorization settings page
│   ├── components/
│   │   ├── channels/
│   │   │   ├── ChannelBindingList.tsx    # List bound channels
│   │   │   ├── BindingCodeDialog.tsx     # Generate + display OTP code
│   │   │   └── UnbindDialog.tsx          # Confirm unbinding
│   │   └── email-import/
│   │       ├── EmailAuthCard.tsx         # Gmail authorization card
│   │       ├── ImportBatchList.tsx       # List import batches
│   │       ├── ImportPreview.tsx         # Preview parsed transactions
│   │       └── ImportConfirmDialog.tsx   # Confirm import
│   └── lib/
│       ├── api/
│       │   ├── channels.ts          # Channel binding API client
│       │   └── emailImport.ts       # Email import API client
│       └── hooks/
│           ├── useChannelBindings.ts
│           └── useEmailImport.ts
└── tests/
    └── (component tests as needed)
```

**Structure Decision**: Web application structure (backend + frontend)，延續現有架構。新增 `backend/src/bots/` 模組作為 bot adapter 層，其餘遵循現有的 models/schemas/services/routes 分層。

## Implementation Phases

> **Note**: Phase 編號與 tasks.md 一致（共 7 個 Phase）

### Phase 1: Setup — 共用基礎設施

**依賴**: 無外部依賴（可在本地開發）
**重點**: 安裝依賴、建立所有共用資料模型、DB migration、Pydantic schemas、rate limiting middleware。

產出:

- ChannelBinding、ChannelMessageLog、EmailAuthorization、EmailImportBatch models
- Transaction model 新增 source_channel、channel_message_id 欄位
- Alembic migration
- Channel binding + email import Pydantic schemas
- SlowAPI rate limiting middleware

### Phase 2: Foundational — 阻塞性前置服務

**依賴**: Phase 1
**重點**: 建立所有 user story 共用的核心服務。**此 phase 完成前，任何 user story 都不能開始。**

產出:

- BotMessageHandler（訊息接收 → ChatService → 回覆格式化）
- User model relationships（channel_bindings、email_authorizations）

### Phase 3: US4 — 使用者帳號綁定與管道管理 (P1)

**依賴**: Phase 2
**重點**: OTP 驗證碼綁定流程、管道管理 API、前端設定頁面。此 phase 完成後 US2（Bot）才能開始。

產出:

- ChannelBindingService（OTP 生成/驗證、綁定/解綁）
- Channel binding API routes
- 管道管理前端頁面（設定 > 管道綁定）

### Phase 4: US1 — AI 助手對話記帳 (P1)

**依賴**: Phase 2（不依賴 Phase 3，可與 Phase 3 平行）+ Feature 007（MCP server）
**重點**: 產生 ChatGPT GPT Actions 所需的 OpenAPI spec，配置 Gemini extension，確認 Claude MCP 連線。此 phase 主要是配置和文件工作，code 改動最少。

產出:

- ChatGPT GPT Actions OpenAPI spec（從 FastAPI 自動生成 + 精簡）
- Gemini extension function declarations 或 MCP 配置
- Claude MCP 配置文件更新（如需要）
- 各 AI 助手的 system prompt 範本

### Phase 5: US2 — 通訊軟體 Bot 記帳 (P2)

**依賴**: Phase 2 + Phase 3（Bot 需要管道綁定）
**重點**: 依序實作三個 bot adapter，每個 adapter 包含 webhook 驗證、訊息格式轉換、綁定流程。Telegram 額外支援語音訊息。

產出:

- Telegram adapter + webhook route + 語音轉文字
- LINE adapter + webhook route
- Slack adapter + webhook route + slash commands
- 各 bot 的 webhook signature verification
- Webhook routes

### Phase 6: US3 — Email 信用卡帳單自動匯入 (P3)

**依賴**: Phase 2（不依賴 Phase 3/4/5，可獨立進行）
**重點**: Gmail OAuth2 授權流程、email 掃描排程、LLM 帳單解析、預覽確認匯入流程。

產出:

- Gmail OAuth2 授權流程（backend + frontend）
- Email 掃描排程（APScheduler）
- LLM 帳單解析 service
- 匯入預覽 + 確認 UI
- 重複帳單偵測

### Phase 7: Polish — 跨 Story 打磨

**依賴**: 所有需要的 user story 完成後
**重點**: 錯誤訊息、來源篩選、資料完整性驗證、安全強化、端到端驗證。

產出:

- 完善的繁體中文錯誤訊息
- Transaction 來源管道篩選功能
- 安全性審查（webhook 驗證、token 加密、rate limiting）
- 授權到期偵測與通知（FR-013）

## Dependencies & New Packages

### Backend (pyproject.toml)

```toml
# Bot integrations
"python-telegram-bot>=21.0",
"slack-bolt>=1.18.0",
"line-bot-sdk>=3.5.0",

# Email integration
"google-auth>=2.27.0",
"google-auth-oauthlib>=1.2.0",
"google-api-python-client>=2.114.0",

# PDF parsing (for credit card statements)
"pdfplumber>=0.10.0",

# Background tasks
"apscheduler>=3.10.0",

# Rate limiting
"slowapi>=0.1.9",
```

### Environment Variables

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=

# LINE Bot
LINE_CHANNEL_SECRET=
LINE_CHANNEL_ACCESS_TOKEN=

# Slack Bot
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
SLACK_APP_TOKEN=

# Gmail API
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# Encryption key for OAuth tokens
ENCRYPTION_KEY=
```

## Cost Summary

| Service      | Provider         | Monthly Cost |
| ------------ | ---------------- | ------------ |
| Telegram Bot | Telegram API     | $0           |
| LINE Bot     | LINE Free (500)  | $0           |
| Slack Bot    | Slack Free       | $0           |
| Gmail API    | Google Free Tier | $0           |
| LLM (Gemini) | Gemini Free Tier | $0           |
| **Total**    |                  | **$0/mo**    |

## Security Considerations

1. **Webhook Verification**: 各平台 signature verification（Telegram secret token、LINE HMAC-SHA256、Slack HMAC-SHA256）
2. **Secrets Management**: 所有 token/secret 存在環境變數，不進 Git
3. **Gmail OAuth2**: 最小權限 scope（`gmail.readonly`）
4. **Token Encryption**: OAuth2 refresh token 加密儲存（使用 ENCRYPTION_KEY）
5. **Rate Limiting**: 每使用者每分鐘 30 次請求，防止濫用
6. **Channel Binding Security**: OTP 驗證碼 6 位數 + 5 分鐘有效期 + 單次使用
