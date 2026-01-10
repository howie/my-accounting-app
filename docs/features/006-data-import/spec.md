# Feature Specification: 資料匯入功能

**Feature Branch**: `006-data-import`
**Created**: 2026-01-09
**Status**: Draft
**Input**: User description: "006-data-import 參考 ROADMAP.md - 批次匯入入口、MyAB CSV 匯入、信用卡帳單匯入"

## Clarifications

### Session 2026-01-09

- Q: 重複交易偵測策略為何？ → A: 寬鬆比對（同日期+同金額+同科目即警告，忽略備註差異）
- Q: 信用卡帳單初始支援的銀行數量？ → A: 五家以上銀行（涵蓋大多數台灣發卡銀行）
- Q: CSV 檔案大小限制？ → A: 10MB（平衡檔案大小與效能）
- Q: 部分交易驗證失敗的處理策略？ → A: 全有或全無（任一筆失敗則整批取消）

## User Scenarios & Testing _(mandatory)_

### User Story 1 - MyAB CSV 匯入 (Priority: P1)

使用者從舊的 MyAB 記帳軟體匯出 CSV 檔案，想要將歷史記帳資料匯入到本系統。使用者選擇 CSV 檔案後，系統會解析 MyAB 的匯出格式，自動對應或建立科目，讓使用者預覽匯入資料後確認匯入。

**Why this priority**: 這是最核心的匯入功能，讓使用者能夠從既有的記帳系統遷移資料，降低轉換成本，是新使用者採用本系統的關鍵功能。

**Independent Test**: 可以獨立測試 - 準備一個 MyAB 匯出的 CSV 檔案，執行匯入流程，驗證交易資料正確寫入系統。

**Acceptance Scenarios**:

1. **Given** 使用者有 MyAB 匯出的 CSV 檔案, **When** 使用者上傳 CSV 檔案, **Then** 系統解析並顯示匯入預覽（包含交易筆數、日期範圍、涉及科目）
2. **Given** CSV 中包含系統尚未存在的科目名稱, **When** 系統解析 CSV 時, **Then** 系統提示使用者選擇：自動建立新科目或對應到現有科目
3. **Given** 使用者已確認科目對應, **When** 使用者點擊「確認匯入」, **Then** 系統批次建立所有交易，並顯示匯入結果摘要
4. **Given** CSV 格式不正確或檔案損壞, **When** 使用者上傳該檔案, **Then** 系統顯示明確錯誤訊息，說明問題所在

---

### User Story 2 - 批次匯入入口 (Priority: P1)

使用者想要匯入外部資料，可以從選單中找到「批次匯入」功能入口，進入匯入頁面選擇匯入類型（MyAB CSV 或信用卡帳單）。

**Why this priority**: 這是所有匯入功能的入口，與 User Story 1 同屬 P1，因為沒有入口就無法進行任何匯入操作。

**Independent Test**: 可以獨立測試 - 驗證選單中有「批次匯入」選項，點擊後可進入匯入頁面並看到匯入類型選項。

**Acceptance Scenarios**:

1. **Given** 使用者已登入並在任一頁面, **When** 使用者點擊選單中的「批次匯入」, **Then** 系統導向匯入頁面，顯示可用的匯入類型
2. **Given** 使用者在匯入頁面, **When** 使用者選擇「MyAB CSV 匯入」, **Then** 系統顯示 CSV 檔案上傳介面
3. **Given** 使用者在匯入頁面, **When** 使用者選擇「信用卡帳單匯入」, **Then** 系統顯示信用卡帳單上傳介面

---

### User Story 3 - 信用卡帳單 CSV 匯入 (Priority: P2)

使用者從銀行下載信用卡帳單 CSV 檔案，想要快速匯入消費記錄。系統解析 CSV 後，自動將消費項目分類到適當的支出科目。

**Why this priority**: 信用卡帳單匯入能大幅減少手動記帳時間，但需要先有基本的匯入框架（P1）才能擴展支援。

**Independent Test**: 可以獨立測試 - 準備一個銀行信用卡帳單 CSV，執行匯入流程，驗證消費記錄正確分類並寫入系統。

**Acceptance Scenarios**:

1. **Given** 使用者有銀行信用卡帳單 CSV, **When** 使用者上傳 CSV 並選擇銀行/信用卡類型, **Then** 系統解析並顯示消費明細預覽
2. **Given** 系統解析到消費項目, **When** 顯示預覽時, **Then** 每筆消費顯示建議的支出科目分類（使用者可調整）
3. **Given** 使用者已確認分類, **When** 使用者點擊「確認匯入」, **Then** 系統建立所有支出交易（從信用卡科目轉出到各支出科目）
4. **Given** CSV 格式與所選銀行不符, **When** 使用者上傳該檔案, **Then** 系統提示格式錯誤並建議檢查銀行選擇是否正確

---

### Edge Cases

- 重複匯入：使用者上傳 CSV 檔案時，系統以「同日期+同金額+同科目」比對現有交易，符合條件即顯示重複警告（忽略備註差異）
- 大量資料：CSV 包含超過 1000 筆交易時，系統應顯示進度指示，避免使用者以為系統無回應
- 金額格式：不同來源的 CSV 可能使用不同的金額格式（如 "1,000.00" vs "1000" vs "-1000"），系統應能正確解析
- 日期格式：不同來源可能使用不同日期格式（如 "2026/01/09" vs "2026-01-09" vs "01/09/2026"），系統應能正確解析
- 編碼問題：CSV 檔案可能使用不同編碼（UTF-8、Big5），系統應能正確處理或提示使用者
- 科目階層：MyAB 匯入時若科目有父子關係，應保留階層結構
- 取消匯入：使用者在預覽階段取消時，不應產生任何資料變更
- 部分失敗：批次匯入中若任一筆交易驗證失敗，整批匯入取消（原子操作），系統顯示所有錯誤明細供使用者修正 CSV 後重試

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST provide a "Batch Import" menu entry accessible from the sidebar navigation
- **FR-002**: System MUST support importing MyAB CSV export files
- **FR-003**: System MUST parse and validate CSV files before import, showing clear error messages for invalid formats
- **FR-004**: System MUST display an import preview showing: total transaction count, date range, accounts involved, and sample transactions
- **FR-005**: System MUST allow users to map CSV accounts to existing system accounts or create new accounts
- **FR-006**: System MUST support automatic account creation during import with user confirmation
- **FR-007**: System MUST require explicit user confirmation before executing the import
- **FR-008**: System MUST display import results summary after completion (success count, error count, created accounts)
- **FR-009**: System MUST support importing credit card statement CSV files
- **FR-010**: System MUST allow users to select bank/card type before parsing credit card statements
- **FR-011**: System MUST suggest expense categories for credit card transactions based on merchant/description keywords
- **FR-012**: System MUST allow users to modify suggested categories before confirming import
- **FR-013**: System MUST detect potential duplicate transactions (matching date + amount + account, ignoring notes) and warn users before import
- **FR-014**: System MUST support cancellation at any point before final confirmation without data changes
- **FR-015**: System MUST handle various date formats commonly used in Taiwan (yyyy/MM/dd, yyyy-MM-dd, MM/dd/yyyy)
- **FR-016**: System MUST handle various number formats (with/without thousand separators, negative signs)
- **FR-017**: System MUST support UTF-8 and Big5 encoded CSV files
- **FR-018**: System MUST reject CSV files larger than 10MB with clear error message

### Data Integrity Requirements _(required for features modifying financial data)_

- **DI-001**: System MUST validate all imported amounts (format, range, precision - max 2 decimal places for TWD)
- **DI-002**: System MUST create audit trail entries for all imported transactions, marking them as "imported" with source file reference
- **DI-003**: System MUST enforce double-entry bookkeeping for all imported transactions (debits = credits)
- **DI-004**: System MUST execute import as an atomic operation - all transactions succeed or all are rolled back
- **DI-005**: System MUST preserve original transaction dates from source file
- **DI-006**: System MUST NOT allow partial imports to corrupt existing data

### Key Entities _(include if feature involves data)_

- **ImportSession**: Represents a single import operation - tracks source file, type (MyAB/CreditCard), status, timestamp, user
- **ImportPreview**: Temporary data structure holding parsed transactions before user confirmation
- **AccountMapping**: User-defined mapping from CSV account names to system accounts
- **CategorySuggestion**: Keyword-based rules for suggesting expense categories for credit card transactions

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Users can complete a MyAB CSV import (under 500 transactions) in under 5 minutes from file selection to confirmation
- **SC-002**: 90% of imported transactions require no manual account mapping adjustment (auto-mapping accuracy)
- **SC-003**: Credit card transaction category suggestions are accepted by users 70% of the time without modification
- **SC-004**: System handles CSV files with up to 2000 transactions without timeout or error
- **SC-005**: Zero data corruption incidents - all imports maintain double-entry balance integrity
- **SC-006**: Users can identify and resolve import errors without contacting support (clear error messages)

## Assumptions

- MyAB CSV export format is documented and consistent (based on reference spec 5.3)
- Initial supported banks for credit card import: 五家以上台灣主要發卡銀行（如國泰世華、中國信託、玉山、台新、富邦等），具體清單於 planning 階段確定
- Category suggestion rules will be based on simple keyword matching initially, with potential for ML-based improvement in future
- Import is per-ledger - users must select the target ledger before importing
- Original MyAB transaction IDs (if any) are not preserved; new system IDs are generated

## Out of Scope

- AI/Conversational import (marked as "Future" in roadmap - will be separate feature)
- PDF parsing for credit card statements (CSV only for initial release)
- Real-time bank API integration
- Automatic recurring import scheduling
- Import from other accounting software (only MyAB for now)
