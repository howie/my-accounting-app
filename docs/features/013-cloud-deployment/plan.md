# 013 - Cloud Deployment & AI Multi-Channel Integration Plan

## 目標

將 LedgerOne 部署到雲端，透過 MCP 及多種 AI 管道（Slack、Telegram、LINE、Claude App、ChatGPT、Gemini）進行記帳操作，並支援語音輸入和 Email 信用卡帳單自動匯入。

---

## 一、部署架構總覽

```
┌─────────────────────────────────────────────────────────────┐
│                     使用者接入管道                            │
│                                                             │
│  Claude App ──┐                                             │
│  ChatGPT ─────┤  MCP / API  ┐                               │
│  Gemini ──────┘             │                               │
│                              ▼                               │
│  Slack Bot ───┐         ┌──────────┐      ┌────────────┐    │
│  Telegram Bot ┤ Webhook │ FastAPI  │ ───► │ PostgreSQL │    │
│  LINE Bot ────┘    ───► │ Backend  │      │ (Supabase) │    │
│                         │ + MCP    │      └────────────┘    │
│                         └──────────┘                        │
│                              │                               │
│  Email (IMAP) ──► Scheduled ─┘      ┌────────────┐          │
│                   Parser            │  Next.js   │          │
│                                     │  Frontend  │          │
│                                     │  (Vercel)  │          │
│                                     └────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、部署方案（以免費/最低成本為目標）

> **詳細平台比較分析見 [research.md](./research.md)**

### 推薦方案（修訂版）：Fly.io + Vercel + Supabase

| 元件 | 平台 | 費用 | 說明 |
|------|------|------|------|
| **Frontend** | **Vercel Hobby** | **$0/月** | Next.js 原生支援，全球 CDN，zero config |
| **Backend + MCP** | **Fly.io** | **~$4-6/月** | MCP 一級支援，東京節點，冷啟動 2-5 秒 |
| **PostgreSQL** | **Supabase Free** | **$0/月** | 500MB 儲存，PostgreSQL 16，自動備份 |
| **總計** | | **~$4-6/月** | |

#### 為何改推 Fly.io 而非 Render？

經深入分析後發現 Render 免費方案有**兩個致命問題**：
1. **POST 請求無法喚醒休眠服務**——只有 GET 能喚醒，POST 會被丟棄。MCP 和 Bot Webhook 都是 POST，這直接導致核心功能不可用
2. **冷啟動 30-60 秒** vs Fly.io 的 2-5 秒

此外，Fly.io 對 MCP 有**官方一級支援**，含 SSE 和 Streamable HTTP 的專門文件。

#### 為何不用 Cloudflare 取代 Vercel？

Cloudflare Workers 在成本上更有優勢（免費 + 無限 bandwidth），但：
1. Next.js 需透過 `@opennextjs/cloudflare` adapter，**地雷很多**（Turbopack 不能用、Edge runtime 不支援、build cache 差導致每次 ~15 分鐘）
2. Vercel 是 Next.js 的開發者，零配置直接部署
3. 個人記帳 app 的 Vercel Hobby 免費方案完全夠用
4. 未來若需商業化，再遷移到 Cloudflare（$5/月）即可

### 方案比較表

| 方案 | Frontend | Backend | Database | 月費 | 適用情境 |
|------|----------|---------|----------|------|----------|
| **A (推薦)** | Vercel | Fly.io | Supabase | ~$4-6 | 個人使用，MCP 核心需求 |
| **B (純免費)** | Cloudflare | Render | Supabase | $0 | 測試/開發，可接受各種限制 |
| **C (最佳平衡)** | Cloudflare $5 | Fly.io | Supabase | ~$9-11 | 長期運行，有商業化可能 |
| **D (最簡運維)** | Vercel Pro $20 | Fly.io | Supabase | ~$24-26 | 重視開發效率 |

### 各平台 Free Tier 限制

#### Vercel Hobby (Frontend)
- 100GB bandwidth/月，150K function requests/月
- 自動 HTTPS + 自訂域名，Git push 自動部署
- **限制**：禁止商業使用（個人記帳 app 不受影響）

#### Fly.io (Backend)
- 新用戶無免費方案，Pay As You Go
- shared-cpu-1x + 512MB RAM ≈ $3.57/月（24/7 運行）
- 冷啟動 2-5 秒，可設定 auto-stop 節省費用
- **18 個區域**含東京（台灣延遲最低）
- **MCP Streamable HTTP 一級支援**
- IPv4 $2/月/app（可用 IPv6 免費）

#### Supabase Free (PostgreSQL)
- 500MB 資料庫儲存，2 個免費專案
- 自動每日備份（7天保留）
- **限制**：7天未活動會暫停（需 cron ping 保持活躍）

---

## 三、部署所需的開發工作

### Phase 0：部署基礎設施準備（必做）

#### 0.1 Backend 生產環境配置
- [ ] 新增 `ENVIRONMENT=production` 配置處理
- [ ] 設定 production CORS origins（Vercel 的域名）
- [ ] 啟用 production 模式下的 Alembic migration（啟動時自動 migrate）
- [ ] 設定 `docs_url=None`, `redoc_url=None` (production 已有)
- [ ] 新增 Gunicorn 作為 production WSGI server（取代 uvicorn --reload）
- [ ] 新增 `start.sh` 啟動腳本（migration + server start）

```bash
# start.sh
#!/bin/bash
alembic upgrade head
gunicorn src.api.main:app -w 2 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT:-8000}
```

#### 0.2 Frontend 生產環境配置
- [ ] 設定 `NEXT_PUBLIC_API_URL` 指向 Fly.io backend URL
- [ ] 確保 `next.config.js` 有 `output: 'standalone'` (Docker 部署用)
- [ ] 新增 Vercel 配置 (`vercel.json`) 或使用預設 Next.js 設定

#### 0.3 Database Migration 到 Supabase
- [ ] 在 Supabase 建立專案並取得連線字串
- [ ] 調整 `DATABASE_URL` 支援 Supabase 的 connection pooling (pgBouncer)
- [ ] 測試 Alembic migration 在 Supabase 上是否正常
- [ ] 設定 SSL mode (`?sslmode=require`)

#### 0.4 CI/CD Pipeline 調整
- [ ] GitHub Actions 新增 deploy job（push to main → auto deploy）
- [ ] Fly.io 設定 `fly deploy` 自動部署（可透過 GitHub Actions）
- [ ] Vercel 連接 GitHub repo auto-deploy
- [ ] 新增 production environment secrets 管理

#### 0.5 Fly.io 配置檔
```toml
# fly.toml
app = "ledgerone-backend"
primary_region = "nrt"  # Tokyo - 對台灣延遲最低

[build]
  dockerfile = "backend/Dockerfile"

[env]
  ENVIRONMENT = "production"
  PORT = "8000"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = "stop"     # 閒置時自動停止，節省費用
  auto_start_machines = true      # 收到請求時自動啟動
  min_machines_running = 0

[[vm]]
  size = "shared-cpu-1x"
  memory = "512mb"

[checks]
  [checks.health]
    type = "http"
    port = 8000
    path = "/health"
    interval = "30s"
    timeout = "5s"
```

**預估工作量**：修改約 5-8 個檔案，新增 2-3 個配置檔

---

### Phase 1：MCP 遠端存取（已完成 80%）

目前 MCP Server 已實作（`/mcp` endpoint），使用 `streamable_http_app()` transport。
部署到雲端後，遠端 AI 可直接連線。

#### 1.1 Claude Desktop/App 連線設定
- [ ] 文件化 MCP 連線配置

```json
// Claude Desktop: ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "ledgerone": {
      "type": "streamable-http",
      "url": "https://ledgerone-backend.fly.dev/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-token>"
      }
    }
  }
}
```

#### 1.2 確保 MCP 在生產環境正常運作
- [ ] 驗證 Bearer token 認證在 HTTPS 下正常
- [ ] 測試 Streamable HTTP transport 穿透 Fly.io proxy（Fly.io 有一級 MCP 支援）
- [ ] 設定適當的 timeout 和 auto-stop 策略

**預估工作量**：主要是配置和測試，少量程式碼修改

---

### Phase 2：ChatGPT / Gemini 整合（新開發）

#### 2.1 OpenAPI Schema for ChatGPT Custom GPT Actions
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
  - url: "https://ledgerone-backend.fly.dev/api/v1"
paths:
  /ledgers/{ledger_id}/transactions:
    post:
      summary: "建立交易記錄"
      operationId: "createTransaction"
      # ...
    get:
      summary: "查詢交易記錄"
      operationId: "listTransactions"
      # ...
  /ledgers/{ledger_id}/accounts:
    get:
      summary: "查詢帳戶列表"
      operationId: "listAccounts"
      # ...
```

#### 2.2 Google Gemini Extension
- [ ] 使用 Gemini Function Calling 對接 LedgerOne REST API
- [ ] 或透過 MCP Gateway（Gemini 已開始支援 MCP）
- [ ] 設定 Gemini Extension 的 function declarations

**預估工作量**：新增 1 個 OpenAPI spec 檔案，GPT prompt 文件，少量配置

---

### Phase 3：Messaging Bot 整合（新開發，中等工作量）

#### 3.1 共用 Bot 框架
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

#### 3.2 Telegram Bot
- [ ] 使用 `python-telegram-bot` 套件
- [ ] Webhook 模式（比 polling 更適合雲端部署）
- [ ] 掛載在 FastAPI：`POST /webhooks/telegram`
- [ ] 功能：文字記帳、語音記帳（Telegram 內建語音轉文字）、查餘額
- **費用**：免費（Telegram Bot API 完全免費）

```python
# backend/src/bots/telegram_bot.py
from fastapi import APIRouter
router = APIRouter(prefix="/webhooks/telegram")

@router.post("/")
async def telegram_webhook(update: dict):
    # 解析 Telegram message → 呼叫 BotMessageHandler
    ...
```

#### 3.3 Slack Bot
- [ ] 使用 `slack-bolt` 套件
- [ ] Slack Events API + Webhook
- [ ] 掛載在 FastAPI：`POST /webhooks/slack`
- [ ] 功能：Slash command `/expense`、DM 對話記帳、查詢
- **費用**：免費（Slack Free workspace）

#### 3.4 LINE Bot
- [ ] 使用 `line-bot-sdk` 套件
- [ ] Messaging API Webhook
- [ ] 掛載在 FastAPI：`POST /webhooks/line`
- [ ] 功能：文字記帳、查詢餘額、Rich Menu
- **費用**：免費（LINE Messaging API 免費方案 500 則/月）

#### 3.5 Bot API Routes 整合

```python
# backend/src/api/routes/__init__.py 新增
from src.bots.telegram_bot import router as telegram_router
from src.bots.slack_bot import router as slack_router
from src.bots.line_bot import router as line_router

app.include_router(telegram_router)
app.include_router(slack_router)
app.include_router(line_router)
```

**預估工作量**：新增約 10-15 個檔案，每個 Bot 約 2-3 個檔案

#### 3.6 優先順序建議

| 順序 | Bot | 理由 |
|------|-----|------|
| 1 | **Telegram** | 最容易開發、API 最友善、完全免費、支援語音 |
| 2 | **LINE** | 台灣使用率最高、API 文件完整 |
| 3 | **Slack** | 適合工作場景，但記帳較少在 Slack |

---

### Phase 4：Email 信用卡帳單自動匯入（新開發）

#### 4.1 Email 讀取模組
- [ ] 新建 `backend/src/services/email_service.py`
- [ ] 支援 Gmail API（OAuth2）或 IMAP 協定
- [ ] 定時排程（使用 APScheduler 或簡易 background task）
- [ ] Email 過濾規則（寄件者、主旨關鍵字）

```python
# backend/src/services/email_service.py
class EmailService:
    """讀取 Email 中的信用卡帳單"""

    async def fetch_credit_card_emails(self, user_id: str) -> list[Email]:
        """從 Gmail/IMAP 獲取信用卡帳單郵件"""
        # 過濾條件：
        # - 寄件者：各銀行 email domain
        # - 主旨：信用卡, 帳單, statement
        ...

    async def parse_statement(self, email: Email) -> list[Transaction]:
        """解析帳單內容為交易記錄"""
        # 使用 LLM 解析非結構化帳單
        ...
```

#### 4.2 帳單解析引擎
- [ ] 使用 LLM（Gemini/Claude）解析帳單 email 內容
- [ ] 支援 HTML email 解析
- [ ] 支援 PDF 附件帳單解析（需 `pymupdf` 或 `pdfplumber`）
- [ ] 交易明細結構化提取：日期、商家、金額、幣別
- [ ] 自動分類（利用現有的 category_suggester）

#### 4.3 帳單匯入流程
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

#### 4.4 Gmail OAuth2 整合
- [ ] Google Cloud Console 建立 OAuth2 credentials
- [ ] Frontend 新增 Gmail 授權頁面
- [ ] 安全儲存 refresh token（加密存 DB）
- **費用**：免費（Gmail API 免費額度足夠個人使用）

#### 4.5 支援的銀行帳單格式
- 台灣各大銀行信用卡帳單 email 格式
- 國際：Visa/Mastercard statement email
- 透過 LLM 做通用解析（不需為每家銀行寫 parser）

**預估工作量**：新增約 5-8 個檔案，較複雜的功能

---

## 四、需要新增的 Dependencies

### Backend (pyproject.toml)

```toml
# Production server
"gunicorn>=21.2.0",

# Bot integrations
"python-telegram-bot>=21.0",
"slack-bolt>=1.18.0",
"line-bot-sdk>=3.5.0",

# Email integration
"google-auth>=2.27.0",
"google-auth-oauthlib>=1.2.0",
"google-api-python-client>=2.114.0",
# 或 IMAP 方案（不需額外套件，Python 內建 imaplib）

# PDF parsing (for credit card statements)
"pdfplumber>=0.10.0",

# Background tasks
"apscheduler>=3.10.0",
```

---

## 五、環境變數新增

```env
# === Production ===
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres?sslmode=require
CORS_ORIGINS=https://ledgerone.vercel.app
FRONTEND_URL=https://ledgerone.vercel.app

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

## 六、實作優先順序與路線圖

```
Phase 0 ─── 雲端部署基礎（最高優先）
   │        • Backend → Fly.io (東京節點)
   │        • Frontend → Vercel
   │        • Database → Supabase
   │        • CI/CD pipeline
   │
Phase 1 ─── MCP 遠端連線（部署完即可用）
   │        • Claude Desktop/App 設定
   │        • 測試 MCP over HTTPS
   │
Phase 2 ─── ChatGPT & Gemini（低工作量，高價值）
   │        • OpenAPI spec for GPT Actions
   │        • Gemini function calling setup
   │
Phase 3 ─── Messaging Bots（中等工作量）
   │        • Telegram Bot (最先)
   │        • LINE Bot
   │        • Slack Bot
   │
Phase 4 ─── Email 帳單匯入（較高工作量）
            • Gmail OAuth2
            • LLM 帳單解析
            • 自動匯入流程
```

---

## 七、成本總結

### 推薦方案成本（Fly.io + Vercel + Supabase）

| 項目 | 平台 | 月費 |
|------|------|------|
| Frontend hosting | Vercel Hobby | $0 |
| Backend hosting | Fly.io (shared-cpu-1x, 512MB) | ~$3.57 |
| IPv4 (optional) | Fly.io | $2（可用 IPv6 免費） |
| PostgreSQL | Supabase Free (500MB) | $0 |
| Telegram Bot | Telegram API | $0 |
| LINE Bot | LINE Free (500 msg/月) | $0 |
| Slack Bot | Slack Free | $0 |
| Gmail API | Google Free Tier | $0 |
| LLM (Gemini) | Gemini Free Tier | $0 |
| **合計（有 IPv4）** | | **~$5.57/月** |
| **合計（純 IPv6）** | | **~$3.57/月** |

> 啟用 auto-stop 可進一步降低費用——閒置時不計費，可能降至 ~$1-2/月

### 方案限制與因應

| 限制 | 影響 | 因應措施 |
|------|------|----------|
| Fly.io auto-stop 冷啟動 | 閒置後首次請求慢 2-5 秒 | 可接受；或設 min_machines=1 保持 always-on |
| Supabase 7天未活動暫停 | DB 連不上 | 設定 cron ping 保持活躍 |
| Supabase 500MB | 大量交易可能不夠 | 個人記帳 5 年內通常 < 100MB |
| LINE 500 msg/月 | 大量使用會超 | 個人記帳通常 < 100 msg/月 |
| Vercel Hobby 禁止商業使用 | 未來商業化受限 | 遷移到 Cloudflare Workers ($5/月) |

### 如果需要進一步省錢

| 節省方式 | 效果 |
|----------|------|
| 啟用 auto-stop | 閒置不計費，月費可能 < $2 |
| 使用 IPv6 only | 省 $2/月 |
| Frontend 改 Cloudflare | 同為 $0，但建置較慢 |

---

## 八、安全性考量

1. **API Token**：所有外部存取都透過 Bearer Token，已實作
2. **HTTPS**：Vercel / Fly.io / Supabase 都自動提供 SSL
3. **Webhook 驗證**：各 Bot 平台都有 signature 驗證機制
4. **環境變數**：敏感資訊存在各平台的 Environment Variables（不進 Git）
5. **CORS**：僅允許 Frontend domain
6. **Rate Limiting**：建議新增 API rate limiting（防止濫用）
7. **Gmail OAuth2**：使用最小權限 scope（`gmail.readonly`）

---

## 九、部署步驟清單（Quick Start）

### Step 1: Supabase Database
```bash
# 1. 到 supabase.com 建立帳號與專案
# 2. 取得 Connection String (Settings → Database)
# 3. 記下 DATABASE_URL
```

### Step 2: Fly.io Backend
```bash
# 1. 安裝 flyctl CLI
curl -L https://fly.io/install.sh | sh

# 2. 登入 Fly.io
fly auth login

# 3. 從專案根目錄 launch（會自動偵測 Dockerfile）
fly launch --region nrt  # nrt = 東京

# 4. 設定環境變數（secrets）
fly secrets set DATABASE_URL="postgresql://..." \
  CORS_ORIGINS="https://ledgerone.vercel.app" \
  ENVIRONMENT="production" \
  LLM_PROVIDER="gemini" \
  GEMINI_API_KEY="..."

# 5. 部署
fly deploy
```

### Step 3: Vercel Frontend
```bash
# 1. 到 vercel.com 建立帳號
# 2. Import GitHub repo
# 3. Root Directory: frontend
# 4. Framework Preset: Next.js
# 5. 設定 NEXT_PUBLIC_API_URL = https://ledgerone-backend.fly.dev
```

### Step 4: 測試 MCP 連線
```bash
# Claude Desktop 設定
# 在 ~/.config/claude/claude_desktop_config.json 加入 MCP server
# 使用已建立的 API Token 連線
```

---

## 十、總結

### 核心發現

1. **已完成 80% 的基礎工作**：MCP Server、REST API、Token 認證都已實作
2. **部署到雲端後，Claude Desktop/App 立即可用**（Phase 0 + 1）
3. **ChatGPT/Gemini 整合工作量不大**，主要是 OpenAPI spec 和設定
4. **Bot 整合是最大工作量**，但可按需逐一開發
5. **Email 帳單匯入最複雜**，但 LLM 可大幅簡化解析邏輯

### 建議的第一步

先完成 **Phase 0（雲端部署）** 和 **Phase 1（MCP 遠端連線）**，這樣就能立即透過 Claude Desktop/App 用自然語言記帳。其餘功能可以根據實際使用需求逐步開發。
