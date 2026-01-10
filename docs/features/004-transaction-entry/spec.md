# Feature Specification: Transaction Entry

**Feature Branch**: `004-transaction-entry`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "Transaction entry feature for adding new transactions from account page"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Add Transaction from Account Page (Priority: P1)

使用者在瀏覽科目頁面時，想要直接從該頁面新增交易，而不需要跳轉到其他地方。這讓記帳流程更加順暢。

**Why this priority**: 這是核心功能 - 使用者最常用的操作就是新增交易。從科目頁面直接新增是最自然的入口點。

**Independent Test**: 使用者點擊科目頁面的「新增交易」按鈕，填寫表單後儲存，交易立即出現在該科目的交易列表中。

**Acceptance Scenarios**:

1. **Given** 使用者在 "Cash" 帳戶頁面，**When** 點擊「新增交易」按鈕，**Then** 顯示交易表單，且 From 帳戶預設為 "Cash"
2. **Given** 交易表單已開啟，**When** 使用者選擇交易類型為「支出」、To 帳戶為 "Food"、金額 150、日期為今天，**Then** 可以成功儲存交易
3. **Given** 交易成功儲存，**When** 表單關閉，**Then** 新交易立即顯示在科目的交易列表中，不需手動重新整理
4. **Given** 使用者在 "Salary" (Income) 帳戶頁面，**When** 點擊新增交易，**Then** From 帳戶預設為 "Salary"，交易類型自動設為「收入」

---

### User Story 2 - Smart Amount Input with Calculator (Priority: P1)

使用者在輸入金額時，經常需要做簡單計算（例如：分攤餐費、合計多項支出）。支援表達式計算可以減少心算錯誤。

**Why this priority**: 金額輸入是交易表單的核心欄位，計算功能大幅提升使用體驗，且實作成本不高。

**Independent Test**: 使用者在金額欄位輸入 "50+40+10"，按下 Enter 或離開欄位時，自動計算並顯示結果 100。

**Acceptance Scenarios**:

1. **Given** 金額輸入欄位為空，**When** 使用者輸入 "50+40"，**Then** 欄位即時顯示表達式，失焦後計算結果為 90
2. **Given** 使用者輸入表達式 "1000/4"，**When** 失焦，**Then** 顯示結果 250
3. **Given** 使用者輸入無效表達式 "50++40"，**When** 失焦，**Then** 顯示錯誤提示並保留原始輸入
4. **Given** 使用者輸入 "100\*1.1"，**When** 失焦，**Then** 顯示 110 並自動四捨五入到小數點後兩位
5. **Given** 計算結果已顯示，**When** 使用者點擊金額欄位，**Then** 可以看到原始表達式進行修改

---

### User Story 3 - Select Date for Transaction (Priority: P1)

使用者需要為交易指定日期，可能是今天、昨天、或更早的日期（補記帳）。

**Why this priority**: 日期是交易的必要欄位，且使用者經常需要補記過去的交易。

**Independent Test**: 使用者點擊日期欄位，從日曆選擇器中選擇日期，該日期正確顯示在表單中。

**Acceptance Scenarios**:

1. **Given** 交易表單開啟，**When** 檢視日期欄位，**Then** 預設為今天日期
2. **Given** 使用者點擊日期欄位，**When** 日曆選擇器顯示，**Then** 可以選擇過去或未來的日期
3. **Given** 使用者需要記錄昨天的交易，**When** 選擇昨天日期並儲存，**Then** 交易以正確日期儲存並顯示在列表的正確位置
4. **Given** 日曆選擇器開啟，**When** 點擊「今天」按鈕，**Then** 快速選擇今天日期

---

### User Story 4 - Add Description and Notes (Priority: P2)

使用者想要為交易添加描述（必填）和備註（選填），以便日後查詢和追蹤。

**Why this priority**: 描述是識別交易的關鍵，但基本功能可以先只支援描述欄位。

**Independent Test**: 使用者填寫描述和備註後儲存，兩個欄位的內容都正確保存並顯示。

**Acceptance Scenarios**:

1. **Given** 交易表單開啟，**When** 描述欄位為空並嘗試儲存，**Then** 顯示驗證錯誤「請輸入交易描述」
2. **Given** 使用者輸入描述 "午餐 - 麥當勞"，**When** 儲存交易，**Then** 描述正確顯示在交易列表中
3. **Given** 使用者輸入備註 "與同事聚餐，AA制"，**When** 儲存並檢視交易詳情，**Then** 備註完整顯示
4. **Given** 備註欄位為空，**When** 儲存交易，**Then** 交易正常儲存（備註為選填）

---

### User Story 5 - Save Transaction Template (Priority: P2)

使用者有固定的週期性支出（例如：每月房租、定期儲蓄），想要將常用交易儲存為模板以便快速記帳。

**Why this priority**: 模板功能可以顯著提升重複交易的記帳效率，但不是首次使用的必要功能。

**Independent Test**: 使用者將一筆交易儲存為模板，之後可以在模板列表中看到並套用它。

**Acceptance Scenarios**:

1. **Given** 交易表單已填寫完成，**When** 使用者點擊「儲存為模板」並輸入模板名稱 "月租房"，**Then** 模板成功儲存
2. **Given** 存在多個已儲存的模板，**When** 使用者開啟模板選擇器，**Then** 顯示所有模板列表（名稱、金額、帳戶）
3. **Given** 使用者選擇 "月租房" 模板，**When** 套用模板，**Then** 表單自動填入模板的所有欄位（日期保持今天）
4. **Given** 模板已套用，**When** 使用者修改金額後儲存，**Then** 以修改後的值儲存交易，模板本身不受影響

---

### User Story 6 - Quick Apply Template (Priority: P2)

使用者想要用最少的步驟快速記錄常用交易，例如：一鍵記錄 "早餐"。

**Why this priority**: 這是模板功能的延伸，讓記帳更快速，但依賴於 User Story 5 的完成。

**Independent Test**: 使用者點擊常用模板的快速按鈕，交易立即儲存，不需要額外操作。

**Acceptance Scenarios**:

1. **Given** 存在已儲存的模板，**When** 使用者進入快速記帳模式，**Then** 顯示模板快捷按鈕列表
2. **Given** 使用者點擊 "早餐" 模板的快速按鈕，**When** 確認對話框顯示交易摘要，**Then** 使用者可以選擇「確認」或「編輯」
3. **Given** 使用者選擇「確認」，**When** 點擊後，**Then** 交易以今天日期立即儲存並顯示成功訊息
4. **Given** 使用者選擇「編輯」，**When** 點擊後，**Then** 開啟完整交易表單，所有欄位已預填

---

### User Story 7 - Manage Templates (Priority: P3)

使用者需要管理已儲存的模板：編輯、刪除、或調整順序。

**Why this priority**: 這是模板功能的維護需求，優先級較低但對長期使用者很重要。

**Independent Test**: 使用者可以編輯模板的內容並儲存變更。

**Acceptance Scenarios**:

1. **Given** 存在 "月租房" 模板，**When** 使用者選擇編輯並修改金額為 15000，**Then** 模板更新成功
2. **Given** 存在不再使用的模板，**When** 使用者選擇刪除並確認，**Then** 模板從列表中移除
3. **Given** 存在多個模板，**When** 使用者拖拉調整順序，**Then** 新順序保存並反映在快速記帳列表中

---

### Edge Cases

- 金額為 0：顯示警告確認（「確定要儲存金額為 0 的交易嗎？」）
- 金額表達式除以 0：顯示錯誤「無法除以零」
- 超長描述（超過 200 字元）：截斷並提示
- 選擇相同的 From/To 帳戶：阻止並顯示錯誤
- 模板名稱重複：提示「模板名稱已存在，是否覆蓋？」
- 帳戶已刪除但模板仍引用：套用時顯示錯誤並建議編輯模板
- 金額超過系統最大值（999,999,999.99）：顯示錯誤
- 模板數量達到上限（50 個）：顯示錯誤並建議刪除不常用的模板

## Requirements _(mandatory)_

### Functional Requirements

**Transaction Entry**

- **FR-001**: System MUST provide "Add Transaction" button on each account page that opens a modal dialog
- **FR-002**: System MUST pre-select the current account as From/To account based on account type (Asset/Expense as From, Income/Liability as To)
- **FR-003**: System MUST support three transaction types: Expense, Income, Transfer
- **FR-004**: System MUST auto-suggest transaction type based on From account type
- **FR-005**: System MUST validate that From and To accounts are different
- **FR-006**: System MUST close modal and refresh transaction list after successful save without page reload

**Amount Input**

- **FR-007**: System MUST support basic arithmetic expressions in amount field (+, -, \*, /)
- **FR-008**: System MUST calculate expression result on field blur or Enter key
- **FR-009**: System MUST display error for invalid expressions without losing user input
- **FR-010**: System MUST round calculation results to 2 decimal places (banker's rounding)
- **FR-011**: System MUST allow viewing/editing original expression after calculation

**Date Selection**

- **FR-012**: System MUST provide date picker with calendar view
- **FR-013**: System MUST default to today's date
- **FR-014**: System MUST support selecting past and future dates
- **FR-015**: System MUST provide "Today" quick-select button in calendar

**Description & Notes**

- **FR-016**: System MUST require description field (non-empty)
- **FR-017**: System MUST support optional notes field (maximum 500 characters)
- **FR-018**: System MUST limit description to 200 characters

**Transaction Templates**

- **FR-019**: System MUST allow saving current form values as named template (maximum 50 templates per ledger)
- **FR-020**: System MUST store template: name, transaction type, from_account, to_account, amount, description
- **FR-021**: System MUST display template list with name, amount, accounts preview
- **FR-022**: System MUST apply template values to form (except date, which defaults to today)
- **FR-023**: System MUST allow editing existing templates
- **FR-024**: System MUST allow deleting templates with confirmation
- **FR-025**: System MUST support reordering templates via drag-and-drop

**Quick Entry**

- **FR-026**: System MUST provide quick-entry mode on Dashboard showing template buttons
- **FR-027**: System MUST show confirmation dialog before quick-save
- **FR-028**: System MUST allow user to edit before saving from quick-entry

### Data Integrity Requirements _(required for features modifying financial data)_

- **DI-001**: System MUST validate amount format, range (0.01 - 999,999,999.99), and precision (2 decimal places)
- **DI-002**: System MUST maintain audit trail for all transactions (created_at, updated_at)
- **DI-003**: System MUST enforce double-entry bookkeeping (From account credited, To account debited)
- **DI-004**: System MUST require confirmation for zero-amount transactions
- **DI-005**: System MUST ensure all calculations are traceable (store original expression if used)

### Key Entities _(include if feature involves data)_

- **Transaction**: Core entity storing date, description, amount, from_account, to_account, transaction_type, notes (extends existing model from 001-core-accounting)
- **TransactionTemplate**: Reusable transaction preset storing name, transaction_type, from_account_id, to_account_id, amount, description, sort_order

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Users can add a new transaction from account page in under 30 seconds
- **SC-002**: Users can apply a template and save transaction in under 10 seconds
- **SC-003**: 95% of users successfully complete their first transaction entry without errors
- **SC-004**: Calculator expressions are correctly evaluated 100% of the time
- **SC-005**: System prevents 100% of invalid transactions (same account, empty description, invalid amount)
- **SC-006**: Transaction appears in list within 1 second after save (no page refresh required)

## Assumptions

- **A-001**: Users have already set up accounts in their ledger (via 001-core-accounting or 003-settings-account-management)
- **A-002**: Single currency per ledger (no currency conversion needed)
- **A-003**: Templates are ledger-specific (not shared across ledgers)
- **A-004**: Mobile/responsive design follows patterns established in 002-ui-layout-dashboard

## Constraints

- **C-001**: Must integrate with existing transaction data model from 001-core-accounting
- **C-002**: Must follow i18n patterns established in 002-ui-layout-dashboard (zh-TW, en)
- **C-003**: Must respect dark/light mode from 003-settings-account-management

## Dependencies

- **001-core-accounting**: Transaction data model, account types, double-entry validation
- **002-ui-layout-dashboard**: Account page layout, sidebar integration
- **003-settings-account-management**: Account hierarchy for account selection dropdown

## Clarifications

### Session 2026-01-09

- Q: Transaction form UI pattern? → A: Modal dialog (彈出視窗，覆蓋在當前頁面上)
- Q: Quick entry access location? → A: Dashboard 上的快捷區塊或浮動按鈕
- Q: Form behavior after save? → A: 關閉 Modal，返回交易列表
- Q: Maximum templates per ledger? → A: 50 個
- Q: Notes field character limit? → A: 500 字元
- Q: Max amount error message? → A: "金額必須在 0.01 到 999,999,999.99 之間" / "Amount must be between 0.01 and 999,999,999.99"
- Q: Zero amount warning message? → A: "確定要儲存金額為 0 的交易嗎？" / "Are you sure you want to save a transaction with zero amount?"

## References

- ROADMAP.md section 004-transaction-entry
- MyAB spec 2.1, 2.2 (快速入帳、交易模板)
