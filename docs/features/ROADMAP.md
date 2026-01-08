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

---

## Planned Features

### 003-settings-account-management

**Priority: High**

Settings 頁面與科目管理功能。

**Scope:**

- [ ] Settings 入口（Sidebar menu 增加 Settings）
- [ ] 科目管理頁面
  - [ ] 新增科目（支援父子關係）
  - [ ] 編輯科目名稱
  - [ ] 刪除科目（檢查是否有交易）
  - [ ] 科目排序（拖拉排序）
- [ ] 科目樹狀結構改進
  - [ ] 支援 3 層結構（如：存款.LineBank.外幣帳戶）
  - [ ] MyAB 格式解析（A-代墊應收帳款.借別人錢）
- [ ] i18n 語言切換設定
- [ ] Dark/Light mode 切換

**Reference:** MyAB spec 1.4 自訂科目

---

### 004-transaction-entry

**Priority: High**

科目頁面新增交易功能。

**Scope:**

- [ ] 科目頁面增加「新增交易」按鈕
- [ ] 交易表單（From/To 帳戶選擇）
- [ ] 日期選擇器
- [ ] 金額輸入（支援計算：50+40=90）
- [ ] 明細/備註欄位
- [ ] 快速入帳模板
  - [ ] 儲存常用交易樣本
  - [ ] 套用模板快速記帳

**Reference:** MyAB spec 2.1, 2.2

---

### 005-ui-navigation-v2

**Priority: High**

UI 導航改進。

**Scope:**

- [ ] Sidebar menu 調整
  - [ ] 「回到帳本清單」移到最上方
  - [ ] 新增 Settings 入口
  - [ ] 新增批次匯入入口
- [ ] Top bar 改進
  - [ ] 帳本選擇器（右上角）
  - [ ] 設定選單（i18n、主題切換）
- [ ] Dashboard 卡片改進
  - [ ] 第一行：總資產、總負債、當月收入、當月支出
  - [ ] 總資產圖表：數值 + 一年趨勢折線圖
  - [ ] Income vs Expense：每月長條圖

---

### 006-data-import

**Priority: Medium**

資料匯入功能。

**Scope:**

- [ ] 批次匯入入口（Menu）
- [ ] MyAB CSV 匯入
  - [ ] 解析 MyAB 匯出格式
  - [ ] 科目自動對應/建立
  - [ ] 預覽匯入資料
  - [ ] 確認匯入
- [ ] 信用卡帳單匯入
  - [ ] 支援常見銀行 CSV/PDF 格式
  - [ ] 自動分類支出科目
- [ ] 對話式匯入（AI）- Future
  - [ ] 自然語言輸入
  - [ ] AI 解析並產生交易

**Reference:** MyAB spec 5.3

---

### 007-data-export

**Priority: Medium**

資料匯出功能。

**Scope:**

- [ ] 匯出入口
- [ ] CSV 匯出（完整格式，可再匯入）
- [ ] HTML 匯出（列印用）
- [ ] 按科目匯出
- [ ] 按日期範圍匯出

**Reference:** MyAB spec 5.2

---

### 008-reports

**Priority: Medium**

報表與分析功能。

**Scope:**

- [ ] 資產負債表 (Balance Sheet)
  - [ ] 資產小計
  - [ ] 負債小計
  - [ ] 淨資產計算
- [ ] 損益表 (Income Statement)
  - [ ] 收入小計
  - [ ] 支出小計
  - [ ] 淨收益計算
- [ ] 期間選擇器
- [ ] 匯出報表

**Reference:** MyAB spec 4.1

---

### 009-advanced-transactions

**Priority: Low**

進階交易功能。

**Scope:**

- [ ] 分期付款記錄
  - [ ] 輸入單期金額 + 期數
  - [ ] 一次產生多筆交易
- [ ] 定期記錄
  - [ ] 設定週期（每日/週/月/年）
  - [ ] 自動產生交易
  - [ ] 逾期補登提示
- [ ] 標記功能
  - [ ] 交易標記（待對帳、可報稅等）
  - [ ] 按標記篩選

**Reference:** MyAB spec 3.1, 3.2, 3.3

---

### 010-budget

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

### 011-backup-sync

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
            ├── 003-settings-account-management
            │       └── 005-ui-navigation-v2
            ├── 004-transaction-entry
            ├── 006-data-import
            ├── 007-data-export
            └── 008-reports
                    ├── 009-advanced-transactions
                    └── 010-budget
```

---

## Suggested Implementation Order

**Phase 1 - Core Enhancements (High Priority)**

1. 003-settings-account-management
2. 004-transaction-entry
3. 005-ui-navigation-v2

**Phase 2 - Data Management (Medium Priority)** 4. 006-data-import 5. 007-data-export 6. 008-reports

**Phase 3 - Advanced Features (Low Priority)** 7. 009-advanced-transactions 8. 010-budget 9. 011-backup-sync
