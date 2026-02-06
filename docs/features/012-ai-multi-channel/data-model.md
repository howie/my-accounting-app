# Data Model: AI Multi-Channel Integration

**Feature**: 012-ai-multi-channel
**Date**: 2026-02-06

## Entity Relationship Overview

```
User 1──N ChannelBinding
User 1──N EmailAuthorization

ChannelBinding 1──N ChannelMessageLog
EmailAuthorization 1──N EmailImportBatch

ChannelMessageLog N──1 Transaction (optional, if message created a transaction)
EmailImportBatch 1──N Transaction (via import_session)
```

---

## New Entities

### ChannelBinding

管道綁定：記錄使用者帳號與外部管道帳號的對應關係。

| Field             | Type         | Constraints                      | Description                   |
| ----------------- | ------------ | -------------------------------- | ----------------------------- |
| id                | UUID         | PK, auto-generated               | 唯一識別碼                    |
| user_id           | UUID         | FK → users.id, NOT NULL, indexed | 綁定的系統使用者              |
| channel_type      | Enum         | NOT NULL                         | TELEGRAM, LINE, SLACK         |
| external_user_id  | VARCHAR(255) | NOT NULL                         | 外部平台的使用者識別碼        |
| display_name      | VARCHAR(100) | NULL                             | 外部平台上的顯示名稱          |
| is_active         | BOOLEAN      | NOT NULL, default TRUE           | 綁定是否有效                  |
| default_ledger_id | UUID         | FK → ledgers.id, NULL            | 預設記帳帳本（簡化 bot 操作） |
| created_at        | TIMESTAMP    | NOT NULL, auto                   | 綁定時間                      |
| last_used_at      | TIMESTAMP    | NULL                             | 最近一次透過此管道操作的時間  |
| unbound_at        | TIMESTAMP    | NULL                             | 解除綁定時間（soft delete）   |

**Indexes**:

- `idx_channel_binding_user` on (user_id)
- `idx_channel_binding_lookup` on (channel_type, external_user_id) WHERE is_active = TRUE — UNIQUE
- `idx_channel_binding_active` on (user_id) WHERE is_active = TRUE

**Constraints**:

- 同一 channel_type + external_user_id 在 is_active = TRUE 時必須唯一（一個外部帳號只能綁定一個系統帳號）
- channel_type ENUM: TELEGRAM, LINE, SLACK

**State Transitions**:

- ACTIVE (is_active=TRUE) → UNBOUND (is_active=FALSE, unbound_at set)
- 不可從 UNBOUND 回到 ACTIVE（需重新綁定建立新記錄）

---

### ChannelMessageLog

管道訊息紀錄：記錄所有透過外部管道收到的原始訊息，作為審計軌跡。

| Field              | Type         | Constraints                        | Description                                          |
| ------------------ | ------------ | ---------------------------------- | ---------------------------------------------------- |
| id                 | UUID         | PK, auto-generated                 | 唯一識別碼                                           |
| channel_binding_id | UUID         | FK → channel_bindings.id, NOT NULL | 來源管道綁定                                         |
| channel_type       | Enum         | NOT NULL                           | TELEGRAM, LINE, SLACK（冗餘欄位，方便查詢）          |
| message_type       | Enum         | NOT NULL                           | TEXT, VOICE, COMMAND                                 |
| raw_content        | TEXT         | NOT NULL                           | 原始訊息內容                                         |
| parsed_intent      | VARCHAR(50)  | NULL                               | 解析出的意圖（CREATE_TRANSACTION, QUERY_BALANCE 等） |
| parsed_data        | JSON         | NULL                               | 解析出的結構化資料                                   |
| processing_status  | Enum         | NOT NULL, default RECEIVED         | 處理狀態                                             |
| error_message      | VARCHAR(500) | NULL                               | 處理失敗時的錯誤訊息                                 |
| response_text      | TEXT         | NULL                               | 回覆給使用者的訊息                                   |
| transaction_id     | UUID         | FK → transactions.id, NULL         | 如果建立了交易，關聯的交易 ID                        |
| processing_time_ms | INT          | NULL                               | 處理耗時（毫秒）                                     |
| created_at         | TIMESTAMP    | NOT NULL, auto                     | 收到訊息的時間                                       |

**Indexes**:

- `idx_message_log_binding` on (channel_binding_id)
- `idx_message_log_created` on (created_at)
- `idx_message_log_transaction` on (transaction_id) WHERE transaction_id IS NOT NULL

**processing_status ENUM**: RECEIVED, PROCESSING, COMPLETED, FAILED

**parsed_intent ENUM values**:

- CREATE_TRANSACTION — 建立交易
- QUERY_BALANCE — 查詢餘額
- QUERY_TRANSACTIONS — 查詢交易記錄
- LIST_ACCOUNTS — 列出帳戶
- UNKNOWN — 無法辨識

---

### EmailAuthorization

Email 授權：記錄使用者的 email 存取授權資訊。

| Field                   | Type         | Constraints                      | Description                     |
| ----------------------- | ------------ | -------------------------------- | ------------------------------- |
| id                      | UUID         | PK, auto-generated               | 唯一識別碼                      |
| user_id                 | UUID         | FK → users.id, NOT NULL, indexed | 授權的系統使用者                |
| email_address           | VARCHAR(255) | NOT NULL                         | 授權的 email 地址               |
| provider                | Enum         | NOT NULL                         | GMAIL（未來可擴展）             |
| encrypted_refresh_token | TEXT         | NULL                             | 加密儲存的 OAuth2 refresh token |
| scopes                  | VARCHAR(500) | NOT NULL                         | 授權的 scope 列表               |
| is_active               | BOOLEAN      | NOT NULL, default TRUE           | 授權是否有效                    |
| last_sync_at            | TIMESTAMP    | NULL                             | 最近一次掃描 email 的時間       |
| token_expires_at        | TIMESTAMP    | NULL                             | Token 過期時間                  |
| created_at              | TIMESTAMP    | NOT NULL, auto                   | 授權建立時間                    |
| revoked_at              | TIMESTAMP    | NULL                             | 撤銷授權時間                    |

**Indexes**:

- `idx_email_auth_user` on (user_id)
- `idx_email_auth_active` on (user_id) WHERE is_active = TRUE

**Constraints**:

- 同一 user_id + email_address + provider 在 is_active = TRUE 時唯一

---

### EmailImportBatch

Email 匯入批次：記錄每次 email 帳單匯入的批次資訊。

| Field                  | Type          | Constraints                            | Description                    |
| ---------------------- | ------------- | -------------------------------------- | ------------------------------ |
| id                     | UUID          | PK, auto-generated                     | 唯一識別碼                     |
| email_authorization_id | UUID          | FK → email_authorizations.id, NOT NULL | 來源 email 授權                |
| ledger_id              | UUID          | FK → ledgers.id, NOT NULL              | 匯入目標帳本                   |
| email_message_id       | VARCHAR(255)  | NOT NULL                               | Email RFC 2822 Message-ID      |
| email_subject          | VARCHAR(500)  | NOT NULL                               | Email 主旨                     |
| email_sender           | VARCHAR(255)  | NOT NULL                               | Email 寄件者                   |
| email_date             | TIMESTAMP     | NOT NULL                               | Email 日期                     |
| statement_period_hash  | VARCHAR(64)   | NOT NULL                               | 帳單期間 hash（重複偵測）      |
| parsed_transactions    | JSON          | NULL                                   | LLM 解析出的交易明細（預覽用） |
| parsed_count           | INT           | NOT NULL, default 0                    | 解析出的交易數量               |
| imported_count         | INT           | NOT NULL, default 0                    | 實際匯入的交易數量             |
| failed_count           | INT           | NOT NULL, default 0                    | 解析失敗的交易數量             |
| status                 | Enum          | NOT NULL, default PARSED               | 批次狀態                       |
| error_message          | VARCHAR(1000) | NULL                                   | 錯誤訊息                       |
| user_confirmed_at      | TIMESTAMP     | NULL                                   | 使用者確認匯入的時間           |
| created_at             | TIMESTAMP     | NOT NULL, auto                         | 批次建立時間                   |
| completed_at           | TIMESTAMP     | NULL                                   | 匯入完成時間                   |

**Indexes**:

- `idx_email_batch_auth` on (email_authorization_id)
- `idx_email_batch_ledger` on (ledger_id)
- `idx_email_batch_dedup` on (email_message_id, statement_period_hash) — UNIQUE

**status ENUM**: PARSED, PENDING_CONFIRMATION, IMPORTING, COMPLETED, FAILED

**State Transitions**:

```
PARSED → PENDING_CONFIRMATION → IMPORTING → COMPLETED
                                          → FAILED
```

---

## Existing Model Extensions

### Transaction (existing)

新增可選欄位記錄來源管道：

| Field              | Type        | Change    | Description                                                 |
| ------------------ | ----------- | --------- | ----------------------------------------------------------- |
| source_channel     | VARCHAR(20) | NEW, NULL | 交易來源管道: web, telegram, line, slack, email-import, mcp |
| channel_message_id | UUID        | NEW, NULL | 關聯的 ChannelMessageLog ID（非 FK，僅供追溯）              |

**Validation**: source_channel 可選值: `web`, `telegram`, `line`, `slack`, `email-import`, `mcp`, `NULL`（NULL 表示直接從 web UI 建立的舊交易）

### User (existing)

新增 relationship：

```
User 1──N ChannelBinding (back_populates="user")
User 1──N EmailAuthorization (back_populates="user")
```

---

## Verification Code (Transient)

綁定驗證碼不需要持久化表。使用 in-memory cache（或 Redis，如果可用）：

| Key Pattern           | Value                  | TTL   |
| --------------------- | ---------------------- | ----- |
| `channel_bind:{code}` | `{user_id, ledger_id}` | 5 min |

- 6 位數字驗證碼
- 5 分鐘有效期
- 使用後立即刪除
