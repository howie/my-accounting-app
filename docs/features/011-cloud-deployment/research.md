# 平台比較分析：Backend (Render vs Fly.io) & Frontend (Vercel vs Cloudflare)

## 一、Backend 比較：Render vs Fly.io

### 1. Free Tier 比較

| 項目                | Render                           | Fly.io                 |
| ------------------- | -------------------------------- | ---------------------- |
| **免費方案**        | 有（750 hr/月, 100GB bandwidth） | **新用戶已無免費方案** |
| **需信用卡**        | 不需要                           | 需要                   |
| **商業使用**        | 允許                             | 允許                   |
| **最低月費**        | $0                               | ~$2-4（Pay As You Go） |
| **免費 PostgreSQL** | 1GB，但 **30 天後過期**          | 無                     |

> **重大發現**：Fly.io 已於 2024 年取消 Hobby plan，新用戶無免費方案。所有用量皆需付費。

### 2. Cold Start & 效能

| 項目              | Render                               | Fly.io                            |
| ----------------- | ------------------------------------ | --------------------------------- |
| **Free 閒置行為** | 15 分鐘無活動後 spin down            | 可自行控制 auto-stop              |
| **冷啟動時間**    | **30-60 秒**                         | **2-5 秒**（Firecracker microVM） |
| **POST 喚醒問題** | **只有 GET 能喚醒**，POST 可能被丟棄 | 無此問題                          |
| **Always-on**     | $7/月（Starter）                     | ~$2-4/月（shared VM 24/7）        |

> **關鍵問題**：Render 免費方案 POST 請求無法喚醒休眠服務——這對 MCP、Webhook Bot 等純 POST 的 API 來說是致命問題。

### 3. MCP / SSE / Streamable HTTP 支援

| 項目                | Render                     | Fly.io                                         |
| ------------------- | -------------------------- | ---------------------------------------------- |
| **WebSocket**       | 完整支援，無連線時間限制   | 完整支援                                       |
| **SSE**             | 可用，但有回報連線掛起問題 | 完整支援                                       |
| **MCP Transport**   | 無專門文件                 | **有 MCP 官方文件**，內建 `fly mcp server` CLI |
| **Streamable HTTP** | 未特別測試/文件化          | 開箱即用                                       |

> Fly.io 對 MCP 有**一級支援**（first-class support），這是本專案的核心需求。

### 4. Docker 部署體驗

| 項目                       | Render                          | Fly.io                      |
| -------------------------- | ------------------------------- | --------------------------- |
| **部署方式**               | Git push auto-detect Dockerfile | `fly launch` CLI + fly.toml |
| **操作介面**               | **Web UI 為主**，適合新手       | **CLI 為主**，學習曲線較高  |
| **render.yaml / fly.toml** | Infrastructure as Code 支援     | Infrastructure as Code 支援 |
| **Private Registry**       | 需 Teams plan                   | 支援                        |

### 5. PostgreSQL 方案

| 項目             | Render              | Fly.io                                     |
| ---------------- | ------------------- | ------------------------------------------ |
| **免費方案**     | 1GB，30 天後過期    | 無免費方案                                 |
| **最低付費**     | ~$7/月（managed）   | $38/月（managed）或 ~$2/月（self-managed） |
| **Self-managed** | 不提供              | 自行在 Fly Machine 跑 Postgres             |
| **建議**         | 不使用（30 天過期） | 不使用（貴或需自行維護）                   |

> **結論**：兩者的 PostgreSQL 都不理想。**一律使用 Supabase 或 Neon 作為免費外部 DB**。

### 6. 區域覆蓋

| 項目             | Render                                            | Fly.io                           |
| ---------------- | ------------------------------------------------- | -------------------------------- |
| **區域數**       | 5（Oregon, Ohio, Virginia, Frankfurt, Singapore） | **18+**（含東京、新加坡等）      |
| **亞洲節點**     | Singapore                                         | Tokyo, Singapore, Mumbai, Sydney |
| **Multi-region** | 不支援跨區域私有網路                              | 核心功能，Anycast routing        |

> 台灣使用者：Fly.io 的東京節點延遲約 30-50ms，Render Singapore 約 50-70ms。

### 7. 價格比較（超出免費後）

| 方案               | Render                  | Fly.io                         |
| ------------------ | ----------------------- | ------------------------------ |
| **最小 Always-on** | $7/月（0.5 CPU, 512MB） | **~$3.57/月**（shared, 512MB） |
| **標準**           | $25/月（1 CPU, 2GB）    | ~$5.84/月（shared, 1GB）       |
| **IPv4**           | 包含                    | **$2/月/app**                  |
| **Bandwidth 超量** | $30/100GB               | $0.02/GB                       |

### 8. 重要地雷

#### Render

- POST 無法喚醒休眠服務（對 MCP/Bot webhook 致命）
- 免費 DB 只有 30 天
- Ephemeral filesystem（檔案不持久化）
- 無靜態出站 IP

#### Fly.io

- 新用戶無免費方案
- Dedicated IPv4 每個 app $2/月
- Volume 即使停止也收費（$0.15/GB/月）
- 預設 256MB RAM，容易 OOM
- 2025/2 曾發生 IAD 資料中心重大故障

---

### Backend 結論

| 情境                    | 推薦                | 理由                                   |
| ----------------------- | ------------------- | -------------------------------------- |
| **純免費、測試用**      | Render              | 唯一有免費方案，但 POST 喚醒問題嚴重   |
| **MCP 為核心需求**      | **Fly.io**          | 一級 MCP 支援、快速冷啟動、POST 無問題 |
| **最低成本 production** | **Fly.io ~$4-6/月** | shared VM + 外部免費 DB                |
| **簡單好管理**          | Render $7/月        | Web UI 操作直覺，zero config           |

**最終推薦：Fly.io**

理由：

1. 本專案核心需求是 **MCP Streamable HTTP**——Fly.io 有一級支援
2. Render 免費方案的 **POST 無法喚醒**問題，對 MCP 和 Bot webhook 是致命缺陷
3. Fly.io 冷啟動 2-5 秒 vs Render 30-60 秒
4. 東京節點對台灣延遲更低
5. 月費 ~$4-6 仍非常便宜

---

## 二、Frontend 比較：Vercel vs Cloudflare

### 重要前提

Cloudflare Pages 已於 2025 年 4 月 deprecated，正在合併進 Workers。新專案應使用
**Cloudflare Workers + `@opennextjs/cloudflare`** 部署 Next.js。

### 1. Free Tier 比較

| 項目                  | Vercel Hobby                  | Cloudflare Workers Free       |
| --------------------- | ----------------------------- | ----------------------------- |
| **Bandwidth**         | 100 GB/月                     | **無限制（無出流量費）**      |
| **Function 請求**     | 150,000/月                    | **100,000/天**（~3M/月）      |
| **Build 額度**        | 6,000 分鐘/月                 | 500 builds/月                 |
| **Commercial use**    | **禁止**（需升級 Pro $20/月） | 允許                          |
| **Team members**      | 僅個人                        | 無限制                        |
| **Worker size**       | N/A                           | 3 MiB（免費）/ 10 MiB（付費） |
| **Function duration** | 60 秒 wall-clock              | 10ms CPU time                 |

> **關鍵差異**：Vercel Hobby 禁止商業使用。若有任何營利行為需升級 Pro（$20/月）。Cloudflare 無此限制。

### 2. Next.js 相容性

| 功能               | Vercel                   | Cloudflare (@opennextjs)        |
| ------------------ | ------------------------ | ------------------------------- |
| **App Router**     | 完整（原生）             | 支援                            |
| **SSR**            | 完整，含 Streaming       | 支援（Node.js runtime）         |
| **ISR**            | 完整（revalidateTag 等） | 支援（Workers 上運作）          |
| **Middleware**     | 完整                     | 支援，但**不支援 Edge runtime** |
| **Server Actions** | 完整                     | 支援                            |
| **PPR**            | 支援                     | 支援                            |
| **Turbopack**      | 支援                     | **不支援**（build 會壞）        |
| **`use cache`**    | 支援                     | **尚未支援**                    |
| **React 19**       | 支援                     | 支援                            |
| **設定難度**       | Zero config              | 需 OpenNext adapter 配置        |

### 3. 效能與 CDN

| 項目            | Vercel                               | Cloudflare                 |
| --------------- | ------------------------------------ | -------------------------- |
| **Edge 節點數** | ~100+                                | **300+**                   |
| **HTTP/3**      | 不支援                               | 支援                       |
| **DDoS 防護**   | 基本                                 | **企業級（免費）**         |
| **WAF**         | 需付費                               | **免費包含**               |
| **SSR latency** | 較好（Fluid Compute + 資料庫同區域） | 全球邊緣，但 DB-heavy 較慢 |
| **靜態內容**    | 好                                   | **更好（更多 PoP）**       |

### 4. 建置速度

| 項目               | Vercel              | Cloudflare                   |
| ------------------ | ------------------- | ---------------------------- |
| **增量建置**       | ~3 分鐘（有 cache） | **~15 分鐘**（cache 效果差） |
| **首次建置**       | ~5-8 分鐘           | ~15-20 分鐘                  |
| **Turbopack 加速** | 支援                | 不支援（會導致錯誤）         |

> Cloudflare 缺乏有效的 build cache，每次幾乎從頭建置。

### 5. 超出免費後的價格

| 方案           | Vercel                     | Cloudflare                |
| -------------- | -------------------------- | ------------------------- |
| **入門付費**   | $20/user/月（Pro）         | **$5/月（Paid Workers）** |
| **Bandwidth**  | 1 TB（Pro），超量 $0.15/GB | **無限制，無出流量費**    |
| **Functions**  | 含 Pro 額度                | 10M requests/月           |
| **規模化成本** | 高（可能暴增）             | **極低且可預測**          |

### 6. Cloudflare 部署 Next.js 的已知地雷

1. **Turbopack 不能用** — `next build --turbo` 會導致部署後 500 error
2. **Edge runtime 不支援** — 必須移除所有 `export const runtime = 'edge'`
3. **Worker size 限制** — 免費 3MiB，大型 Next.js 很容易超過
4. **DB 連線限制** — 不能用全域連線池，需在 request context 內建立
5. **Image optimization 需額外設定** — 需要 Cloudflare Images binding
6. **Build cache 差** — 每次都是完整建置，慢
7. **`nodejs_compat` flag 必須啟用**
8. **Next.js 15.3+ 有 instrumentation hook 的已知 bug**

### 7. 開發體驗

| 項目                    | Vercel                   | Cloudflare                      |
| ----------------------- | ------------------------ | ------------------------------- |
| **Setup 複雜度**        | Git push 即部署          | 需設定 wrangler.toml + OpenNext |
| **Preview deployments** | 自動，1-click            | 需設定                          |
| **環境變數管理**        | 精緻 UI + CLI            | wrangler CLI 為主               |
| **Debug 體驗**          | 好（error overlay 整合） | 一般（需查 worker logs）        |
| **學習曲線**            | 極低                     | 中等                            |

---

### Frontend 結論

| 情境                   | 推薦           | 理由                             |
| ---------------------- | -------------- | -------------------------------- |
| **快速上線、最省事**   | **Vercel**     | Zero config，Next.js 原生支援    |
| **長期省錢、規模化**   | **Cloudflare** | $5/月 vs $20/月，無 bandwidth 費 |
| **需要 DDoS/WAF 防護** | **Cloudflare** | 企業級安全免費包含               |
| **重視建置速度**       | **Vercel**     | 3 min vs 15 min                  |
| **商業使用但不想付費** | **Cloudflare** | Vercel Hobby 禁止商業使用        |

---

## 三、最終推薦方案

### 方案 A：最低成本 Production（推薦）

| 元件         | 平台          | 月費         | 理由                   |
| ------------ | ------------- | ------------ | ---------------------- |
| **Backend**  | Fly.io        | ~$4-6        | MCP 一級支援，快冷啟動 |
| **Frontend** | Vercel Hobby  | $0           | 最佳 Next.js 體驗      |
| **Database** | Supabase Free | $0           | 500MB 免費 PostgreSQL  |
| **合計**     |               | **~$4-6/月** |                        |

適合：個人使用、快速上線、MCP 為核心需求

### 方案 B：完全免費（有妥協）

| 元件         | 平台            | 月費      | 理由              |
| ------------ | --------------- | --------- | ----------------- |
| **Backend**  | Render Free     | $0        | 唯一免費選項      |
| **Frontend** | Cloudflare Free | $0        | 無 bandwidth 限制 |
| **Database** | Supabase Free   | $0        | 500MB 免費        |
| **合計**     |                 | **$0/月** |                   |

妥協：Render 冷啟動慢 + POST 不喚醒，Cloudflare 建置慢 + Next.js 地雷多

### 方案 C：穩定 + 省錢（最佳平衡）

| 元件         | 平台                  | 月費          | 理由                      |
| ------------ | --------------------- | ------------- | ------------------------- |
| **Backend**  | Fly.io                | ~$4-6         | MCP 支援 + 東京節點       |
| **Frontend** | Cloudflare Workers $5 | $5            | 無限 bandwidth + 商業可用 |
| **Database** | Supabase Free         | $0            | 500MB 免費                |
| **合計**     |                       | **~$9-11/月** |                           |

適合：長期運行、有商業化可能、需安全防護

### 方案 D：最簡運維

| 元件         | 平台          | 月費           | 理由             |
| ------------ | ------------- | -------------- | ---------------- |
| **Backend**  | Fly.io        | ~$4-6          | MCP + 效能       |
| **Frontend** | Vercel Pro    | $20            | 零配置 + 最佳 DX |
| **Database** | Supabase Free | $0             |                  |
| **合計**     |               | **~$24-26/月** |                  |

適合：重視開發效率、不想處理相容性問題

---

## 四、我的建議

**選方案 A（Fly.io + Vercel Hobby + Supabase Free）**

理由：

1. **$4-6/月**——一杯咖啡的錢，換來穩定的 MCP 服務
2. Vercel Hobby 免費且 Next.js 零配置，個人記帳 app 不涉及商業使用的限制
3. Fly.io 東京節點對台灣延遲最低，MCP Streamable HTTP 有一級支援
4. Supabase 500MB 對個人記帳足夠用數年
5. 若未來需要商業化，Frontend 再遷移到 Cloudflare Workers（$5/月）即可
