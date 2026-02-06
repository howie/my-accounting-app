# Research: AI Multi-Channel Integration

**Feature**: 012-ai-multi-channel
**Date**: 2026-02-06

## R1: Bot Framework Architecture

### Decision

使用各平台原生 SDK 搭配共用 message handler 模式，而非統一 bot framework。

### Rationale

- 各平台 SDK（python-telegram-bot、line-bot-sdk、slack-bolt）都是官方維護，穩定且文件完善
- 統一 framework（如 Botpress、Rasa）會增加不必要的抽象層，違反 Constitution Principle IV（簡潔性）
- 共用 message handler 層可以抽象自然語言解析和記帳邏輯，各 bot adapter 只負責平台特定的 webhook 驗證和訊息格式轉換

### Alternatives Considered

- **Botpress/Rasa**: 過於複雜，個人記帳場景不需要對話流管理引擎
- **單一通用 adapter**: 各平台差異太大（webhook 格式、認證方式、語音支援），強行統一會導致大量特殊處理

---

## R2: Webhook vs Polling 模式

### Decision

所有 bot 使用 webhook 模式，掛載在現有 FastAPI application 上。

### Rationale

- Webhook 比 polling 更省資源，適合雲端部署（Feature 011 前提）
- FastAPI 已有完整的路由系統，新增 webhook endpoint 成本極低
- 各平台都原生支援 webhook + signature verification

### Alternatives Considered

- **Long polling**: 開發時較簡單，但不適合生產環境（持續消耗連線）
- **獨立 webhook 服務**: 增加維運複雜度，且現有 FastAPI 足以處理

---

## R3: 自然語言解析策略

### Decision

複用現有 ChatService + LLM provider 架構，為 bot 訊息加入精簡版 system prompt，直接使用現有的 tool definitions（create_transaction、list_accounts 等）。

### Rationale

- ChatService 已實作完整的 tool calling loop，包含 list_accounts、get_account、create_transaction、list_transactions、list_ledgers
- LLM provider 已支援 Gemini、Claude、Ollama，provider-agnostic 設計可直接沿用
- Bot 訊息本質上和 chat panel 相同，只是輸入管道不同

### Alternatives Considered

- **自建 NLP 規則引擎**: 初期看似簡單，但維護成本高，且正則表達式無法涵蓋所有自然語言變體
- **獨立 LLM 呼叫**: 會重複 ChatService 的 tool calling 邏輯，違反 DRY 原則

---

## R4: 使用者身份綁定機制

### Decision

採用驗證碼（OTP）綁定模式：使用者在 web UI 產生一次性驗證碼，在 bot 中輸入驗證碼完成帳號綁定。

### Rationale

- 簡單安全：6 位數驗證碼 + 5 分鐘有效期，無需複雜的 OAuth 流程
- 使用者體驗佳：在設定頁產生碼 → 在 bot 中貼上 → 完成
- 各 bot 平台都能取得唯一的外部使用者 ID（Telegram chat_id、LINE user_id、Slack user_id）

### Alternatives Considered

- **Deep link**: 部分平台支援，但實作方式不統一
- **Email 驗證**: 過於繁瑣，使用者已登入 web UI，不需再驗證 email

---

## R5: Telegram 語音訊息處理

### Decision

使用 Telegram Bot API 的 `getFile` 取得語音檔案（OGG 格式），透過 LLM provider 的語音轉文字功能（Gemini 支援音訊輸入）或 OpenAI Whisper API 轉為文字，再走標準文字解析流程。

### Rationale

- Telegram Bot API 提供直接的語音檔案下載
- Gemini 2.0 Flash 原生支援音訊輸入，可直接送入分析
- 轉為文字後即可複用完整的文字記帳流程

### Alternatives Considered

- **本地 Whisper 模型**: 需要額外計算資源，雲端部署成本增加
- **Telegram 內建轉文字**: Telegram Premium 功能，非所有使用者可用

---

## R6: Email 帳單解析策略

### Decision

使用 Gmail API（OAuth2，readonly scope）讀取 email，以 LLM 解析 HTML email 內容和 PDF 附件中的交易明細。

### Rationale

- Gmail API 比 IMAP 更安全（OAuth2 vs 密碼）、功能更豐富（搜尋、過濾）
- LLM 解析比正則表達式更彈性，能處理不同銀行的帳單格式
- `gmail.readonly` scope 是最小權限，只讀不寫

### Alternatives Considered

- **IMAP 直連**: 需要 app password 或開啟低安全性應用，安全性較差
- **規則式解析器**: 每間銀行需要獨立規則，維護成本極高
- **OCR for PDF**: LLM 已能處理結構化 PDF，不需額外 OCR 層

---

## R7: Email 重複偵測

### Decision

使用 email Message-ID + 帳單期間 hash 作為唯一識別碼，存入 EmailImportBatch 表避免重複匯入。

### Rationale

- Email Message-ID 是 RFC 2822 標準的唯一識別碼
- 配合帳單期間可以防止同一期帳單從不同 email 重複匯入
- 與現有 ImportSession 的 source_file_hash 模式一致

### Alternatives Considered

- **僅用 Message-ID**: 同一帳單可能被轉寄多次，Message-ID 不同
- **交易明細比對**: 計算成本高，且可能有合理的重複交易

---

## R8: 速率限制策略

### Decision

使用 SlowAPI（基於 limits 套件）或 FastAPI middleware 實作 per-user rate limiting，webhook endpoint 每使用者每分鐘 30 次。

### Rationale

- 個人記帳場景下 30 req/min 足夠（正常使用遠低於此）
- Per-user 而非 per-IP，因為 bot webhook 來自平台固定 IP
- SlowAPI 與 FastAPI 整合良好，可以直接用 decorator

### Alternatives Considered

- **Per-IP limiting**: 所有 bot webhook 來自同一平台 IP，會誤擋正常請求
- **雲端 WAF/API Gateway**: 個人項目過於複雜
- **無限制**: 存在被惡意利用的風險（攻擊者偽造 webhook）

---

## R9: ChatGPT / Gemini 整合方式

### Decision

- ChatGPT: 透過 OpenAPI spec 定義 GPT Actions，連接現有 REST API
- Gemini: 透過 MCP protocol（Gemini 已支援）或 Function Calling 對接 REST API
- Claude: 已有 MCP server（Feature 007）

### Rationale

- ChatGPT Actions 使用 OpenAPI spec，FastAPI 自動生成，工作量最低
- Gemini 2.0 已開始支援 MCP，可直接複用現有 MCP server
- 三個 AI 助手都不需要額外的 backend 改動，只需產生正確的 API spec / MCP 配置

### Alternatives Considered

- **每個 AI 建立獨立後端**: 不必要，現有 API + MCP 已足夠
- **統一 proxy 層**: 增加複雜度，各 AI 直接存取 API 更簡單

---

## R10: Background Task 排程（Email 掃描）

### Decision

使用 APScheduler 搭配 FastAPI lifespan event 管理定時排程。

### Rationale

- APScheduler 是 Python 生態最成熟的排程套件
- FastAPI lifespan context manager 可以優雅地啟動/停止排程
- 避免引入 Celery 等分散式任務佇列（個人項目不需要）

### Alternatives Considered

- **Celery + Redis**: 過於複雜，需要額外的 broker 服務
- **Cron job**: 需要獨立的 script，不好管理
- **FastAPI BackgroundTasks**: 只適合一次性任務，不適合定時排程

---

## R11: 訊息平台 API 不可用時的處理策略

### Decision

初期不實作 message queue 暫存機制。當平台 API 暫時不可用時，直接回傳錯誤訊息給使用者（如果 webhook 能收到的話），或記錄失敗到 ChannelMessageLog 供後續排查。

### Rationale

- 個人記帳場景下，平台 API 不可用的機率極低且影響範圍有限
- 引入 message queue（Redis/RabbitMQ）會大幅增加架構複雜度，違反 Constitution Principle IV（簡潔性）
- ChannelMessageLog 已記錄所有訊息，失敗的訊息可事後手動補錄
- 若未來確實有暫存需求，可在不改動介面的前提下加入 queue

### Alternatives Considered

- **Redis queue 暫存**: 需要額外的 Redis 服務，個人項目過於複雜
- **DB 暫存 + 重試**: 可行但增加排程複雜度，初期不必要

---

## R12: LINE 免費方案訊息額度耗盡處理

### Decision

在 LINE adapter 中捕捉 LINE API 的 429 Too Many Requests 回應，記錄到 ChannelMessageLog（processing_status=FAILED, error_message 說明額度耗盡），不再嘗試回覆。使用者下次登入 web UI 時可在管道管理頁面看到 LINE 管道的異常狀態。

### Rationale

- LINE 免費方案每月 500 則訊息，個人記帳通常遠低於此上限
- 額度耗盡是月度限制，無法透過重試解決，只能等下個月重置
- 記錄到 message log 確保審計軌跡不中斷

### Alternatives Considered

- **主動通知使用者升級方案**: 過度商業化，不適合個人工具
- **自動切換到其他管道通知**: 增加複雜度，初期不必要
