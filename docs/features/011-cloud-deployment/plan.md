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
│  Email (IMAP) ──► Scheduled ─┘      ┌────────────────┐      │
│                   Parser            │ React+Vite SPA │      │
│                                     │ (Cloudflare    │      │
│                                     │  Pages)        │      │
│                                     └────────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、部署方案（$0/月 全免費）

> **詳細平台比較分析見 [research.md](./research.md)**

### 推薦方案：Render Free + Cloudflare Pages + Supabase

| 元件 | 平台 | 費用 | 說明 |
|------|------|------|------|
| **Frontend (SPA)** | **Cloudflare Pages** | **$0/月** | 純靜態檔案，無限 bandwidth，300+ edge 節點 |
| **Backend + MCP** | **Render Free** | **$0/月** | Docker 部署，cron ping 保持活躍 |
| **PostgreSQL** | **Supabase Free** | **$0/月** | 500MB 儲存，PostgreSQL 16，自動備份 |
| **總計** | | **$0/月** | |

### 為何選 Render Free + cron ping？

Render 免費方案的已知限制：
- 閒置 15 分鐘後 spin down，冷啟動 30-60 秒
- **只有 GET 能喚醒休眠服務**，POST 會被丟棄

**解法**：設定外部 cron job（如 UptimeRobot 免費方案）每 14 分鐘 GET `/health`，服務永不休眠。
服務不休眠 → POST 正常運作 → MCP、Bot Webhook 都沒問題。

| 限制 | cron ping 解決？ | 說明 |
|------|-----------------|------|
| POST 無法喚醒 | **解決** | 服務不休眠就不需要喚醒 |
| 冷啟動 30-60s | **解決** | 服務不休眠就不冷啟動 |
| 750 hr/月 | **剛好夠** | 一個月 744 小時 |
| 0.1 CPU / 512MB RAM | **夠用** | 個人使用負載低 |
| MCP SSE 穩定性 | **需實測** | 有社群回報 SSE 偶爾掛起 |

### 為何 Frontend 改用 Cloudflare Pages？

目前 Frontend 雖用 Next.js，但**實際上 97 個檔案都是 `'use client'`**，零 Server Actions、零 API Routes——本質上是一個包在 Next.js 殼裡的純 SPA。

個人記帳 app 不需要 SEO、不需要 SSR。**應遷移為 React + Vite SPA**：

| | Next.js（現狀） | React + Vite（目標） |
|--|-----------------|---------------------|
| SSR | 有，但不需要 | 無（不需要） |
| Bundle size | 較大（含 SSR runtime） | 更小（純 client） |
| 部署方式 | 需 Node.js server | **純靜態檔案** |
| 部署平台選擇 | Vercel / Node.js hosting | **任何靜態 hosting** |
| 建置速度 | 5-8 分鐘 | 更快（Vite） |
| 複雜度 | 過度（for SPA） | 剛好 |

遷移為純靜態 SPA 後，**Cloudflare Pages 就是最佳選擇**：

| | Vercel（部署 Next.js） | Cloudflare Pages（部署靜態 SPA） |
|--|----------------------|--------------------------------|
| 月費 | $0 | $0 |
| Bandwidth | 100 GB | **無限制** |
| 商業使用 | **禁止**（Hobby） | 允許 |
| Edge 節點 | ~100+ | **300+** |
| DDoS/WAF | 需付費 | **免費包含** |
| Next.js 相容問題 | 無 | **不適用**（純靜態不需要） |
| 建置限制 | 6000 min/月 | 500 builds/月 |

之前不推薦 Cloudflare 是因為 Next.js 在上面有很多相容性地雷。但既然要遷移成純靜態 SPA，**這些問題全部消失**。

### 備援方案

若 Render 的 MCP/SSE 連線在實測中不穩定：

| 項目 | 備援 | 月費 |
|------|------|------|
| Backend | 遷移到 Fly.io | ~$4-6/月 |
| 理由 | Fly.io 有 MCP 一級支援，冷啟動 2-5 秒 | |

### 各平台 Free Tier 限制

#### Cloudflare Pages (Frontend - 靜態 SPA)
- **無限 bandwidth**，每月 500 builds
- 300+ 全球 edge 節點
- 自動 HTTPS + 自訂域名
- 免費 DDoS 防護 + WAF
- 允許商業使用

#### Render Free (Backend)
- 750 hr/月，100GB bandwidth
- 0.1 CPU（shared），512MB RAM
- Docker & Git deploy，自動 HTTPS
- **需 cron ping 保持活躍**

#### Supabase Free (PostgreSQL)
- 500MB 資料庫儲存，2 個免費專案
- 自動每日備份（7 天保留）
- **限制**：7 天未活動會暫停（需 cron ping 保持活躍）

---

## 三、部署所需的開發工作

### Phase 0：Frontend 遷移 Next.js → React + Vite（前置工作）

目前 Frontend 使用 Next.js 15，但 97 個檔案都是 `'use client'`，零 Server Actions，本質上已是 SPA。需遷移為純 React + Vite 才能部署為靜態檔案。

#### 0.1 遷移範圍分析

| 類別 | 影響檔案數 | 替代方案 | 難度 |
|------|-----------|---------|------|
| 路由 (`next/link`, `useRouter`, `usePathname`, `useParams`) | ~19 檔 | React Router v7 | 低 |
| i18n (`next-intl`, `useTranslations`) | **~52 檔** | `react-i18next` + `i18next` | 中（量大但機械式替換） |
| 主題 (`next-themes`, `useTheme`) | 3 檔 | 自寫 ThemeProvider（localStorage + context） | 低 |
| 字體 (`next/font`) | 1 檔 | CSS `@import` Google Fonts | 極低 |
| Metadata (`generateMetadata`) | 3 檔 | 刪除（不需要 SEO） | 極低 |
| `'use client'` directive | 97 檔 | 全部刪除（Vite 全是 client） | 極低（batch find-replace） |
| Server Components (`getTranslations`) | 2 檔 | 改為 client-side i18n | 低 |
| Layouts (`layout.tsx`) | 2 檔 | React Router layout routes | 低 |

#### 0.2 遷移步驟

```
1. 初始化 Vite 專案
   └─ vite.config.ts, index.html, tsconfig

2. 安裝替代套件
   └─ react-router-dom, react-i18next, i18next

3. 路由遷移（~19 檔）
   ├─ next/link → <Link> from react-router-dom
   ├─ useRouter → useNavigate
   ├─ usePathname → useLocation
   ├─ useParams → useParams (same name, different import)
   └─ App Router file-based routes → 集中式 route 定義

4. i18n 遷移（~52 檔）
   ├─ useTranslations('ns') → useTranslation('ns')
   ├─ t('key') → t('key')  (API 幾乎相同)
   ├─ NextIntlClientProvider → I18nextProvider
   └─ 翻譯檔案格式不變（JSON）

5. 清理
   ├─ 刪除所有 'use client' directive
   ├─ 刪除 next.config.js, middleware.ts
   ├─ 刪除 generateMetadata exports
   └─ 更新 Dockerfile 為純靜態 build
```

#### 0.3 不需變動的部分（遷移優勢）

以下核心程式碼**完全不受影響**：
- 所有 React 元件邏輯和 UI
- TanStack Query（data fetching）
- Tailwind CSS 樣式
- Tremor / Recharts 圖表
- Radix UI 對話框
- Zod 驗證
- dnd-kit 拖拉
- 所有 `lib/`, `services/`, `types/` 目錄

#### 0.4 新增 Frontend Dependencies

```json
{
  "dependencies": {
    "react-router-dom": "^7.0.0",
    "react-i18next": "^14.0.0",
    "i18next": "^24.0.0",
    "i18next-browser-languagedetector": "^8.0.0"
  }
}
```

移除：`next`, `next-intl`, `next-themes`, `eslint-config-next`

---

### Phase 1：雲端部署基礎設施

#### 1.1 Backend 生產環境配置
- [ ] 新增 `ENVIRONMENT=production` 配置處理
- [ ] 設定 production CORS origins（Cloudflare Pages 域名）
- [ ] 啟用 production 模式下的 Alembic migration（啟動時自動 migrate）
- [ ] 新增 Gunicorn 作為 production WSGI server（取代 uvicorn --reload）
- [ ] 新增 `start.sh` 啟動腳本

```bash
# start.sh
#!/bin/bash
alembic upgrade head
gunicorn src.api.main:app -w 2 -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:${PORT:-8000}
```

#### 1.2 Frontend 靜態部署配置
- [ ] `vite build` 產生 `dist/` 靜態檔案
- [ ] 新增 `_redirects` 或 `_headers` file（SPA fallback routing）
- [ ] 設定 `VITE_API_URL` 環境變數指向 Render backend URL

```
# public/_redirects (Cloudflare Pages SPA routing)
/*  /index.html  200
```

#### 1.3 Database Migration 到 Supabase
- [ ] 在 Supabase 建立專案並取得連線字串
- [ ] 調整 `DATABASE_URL` 支援 Supabase 的 connection pooling (pgBouncer)
- [ ] 測試 Alembic migration 在 Supabase 上是否正常
- [ ] 設定 SSL mode (`?sslmode=require`)

#### 1.4 Cron Ping 設定（保持 Render 和 Supabase 活躍）
- [ ] 註冊 UptimeRobot 免費帳號（或 cron-job.org）
- [ ] 設定每 14 分鐘 GET ping Backend `/health`
- [ ] 設定每 5 天 ping Supabase（防止 7 天暫停）

#### 1.5 Render 配置

```yaml
# render.yaml
services:
  - type: web
    name: ledgerone-backend
    runtime: docker
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: DATABASE_URL
        sync: false
      - key: ENVIRONMENT
        value: production
      - key: CORS_ORIGINS
        sync: false
      - key: LLM_PROVIDER
        sync: false
    healthCheckPath: /health
```

#### 1.6 CI/CD Pipeline
- [ ] GitHub Actions 新增 deploy job
- [ ] Render auto-deploy from `main` branch
- [ ] Cloudflare Pages 連接 GitHub repo auto-deploy
- [ ] 新增 production environment secrets 管理

---

### Phase 2：MCP 遠端存取（已完成 80%）

MCP Server 已實作（`/mcp` endpoint），使用 `streamable_http_app()` transport。
部署到雲端後，遠端 AI 可直接連線。

#### 2.1 Claude Desktop/App 連線設定
- [ ] 文件化 MCP 連線配置

```json
// Claude Desktop: ~/.config/claude/claude_desktop_config.json
{
  "mcpServers": {
    "ledgerone": {
      "type": "streamable-http",
      "url": "https://ledgerone-backend.onrender.com/mcp",
      "headers": {
        "Authorization": "Bearer <your-api-token>"
      }
    }
  }
}
```

#### 2.2 確保 MCP 在生產環境正常運作
- [ ] 驗證 Bearer token 認證在 HTTPS 下正常
- [ ] 測試 Streamable HTTP transport 穿透 Render proxy
- [ ] 若 MCP/SSE 在 Render 上不穩定，遷移 Backend 到 Fly.io（備援方案）

---

### Phase 3：ChatGPT / Gemini 整合（新開發）

#### 3.1 OpenAPI Schema for ChatGPT Custom GPT Actions
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

#### 3.2 Google Gemini Extension
- [ ] 使用 Gemini Function Calling 對接 LedgerOne REST API
- [ ] 或透過 MCP Gateway（Gemini 已開始支援 MCP）
- [ ] 設定 Gemini Extension 的 function declarations

---

### Phase 4：Messaging Bot 整合（新開發，中等工作量）

#### 4.1 共用 Bot 框架
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

#### 4.2 Telegram Bot
- [ ] 使用 `python-telegram-bot` 套件
- [ ] Webhook 模式（比 polling 更適合雲端部署）
- [ ] 掛載在 FastAPI：`POST /webhooks/telegram`
- [ ] 功能：文字記帳、語音記帳（Telegram 內建語音轉文字）、查餘額
- **費用**：免費（Telegram Bot API 完全免費）

#### 4.3 LINE Bot
- [ ] 使用 `line-bot-sdk` 套件
- [ ] Messaging API Webhook
- [ ] 掛載在 FastAPI：`POST /webhooks/line`
- [ ] 功能：文字記帳、查詢餘額、Rich Menu
- **費用**：免費（LINE Messaging API 免費方案 500 則/月）

#### 4.4 Slack Bot
- [ ] 使用 `slack-bolt` 套件
- [ ] Slack Events API + Webhook
- [ ] 掛載在 FastAPI：`POST /webhooks/slack`
- [ ] 功能：Slash command `/expense`、DM 對話記帳、查詢
- **費用**：免費（Slack Free workspace）

#### 4.5 優先順序

| 順序 | Bot | 理由 |
|------|-----|------|
| 1 | **Telegram** | 最容易開發、API 最友善、完全免費、支援語音 |
| 2 | **LINE** | 台灣使用率最高、API 文件完整 |
| 3 | **Slack** | 適合工作場景，但記帳較少在 Slack |

---

### Phase 5：Email 信用卡帳單自動匯入（新開發）

#### 5.1 Email 讀取模組
- [ ] 新建 `backend/src/services/email_service.py`
- [ ] 支援 Gmail API（OAuth2）或 IMAP 協定
- [ ] 定時排程（使用 APScheduler 或簡易 background task）
- [ ] Email 過濾規則（寄件者、主旨關鍵字）

#### 5.2 帳單解析引擎
- [ ] 使用 LLM（Gemini/Claude）解析帳單 email 內容
- [ ] 支援 HTML email 解析
- [ ] 支援 PDF 附件帳單解析（需 `pdfplumber`）
- [ ] 交易明細結構化提取：日期、商家、金額、幣別
- [ ] 自動分類（利用現有的 category_suggester）

#### 5.3 帳單匯入流程
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

#### 5.4 Gmail OAuth2 整合
- [ ] Google Cloud Console 建立 OAuth2 credentials
- [ ] Frontend 新增 Gmail 授權頁面
- [ ] 安全儲存 refresh token（加密存 DB）
- **費用**：免費（Gmail API 免費額度足夠個人使用）

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

# PDF parsing (for credit card statements)
"pdfplumber>=0.10.0",

# Background tasks
"apscheduler>=3.10.0",
```

### Frontend (package.json) — 遷移後

```json
{
  "新增": {
    "react-router-dom": "^7.0.0",
    "react-i18next": "^14.0.0",
    "i18next": "^24.0.0",
    "i18next-browser-languagedetector": "^8.0.0"
  },
  "移除": {
    "next": "^15.0.0",
    "next-intl": "^4.7.0",
    "next-themes": "^0.4.6",
    "eslint-config-next": "^15.0.0"
  }
}
```

---

## 五、環境變數新增

```env
# === Production ===
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@db.supabase.co:5432/postgres?sslmode=require
CORS_ORIGINS=https://ledgerone.pages.dev
FRONTEND_URL=https://ledgerone.pages.dev

# === Frontend (build time) ===
VITE_API_URL=https://ledgerone-backend.onrender.com

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
Phase 0 ─── Frontend 遷移 Next.js → React + Vite
   │        • 路由遷移 (~19 檔)
   │        • i18n 遷移 (~52 檔)
   │        • 清理 Next.js 殘留
   │
Phase 1 ─── 雲端部署基礎
   │        • Backend → Render Free (+ cron ping)
   │        • Frontend → Cloudflare Pages
   │        • Database → Supabase Free
   │        • CI/CD pipeline
   │
Phase 2 ─── MCP 遠端連線（部署完即可用）
   │        • Claude Desktop/App 設定
   │        • 測試 MCP over HTTPS
   │        • 若不穩定 → Backend 遷 Fly.io
   │
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

## 七、成本總結

### $0/月 全免費方案

| 項目 | 平台 | 月費 |
|------|------|------|
| Frontend hosting | Cloudflare Pages Free | $0 |
| Backend hosting | Render Free (+ cron ping) | $0 |
| PostgreSQL | Supabase Free (500MB) | $0 |
| Cron ping 服務 | UptimeRobot Free | $0 |
| Telegram Bot | Telegram API | $0 |
| LINE Bot | LINE Free (500 msg/月) | $0 |
| Slack Bot | Slack Free | $0 |
| Gmail API | Google Free Tier | $0 |
| LLM (Gemini) | Gemini Free Tier | $0 |
| **合計** | | **$0/月** |

### 限制與因應

| 限制 | 影響 | 因應措施 |
|------|------|----------|
| Render 閒置 spin down | 15 分鐘無活動休眠 | UptimeRobot 每 14 分鐘 ping |
| Render 750 hr/月 | 連續運行剛好夠 | 一個月 744 小時，足夠 |
| Render MCP/SSE 穩定性 | 可能偶爾掛起 | 先實測，不穩定再遷 Fly.io (~$4/月) |
| Supabase 7 天未活動暫停 | DB 連不上 | cron ping 保持活躍 |
| Supabase 500MB | 大量交易可能不夠 | 個人記帳 5 年內通常 < 100MB |
| LINE 500 msg/月 | 大量使用會超 | 個人記帳通常 < 100 msg/月 |

---

## 八、安全性考量

1. **API Token**：所有外部存取都透過 Bearer Token，已實作
2. **HTTPS**：Cloudflare / Render / Supabase 都自動提供 SSL
3. **Webhook 驗證**：各 Bot 平台都有 signature 驗證機制
4. **環境變數**：敏感資訊存在各平台的 Environment Variables（不進 Git）
5. **CORS**：僅允許 Frontend domain
6. **Rate Limiting**：建議新增 API rate limiting（防止濫用）
7. **Gmail OAuth2**：使用最小權限 scope（`gmail.readonly`）
8. **Cloudflare WAF**：免費包含基本 Web Application Firewall

---

## 九、部署步驟清單（Quick Start）

### Step 1: Supabase Database
```bash
# 1. 到 supabase.com 建立帳號與專案
# 2. 取得 Connection String (Settings → Database)
# 3. 記下 DATABASE_URL
```

### Step 2: Render Backend
```bash
# 1. 到 render.com 建立帳號
# 2. New → Web Service → Connect GitHub repo
# 3. Root Directory: backend
# 4. Build Command: pip install .
# 5. Start Command: bash start.sh
# 6. 設定環境變數 (DATABASE_URL, CORS_ORIGINS, etc.)
```

### Step 3: Cloudflare Pages Frontend
```bash
# 1. 到 dash.cloudflare.com → Pages → Create
# 2. Connect GitHub repo
# 3. Build settings:
#    - Root Directory: frontend
#    - Build command: npm run build
#    - Output directory: dist
# 4. 設定 VITE_API_URL = https://ledgerone-backend.onrender.com
```

### Step 4: Cron Ping 設定
```bash
# 1. 到 uptimerobot.com 建立免費帳號
# 2. New Monitor → HTTP(s)
# 3. URL: https://ledgerone-backend.onrender.com/health
# 4. Monitoring Interval: 14 minutes (最短免費間隔可能為 5 分鐘)
```

### Step 5: 測試 MCP 連線
```bash
# Claude Desktop 設定
# 在 ~/.config/claude/claude_desktop_config.json 加入 MCP server
# 使用已建立的 API Token 連線
```

---

## 十、總結

### 核心決策

1. **Frontend 遷移 Next.js → React + Vite**：97 個 `'use client'` 檔案證明不需要 SSR，個人記帳不需要 SEO。遷移後可部署為純靜態檔案，解鎖免費靜態 hosting
2. **Backend 選 Render Free + cron ping**：$0/月，cron ping 解決 POST 喚醒和冷啟動問題。MCP/SSE 穩定性需實測，Fly.io (~$4/月) 作為備援
3. **Frontend 選 Cloudflare Pages**：純靜態 SPA 不存在 Next.js 相容性問題，無限 bandwidth，免費 DDoS/WAF

### 建議的第一步

1. 先完成 **Phase 0（Frontend 遷移）**——移除 Next.js，改為 React + Vite SPA
2. 再做 **Phase 1（雲端部署）** + **Phase 2（MCP 連線）**
3. 部署完畢後就能透過 Claude Desktop/App 用自然語言記帳
4. 其餘功能根據實際需求逐步開發
