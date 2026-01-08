# Feature Specification: LedgerOne - Core Accounting System

**Feature Branch**: `001-core-accounting`
**Created**: 2025-11-20
**Updated**: 2026-01-02
**Status**: Draft

## Project Vision

打造一個「隱私優先」、「數據主權在己」的個人財務管理系統。目標是超越傳統記帳軟體（僅記錄流水帳），轉向資產管理視角（關注淨值成長與資產配置）。

本 Feature 專注於**核心記帳功能**，採用雙重記帳邏輯確保財務數據完整性。

## System Architecture

採用**前後端分離 (Separation of Concerns)** 架構，結合 Next.js 的 UI 渲染能力與 Python 的數據處理強項。

### Tech Stack

**Frontend (UI/UX):**

- **Framework:** Next.js 15 (App Router) - SSR 渲染、路由
- **Language:** TypeScript
- **Styling:** Tailwind CSS + ShadcnUI (元件庫) + Tremor (圖表庫)
- **Desktop Wrapper:** Tauri (將 Web App 包裝為原生 Mac App)

**Backend (Core Logic):**

- **Framework:** Python FastAPI
- **Data Processing:** Pandas, NumPy
- **ORM:** SQLModel

**Database (Storage):**

- **Core:** PostgreSQL (Supabase 或 Local Docker)

## Clarifications

### Session 2025-11-20

- Q: How do users specify account type when creating accounts? → A: Users select account type from dropdown (Asset/Liability/Income/Expense)
- Q: What happens when account balance would become negative? → A: Allow negative balances for Asset/Liability accounts but display warning indicator
- Q: What decimal precision should the system support? → A: Support exactly 2 decimal places with banker's rounding

### Session 2025-11-22

- Q: Should zero-amount transactions be blocked or allowed? → A: Allowed with warning confirmation before saving
- Q: How should the transaction list handle large datasets? → A: Implement virtual scrolling for UI responsiveness
- Q: How should the system handle unbalanced transactions? → A: Block saving entirely until balanced

### Session 2026-01-02

- Q: Architecture decision? → A: Next.js frontend + Python FastAPI backend + PostgreSQL
- Q: Keep double-entry bookkeeping? → A: Yes, maintain strict double-entry validation
- Q: Dashboard, AI import, PWA scope? → A: Split into separate features (002, 003, etc.)

## User Scenarios & Testing

### User Story 1 - Create Ledger and Chart of Accounts (Priority: P1)

使用者需要建立帳本並設定科目表來開始追蹤個人財務。

**Why this priority**: 這是基礎功能 - 沒有帳本和科目，無法進行任何財務追蹤。

**Acceptance Scenarios**:

1. **Given** 新使用者開啟應用程式，**When** 建立名為 "2024 Personal" 的帳本並設定初始現金 10,000，**Then** 系統建立帳本，Cash 帳戶顯示餘額 10,000
2. **Given** 帳本存在，**When** 使用者新增 "Bank Account" 並選擇類型 Asset，**Then** 系統建立帳戶並顯示在帳戶列表
3. **Given** 帳本有預設的 Cash 和 Equity 帳戶，**When** 使用者嘗試刪除這些帳戶，**Then** 系統阻止刪除並顯示錯誤訊息
4. **Given** 使用者建立不同類型的帳戶，**When** 檢視帳戶列表，**Then** 帳戶依類型分類顯示（Asset/Liability/Income/Expense）

---

### User Story 2 - Record Transactions with Double-Entry (Priority: P1)

使用者需要記錄日常財務交易，包括支出、收入和帳戶間轉帳。

**Why this priority**: 記錄交易是記帳軟體的核心目的。

**Acceptance Scenarios**:

1. **Given** Cash 帳戶有 10,000 餘額，**When** 使用者記錄支出 50 從 Cash 到 "Food" (Expense)，**Then** Cash 餘額減少至 9,950，Food 支出顯示 50
2. **Given** 使用者記錄收入 30,000 從 "Salary" (Income) 到 "Bank Account"，**When** 檢視帳戶餘額，**Then** Bank Account 增加 30,000，Salary 顯示 30,000
3. **Given** 使用者有 Cash 5,000 和 Bank 10,000，**When** 轉帳 2,000 從 Cash 到 Bank，**Then** Cash 顯示 3,000，Bank 顯示 12,000（淨資產不變）
4. **Given** 使用者嘗試建立借貸不平衡的交易，**When** 點擊儲存，**Then** 系統阻止儲存並提示錯誤
5. **Given** Cash 帳戶有 100 餘額，**When** 使用者記錄支出 150，**Then** Cash 餘額變為 -50 並顯示警告指示

---

### User Story 3 - View Balances and Transaction History (Priority: P2)

使用者需要查看帳戶餘額和交易歷史以了解財務狀況。

**Why this priority**: 雖然必要，但可在基本記錄功能之後實作。

**Acceptance Scenarios**:

1. **Given** 已記錄多筆交易，**When** 使用者檢視帳戶列表，**Then** 每個帳戶顯示根據所有交易計算的當前餘額
2. **Given** 存在 50 筆交易，**When** 使用者搜尋 "lunch"，**Then** 系統只顯示描述中包含 "lunch" 的交易
3. **Given** 交易跨越 3 個月，**When** 使用者篩選日期範圍（3月1日-31日），**Then** 只顯示 3 月的交易
4. **Given** 使用者選擇 "Food" 帳戶，**When** 檢視該帳戶的交易，**Then** 只顯示涉及 Food 帳戶的交易

---

### User Story 4 - Multiple Ledgers Management (Priority: P3)

使用者想要分離不同的財務情境（個人 vs. 商業、不同年度）。

**Why this priority**: 這是組織性功能，增強基本產品但非初期必須。

**Acceptance Scenarios**:

1. **Given** 使用者帳號存在，**When** 建立 "2024 Personal" 和 "2024 Business" 帳本，**Then** 每個帳本有獨立的科目表和交易列表
2. **Given** 兩個帳本都有名為 "Cash" 的帳戶，**When** 在一個帳本記錄交易，**Then** 另一個帳本的 Cash 帳戶不受影響
3. **Given** 存在多個帳本，**When** 使用者切換帳本，**Then** 系統載入正確的帳戶和交易

---

### Edge Cases

- Zero-amount transactions: 允許，但儲存前必須顯示警告確認
- Very large amounts (999,999,999): 系統應正確處理
- Same account transfer (Cash to Cash): 應阻止
- Future dated transactions: 允許
- Negative balances: Asset/Liability 帳戶允許負餘額並顯示警告
- Delete accounts with transactions: 應阻止刪除

## Requirements

### Functional Requirements

- **FR-001**: System MUST support creation of multiple ledgers per user, each with independent chart of accounts and transactions
- **FR-002**: System MUST enforce double-entry bookkeeping (every transaction affects exactly two accounts with equal amounts)
- **FR-003**: System MUST support four account types: Asset, Liability, Income, Expense
- **FR-004**: System MUST prevent deletion of predefined accounts: "Cash" and "Equity"
- **FR-005**: System MUST support three transaction types: Expense, Income, Transfer
- **FR-006**: System MUST block saving unbalanced transactions (Debits MUST equal Credits)
- **FR-007**: Users MUST be able to edit existing transactions with balances updated immediately
- **FR-008**: Users MUST be able to delete transactions with confirmation prompt
- **FR-009**: System MUST recalculate affected account balances when transactions change
- **FR-010**: System MUST support searching transactions by description, account, or date range
- **FR-011**: System MUST store: date, transaction type, from_account, to_account, amount, description
- **FR-012**: System MUST allow negative balances for Asset/Liability with visual warning
- **FR-013**: System MUST require confirmation for zero-amount transactions

### Data Integrity Requirements

- **DI-001**: All amounts MUST support exactly 2 decimal places with banker's rounding
- **DI-002**: System MUST maintain audit trail through transaction log
- **DI-003**: System MUST enforce double-entry where total debits equal total credits
- **DI-004**: System MUST require confirmation before deleting transactions or ledgers
- **DI-005**: All balance calculations MUST be traceable to source transactions

### API Requirements

- **API-001**: FastAPI backend MUST expose RESTful endpoints for all CRUD operations
- **API-002**: All endpoints MUST return proper HTTP status codes and error messages
- **API-003**: API MUST support pagination for transaction lists
- **API-004**: API MUST validate all inputs before database operations

## Database Schema

### `accounts`

| Field        | Type          | Description                                 |
| ------------ | ------------- | ------------------------------------------- |
| `id`         | UUID          | Primary key                                 |
| `ledger_id`  | UUID          | Foreign key to ledger                       |
| `name`       | String        | Account name (e.g., Cash, Bank, Food)       |
| `type`       | Enum          | ASSET, LIABILITY, INCOME, EXPENSE           |
| `balance`    | Decimal(15,2) | Current balance (cached, calculated)        |
| `is_system`  | Boolean       | True for predefined accounts (Cash, Equity) |
| `created_at` | Timestamp     | Creation time                               |
| `updated_at` | Timestamp     | Last update time                            |

### `transactions`

| Field              | Type          | Description                      |
| ------------------ | ------------- | -------------------------------- |
| `id`               | UUID          | Primary key                      |
| `ledger_id`        | UUID          | Foreign key to ledger            |
| `date`             | Date          | Transaction date                 |
| `description`      | String        | Transaction description          |
| `amount`           | Decimal(15,2) | Amount (positive value)          |
| `from_account_id`  | UUID          | Source account (Credit side)     |
| `to_account_id`    | UUID          | Destination account (Debit side) |
| `transaction_type` | Enum          | EXPENSE, INCOME, TRANSFER        |
| `created_at`       | Timestamp     | Creation time                    |
| `updated_at`       | Timestamp     | Last update time                 |

### `ledgers`

| Field             | Type          | Description          |
| ----------------- | ------------- | -------------------- |
| `id`              | UUID          | Primary key          |
| `user_id`         | UUID          | Foreign key to user  |
| `name`            | String        | Ledger name          |
| `initial_balance` | Decimal(15,2) | Initial cash balance |
| `created_at`      | Timestamp     | Creation time        |

### `balance_snapshots` (for future growth analysis)

| Field        | Type          | Description                         |
| ------------ | ------------- | ----------------------------------- |
| `id`         | UUID          | Primary key                         |
| `date`       | Date          | Snapshot date (typically month-end) |
| `account_id` | UUID          | Foreign key to account              |
| `amount`     | Decimal(15,2) | Balance at snapshot time            |

## Success Criteria

- **SC-001**: Users can create ledger and record first transaction in under 3 minutes
- **SC-002**: System maintains data integrity with zero balance calculation errors
- **SC-003**: Users can find specific transaction via search within 10 seconds
- **SC-004**: API response time under 200ms for typical operations
- **SC-005**: System prevents 100% of unbalanced transactions
- **SC-006**: Multiple ledgers remain completely isolated

## Assumptions

- **A-001**: Users understand basic accounting concepts
- **A-002**: Single currency per ledger
- **A-003**: Users manually backup data (cloud sync in future feature)
- **A-004**: Desktop-first, PWA support in separate feature
- **A-005**: Single-user mode (no concurrent editing)

## Constraints

- **C-001**: PostgreSQL as primary database
- **C-002**: Predefined accounts cannot be deleted
- **C-003**: Single currency per ledger
- **C-004**: No undo/redo (use transaction edit/delete)

## Out of Scope (Separate Features)

- **002-dashboard**: Dashboard with net worth tracking, balance sheet, CAGR calculation
- **003-analytics**: Sankey diagrams, YoY/MoM reports, expense heatmaps, budget alerts
- **004-ai-import**: AI-powered CSV import with auto-categorization, duplicate detection
- **005-pwa-mobile**: PWA support, mobile-optimized UI, Tauri desktop wrapper
- **006-reports**: Financial reports and charts export
- **007-backup**: Backup and restore functionality

## Dependencies

- None - this is the foundational feature

## References

- Project vision document (provided 2026-01-02)
- Design references: Maybe Finance, Linear (dark mode, minimal UI)
