# 012 - AI Multi-Channel Integration Plan

## 目標

透過多種 AI 管道（Slack、Telegram、LINE、ChatGPT、Gemini）進行記帳操作，並支援語音輸入和 Email 信用卡帳單自動匯入。

> **前提**：需先完成 [011-cloud-deployment](../011-cloud-deployment/plan.md)，Backend 部署到雲端後才能接收外部 Webhook。

---

## 一、管道架構總覽

```
┌─────────────────────────────────────────────────────────┐
│                     使用者接入管道                        │
│                                                         │
│  Claude App ──┐                                         │
│  ChatGPT ─────┤  MCP / API  ┐                           │
│  Gemini ──────┘             │                           │
│                              ▼                           │
│  Slack Bot ───┐         ┌──────────┐    ┌────────────┐  │
│  Telegram Bot ┤ Webhook │ FastAPI  │───►│ PostgreSQL │  │
│  LINE Bot ────┘    ───► │ Backend  │    │ (Supabase) │  │
│                         │ + MCP    │    └────────────┘  │
│                         └──────────┘                    │
│                              │                           │
│  Email (IMAP) ──► Scheduled ─┘                           │
│                   Parser                                │
└─────────────────────────────────────────────────────────┘
```

---

## 二、ChatGPT / Gemini 整合（Phase 3）

### 2.1 OpenAPI Schema for ChatGPT Custom GPT Actions

- [ ] 自動生成 OpenAPI 3.1 spec（FastAPI 內建）
- [ ] 建立 ChatGPT GPT Action 的精簡 OpenAPI spec
- [ ] 設定 OAuth / API Key 認證方式
- [ ] 撰寫 GPT system prompt（記帳助手人設）

```yaml
# 精簡的 OpenAPI spec for ChatGPT Actions
openapi: "3.1.0"
info:
  title: "LedgerOne Accounting API"
  version: "1.0"
servers:
  - url: "https://ledgerone-backend.onrender.com/api/v1"
paths:
  /ledgers/{ledger_id}/transactions:
    post:
      summary: "建立交易記錄"
      operationId: "createTransaction"
    get:
      summary: "查詢交易記錄"
      operationId: "listTransactions"
  /ledgers/{ledger_id}/accounts:
    get:
      summary: "查詢帳戶列表"
      operationId: "listAccounts"
```

### 2.2 Google Gemini Extension

- [ ] 使用 Gemini Function Calling 對接 LedgerOne REST API
- [ ] 或透過 MCP Gateway（Gemini 已開始支援 MCP）
- [ ] 設定 Gemini Extension 的 function declarations

---

## 三、Messaging Bot 整合（Phase 4）

### 3.1 共用 Bot 框架

- [ ] 新建 `backend/src/bots/` 模組
- [ ] 實作共用的 message handler（解析自然語言 → 呼叫記帳 service）
- [ ] 利用現有的 LLM provider (Gemini/Claude) 做意圖解析

```python
# backend/src/bots/base.py
class BotMessageHandler:
    """共用的訊息處理邏輯"""

    async def handle_message(self, user_id: str, text: str) -> str:
        """解析自然語言並執行記帳操作"""
        # 1. 透過 LLM 解析意圖（記帳/查詢/報表）
        # 2. 呼叫對應的 service
        # 3. 格式化回覆訊息
        ...
```

### 3.2 Telegram Bot

- [ ] 使用 `python-telegram-bot` 套件
- [ ] Webhook 模式（比 polling 更適合雲端部署）
- [ ] 掛載在 FastAPI：`POST /webhooks/telegram`
- [ ] 功能：文字記帳、語音記帳（Telegram 內建語音轉文字）、查餘額
- **費用**：免費（Telegram Bot API 完全免費）

### 3.3 LINE Bot

- [ ] 使用 `line-bot-sdk` 套件
- [ ] Messaging API Webhook
- [ ] 掛載在 FastAPI：`POST /webhooks/line`
- [ ] 功能：文字記帳、查詢餘額、Rich Menu
- **費用**：免費（LINE Messaging API 免費方案 500 則/月）

### 3.4 Slack Bot

- [ ] 使用 `slack-bolt` 套件
- [ ] Slack Events API + Webhook
- [ ] 掛載在 FastAPI：`POST /webhooks/slack`
- [ ] 功能：Slash command `/expense`、DM 對話記帳、查詢
- **費用**：免費（Slack Free workspace）

### 3.5 優先順序

| 順序 | Bot          | 理由                                       |
| ---- | ------------ | ------------------------------------------ |
| 1    | **Telegram** | 最容易開發、API 最友善、完全免費、支援語音 |
| 2    | **LINE**     | 台灣使用率最高、API 文件完整               |
| 3    | **Slack**    | 適合工作場景，但記帳較少在 Slack           |

---

## 四、Email 信用卡帳單自動匯入（Phase 5）

### 4.1 Email 讀取模組

- [ ] 新建 `backend/src/services/email_service.py`
- [ ] 支援 Gmail API（OAuth2）或 IMAP 協定
- [ ] 定時排程（使用 APScheduler 或簡易 background task）
- [ ] Email 過濾規則（寄件者、主旨關鍵字）

### 4.2 帳單解析引擎

- [ ] 使用 LLM（Gemini/Claude）解析帳單 email 內容
- [ ] 支援 HTML email 解析
- [ ] 支援 PDF 附件帳單解析（需 `pdfplumber`）
- [ ] 交易明細結構化提取：日期、商家、金額、幣別
- [ ] 自動分類（利用現有的 category_suggester）

### 4.3 帳單匯入流程

```
Email 收件匣
    │
    ▼
過濾信用卡帳單 email
    │
    ▼
LLM 解析帳單內容
    │
    ▼
產生 Transaction 預覽
    │
    ▼
[透過 Bot/MCP] 通知使用者確認
    │
    ▼
批次匯入 Transaction
```

### 4.4 Gmail OAuth2 整合

- [ ] Google Cloud Console 建立 OAuth2 credentials
- [ ] Frontend 新增 Gmail 授權頁面
- [ ] 安全儲存 refresh token（加密存 DB）
- **費用**：免費（Gmail API 免費額度足夠個人使用）

---

## 五、需要新增的 Dependencies

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
```

---

## 六、環境變數新增

```env
# === Telegram Bot ===
TELEGRAM_BOT_TOKEN=your-telegram-bot-token
TELEGRAM_WEBHOOK_SECRET=random-secret-string

# === Slack Bot ===
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_SIGNING_SECRET=your-signing-secret
SLACK_APP_TOKEN=xapp-your-app-token

# === LINE Bot ===
LINE_CHANNEL_SECRET=your-channel-secret
LINE_CHANNEL_ACCESS_TOKEN=your-channel-access-token

# === Gmail API ===
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret

# === LLM (existing, needed for bot NLP) ===
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-key
```

---

## 七、實作路線圖

```
Phase 3 ─── ChatGPT & Gemini（低工作量，高價值）
   │        • OpenAPI spec for GPT Actions
   │        • Gemini function calling setup
   │
Phase 4 ─── Messaging Bots（中等工作量）
   │        • Telegram Bot (最先)
   │        • LINE Bot
   │        • Slack Bot
   │
Phase 5 ─── Email 帳單匯入（較高工作量）
            • Gmail OAuth2
            • LLM 帳單解析
            • 自動匯入流程
```

---

## 八、成本總結

| 項目         | 平台                   | 月費      |
| ------------ | ---------------------- | --------- |
| Telegram Bot | Telegram API           | $0        |
| LINE Bot     | LINE Free (500 msg/月) | $0        |
| Slack Bot    | Slack Free             | $0        |
| Gmail API    | Google Free Tier       | $0        |
| LLM (Gemini) | Gemini Free Tier       | $0        |
| **合計**     |                        | **$0/月** |

### 限制

| 限制            | 影響         | 因應措施                  |
| --------------- | ------------ | ------------------------- |
| LINE 500 msg/月 | 大量使用會超 | 個人記帳通常 < 100 msg/月 |

---

## 九、安全性考量

1. **Webhook 驗證**：各 Bot 平台都有 signature 驗證機制
2. **環境變數**：所有 Bot token / secret 存在平台 Environment Variables（不進 Git）
3. **Gmail OAuth2**：使用最小權限 scope（`gmail.readonly`）
4. **Rate Limiting**：各管道 endpoint 應設定 rate limit 防止濫用
