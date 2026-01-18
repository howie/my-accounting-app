# Feature Roadmap

## Completed Features

### 001-core-accounting (DONE)

- Ledger CRUD
- Account CRUD with 4 types (Asset, Liability, Income, Expense)
- Transaction CRUD (Expense, Income, Transfer)
- Double-entry bookkeeping

### 002-ui-layout-dashboard (DONE)

- Sidebar navigation with hierarchical account tree
- Dashboard with total assets card
- Income vs Expenses chart
- Monthly trends chart
- Account transaction list with pagination
- Mobile responsive hamburger menu
- i18n support (zh-TW, en)

### 003-settings-account-management (DONE)

- Settings 入口（Sidebar menu 增加 Settings）
- 科目管理頁面
  - 新增科目（支援父子關係）
  - 編輯科目名稱
  - 刪除科目（含交易重新指派流程）
  - 科目排序（拖拉排序）
- 科目樹狀結構改進
  - 支援 3 層結構
  - 可收合的科目樹與聚合餘額顯示
- i18n 語言切換設定（zh-TW, en）
- Dark/Light mode 切換
- Audit trail 記錄所有科目變更

### 004-transaction-entry (DONE)

- 科目頁面「新增交易」按鈕與 Modal 表單
- From/To 帳戶階層式選擇器
- 日期選擇器（預設今天）
- 金額輸入（支援計算式：50+40=90）
- 描述（必填）與備註（選填）欄位
- 快速入帳模板
  - 儲存常用交易樣本（最多 50 個）
  - 套用模板快速記帳
  - 模板編輯與刪除
- Dashboard QuickEntryPanel 整合
- i18n 支援（zh-TW, en）
- Dark/Light mode 支援

### 005-ui-navigation-v2 (DONE)

- Sidebar menu 調整
  - 「回到帳本清單」移到最上方
  - 新增 Settings 入口
  - 新增批次匯入入口（已在 006 實作）
  - 可收合的 Sidebar（Icon-only mode）
  - 最近瀏覽科目（Recent Accounts）
- Top bar 改進
  - 帳本選擇器（右上角）
  - 設定選單（i18n、主題切換）
  - 麵包屑導覽（Breadcrumbs）
- Dashboard 卡片改進
  - 第一行：總資產、總負債、當月收入、當月支出
  - 總資產圖表：數值 + 一年趨勢折線圖 (Deferred)
  - Income vs Expense：每月長條圖
- 快速搜尋（Command Palette）
  - Cmd/Ctrl+K 開啟搜尋
  - 搜尋科目與頁面
  - 鍵盤導覽結果
- 鍵盤快捷鍵
  - g+d 前往 Dashboard
  - g+s 前往 Settings
  - ? 顯示快捷鍵說明 (Added in Command Palette footer)

### 006-data-import (DONE)

- 批次匯入入口（Menu）
- MyAB CSV 匯入
  - 解析 MyAB 匯出格式
  - 科目自動對應/建立
  - 預覽匯入資料
  - 確認匯入
- 信用卡帳單匯入（Future）
- 對話式匯入（AI）- Future

### 007-api-for-mcp (DONE)

- MCP 基礎建設
  - FastMCP 伺服器設定
  - Bearer Token 認證
  - API Token 管理（建立、撤銷、列表）
- MCP 工具
  - create_transaction - 建立交易（支援科目模糊比對）
  - list_accounts - 列出科目（支援類型篩選、餘額篩選）
  - get_account - 查詢單一科目餘額與近期交易
  - list_transactions - 查詢交易紀錄（分頁、日期篩選）
  - list_ledgers - 列出帳本
- 前端 Token 管理 UI
  - Settings → API Tokens 頁面
  - 建立新 Token
  - 撤銷 Token
  - i18n 支援（zh-TW, en）

### 008-data-export (DONE)

- 匯出入口
- CSV 匯出（完整格式，可再匯入）
- HTML 匯出（列印用）
- 按科目匯出
- 按日期範圍匯出

### 009-reports (DONE)

- 資產負債表 (Balance Sheet)
  - 資產小計、負債小計、淨資產計算
- 損益表 (Income Statement)
  - 收入小計、支出小計、淨收益計算
- 期間選擇器（支援自定義日期範圍）
- 匯出報表（CSV, HTML）
- 視覺化圖表（資產結構、收支趨勢）

---

## Planned Features

### 010-advanced-transactions (IN PROGRESS)

**Priority: High**

進階交易功能。

**Scope:**

- [x] Backend API & Logic (DONE)
- [x] Tags CRUD & Filtering (Backend)
- [x] Recurring Transactions (Backend)
- [x] Installment Plans (Backend)
- [x] Frontend API Client (DONE)
- [ ] Frontend UI (Pending)
  - [x] Tag Management UI
  - [x] Recurring Settings UI
  - [ ] Installment UI

**Reference:** MyAB spec 3.1, 3.2, 3.3

### 003-1-ci-agent-autofix

**Priority: Medium**

CI 流程自動修復工具。

**Scope:**

- [ ] 自動修復 Lint 錯誤
- [ ] 自動修復型別錯誤
- [ ] 測試失敗分析與建議

---

### 011-budget

**Priority: Low**

預算功能。

**Scope:**

- [ ] 預算設定頁面
- [ ] 按科目設定預算
- [ ] 月度/年度預算
- [ ] 預算警告提示
- [ ] 預算執行報表

**Reference:** MyAB spec 3.5

---

### 012-backup-sync

**Priority: Low**

備份與同步功能。

**Scope:**

- [ ] 手動備份/還原
- [ ] 自動備份設定
- [ ] 雲端同步（未來）

**Reference:** MyAB spec 5.1, 5.4

---

## Feature Dependencies

```
001-core-accounting (DONE)
    └── 002-ui-layout-dashboard (DONE)
            ├── 003-settings-account-management (DONE)
            │       └── 005-ui-navigation-v2 (DONE)
            ├── 004-transaction-entry (DONE)
            ├── 006-data-import (DONE)
            ├── 007-api-for-mcp (DONE)
            ├── 008-data-export (DONE)
            └── 009-reports (DONE)
                    ├── 010-advanced-transactions
                    └── 011-budget
```

---

## Suggested Implementation Order

**Phase 1 - Core Enhancements (High Priority)**

1. ~~003-settings-account-management~~ ✅ DONE
2. ~~004-transaction-entry~~ ✅ DONE
3. ~~005-ui-navigation-v2~~ ✅ DONE

**Phase 2 - Data Management & Reporting (Medium Priority)**

4. ~~006-data-import~~ ✅ DONE (MyAB CSV 完成)
5. ~~007-api-for-mcp~~ ✅ DONE (MCP API + Token 管理 UI)
6. ~~008-data-export~~ ✅ DONE (CSV/HTML 匯出)
7. ~~009-reports~~ ✅ DONE (Balance Sheet, Income Statement)

**Phase 3 - Advanced Features & Automation (Low Priority)**

8. 010-advanced-transactions (In Progress: Frontend UI Pending)
9. 003-1-ci-agent-autofix (Planned)
10. 011-budget
11. 012-backup-sync
