# Feature Specification: Gmail 信用卡帳單自動掃描匯入

**Feature Branch**: `011-gmail-cc-statement-import`
**Created**: 2026-02-05
**Status**: Draft
**Input**: User description: "Gmail 信用卡帳單自動掃描匯入功能。系統定期掃描使用者的 Gmail 信箱，自動搜尋並下載各銀行信用卡電子帳單（PDF 附件），解密 PDF、解析帳單內容，並匯入到複式記帳系統。"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - 連接 Gmail 帳號並授權 (Priority: P1)

使用者想要讓系統自動從 Gmail 抓取信用卡帳單。使用者在設定頁面中點選「連接 Gmail」，透過 Google OAuth2 授權流程授予系統唯讀郵件權限。授權完成後，系統顯示連接狀態為「已連接」，並記錄授權的 Gmail 帳號。

**Why this priority**: 這是整個功能的基礎——沒有 Gmail 連接授權，後續的帳單搜尋、下載、解析都無法進行。這是最小可行功能的起點。

**Independent Test**: 可以獨立測試——使用者完成 OAuth2 授權流程後，系統能成功存取 Gmail API 並顯示連接狀態，無需其他帳單處理功能。

**Acceptance Scenarios**:

1. **Given** 使用者尚未連接 Gmail, **When** 使用者點擊「連接 Gmail」按鈕, **Then** 系統開啟 Google OAuth2 授權頁面，要求唯讀郵件權限
2. **Given** 使用者在 Google 授權頁面, **When** 使用者同意授權, **Then** 系統儲存授權憑證並顯示「Gmail 已連接」狀態及已連接的 Gmail 帳號
3. **Given** 使用者已連接 Gmail, **When** 使用者回到設定頁面, **Then** 系統顯示目前連接狀態、已連接帳號、上次掃描時間
4. **Given** 使用者已連接 Gmail, **When** 使用者點擊「中斷連接」, **Then** 系統撤銷授權並移除已儲存的憑證

---

### User Story 2 - 手動觸發帳單掃描與預覽 (Priority: P1)

使用者連接 Gmail 後，想要手動掃描信箱中的信用卡帳單。使用者點擊「掃描帳單」按鈕，系統搜尋符合各銀行特徵的郵件，下載 PDF 附件，解密後解析帳單內容，以清單方式顯示找到的帳單供使用者確認匯入。

**Why this priority**: 手動掃描是核心使用流程——使用者需要能觸發掃描、看到找到的帳單、並決定是否匯入。這與 P1 的 Gmail 連接一起構成最小可行產品。

**Independent Test**: 可以獨立測試——使用者觸發掃描後，系統能找到帳單郵件、列出帳單摘要（銀行名稱、帳單月份、總金額），使用者可選擇匯入或跳過。

**Acceptance Scenarios**:

1. **Given** 使用者已連接 Gmail, **When** 使用者點擊「掃描帳單」, **Then** 系統顯示掃描進度，搜尋各銀行的帳單郵件
2. **Given** 系統正在掃描, **When** 找到符合條件的帳單郵件, **Then** 系統下載 PDF 附件並嘗試解密
3. **Given** 系統已解密並解析 PDF, **When** 掃描完成, **Then** 系統顯示帳單清單，包含：銀行名稱、帳單期間、消費筆數、總金額
4. **Given** 使用者看到帳單清單, **When** 使用者選擇一份帳單點擊「預覽」, **Then** 系統顯示該帳單的逐筆消費明細，每筆包含日期、商家名稱、金額、建議分類
5. **Given** 系統掃描後未找到任何帳單, **When** 掃描完成, **Then** 系統顯示「未找到新帳單」訊息，並提示使用者檢查銀行設定或時間範圍

---

### User Story 3 - 確認匯入帳單到記帳系統 (Priority: P1)

使用者預覽帳單消費明細後，確認分類無誤，點擊「確認匯入」將消費明細匯入複式記帳系統。每筆消費建立為一筆交易（從信用卡科目支出到對應的費用科目）。

**Why this priority**: 匯入是整個功能的核心價值交付——使用者期望的最終結果就是帳單資料進入記帳系統，與手動掃描和預覽一起構成完整的核心流程。

**Independent Test**: 可以獨立測試——使用者確認匯入後，可在帳本中看到新建立的交易記錄，金額、日期、分類皆正確。

**Acceptance Scenarios**:

1. **Given** 使用者已預覽帳單明細, **When** 使用者點擊「確認匯入」, **Then** 系統將所有消費明細建立為交易記錄，標記來源為「Gmail 帳單匯入」
2. **Given** 使用者在預覽頁面, **When** 使用者修改某筆消費的分類, **Then** 系統以修改後的分類建立交易
3. **Given** 系統偵測到部分消費可能與已存在的交易重複, **When** 顯示預覽時, **Then** 重複項目以警告標示，使用者可選擇跳過或仍然匯入
4. **Given** 匯入過程中發生錯誤, **When** 任一筆交易建立失敗, **Then** 整批匯入回滾，不留下部分資料，並顯示錯誤原因

---

### User Story 4 - 設定支援的銀行與 PDF 密碼 (Priority: P2)

使用者需要設定要掃描的銀行以及對應的 PDF 解密密碼。使用者在設定頁面中選擇要啟用的銀行，並為需要密碼的銀行輸入解密密碼（如身分證字號）。密碼以加密方式儲存。

**Why this priority**: 銀行與密碼設定是帳單解析的前置條件，但可以在核心掃描流程完成後再精細化——初始版本可用預設密碼規則，此功能讓使用者自訂設定。

**Independent Test**: 可以獨立測試——使用者新增銀行設定並輸入密碼後，可以看到已設定的銀行清單，密碼以遮罩方式顯示。

**Acceptance Scenarios**:

1. **Given** 使用者在 Gmail 帳單匯入設定頁面, **When** 使用者查看銀行清單, **Then** 系統顯示所有支援的銀行及其啟用狀態
2. **Given** 使用者想啟用某家銀行, **When** 使用者切換該銀行為啟用, **Then** 系統要求輸入 PDF 解密密碼（若該銀行帳單有密碼保護）
3. **Given** 使用者已輸入密碼, **When** 使用者儲存設定, **Then** 密碼以加密方式儲存，畫面上以遮罩顯示
4. **Given** 使用者想修改密碼, **When** 使用者點擊「修改密碼」, **Then** 使用者可輸入新密碼並儲存

---

### User Story 5 - 定期自動掃描排程 (Priority: P3)

使用者希望系統能定期自動掃描 Gmail 信箱中的新帳單，不必每次手動觸發。使用者可在設定中選擇掃描頻率（如每天、每週），系統在排定時間自動執行掃描，找到新帳單後通知使用者確認匯入。

**Why this priority**: 自動排程是便利功能，核心價值（掃描+匯入）已在 P1 中實現。排程只是減少手動觸發的步驟，非核心 MVP 必要功能。

**Independent Test**: 可以獨立測試——設定排程後，系統在指定時間自動執行掃描，使用者在下次登入時看到掃描結果通知。

**Acceptance Scenarios**:

1. **Given** 使用者已連接 Gmail, **When** 使用者在設定中選擇「每週自動掃描」, **Then** 系統記錄排程設定並顯示下次掃描時間
2. **Given** 排定掃描時間到達, **When** 系統自動執行掃描, **Then** 系統搜尋自上次掃描以來的新帳單
3. **Given** 自動掃描找到新帳單, **When** 使用者下次登入系統, **Then** 系統顯示「發現 N 份新帳單待確認」通知
4. **Given** 使用者收到新帳單通知, **When** 使用者點擊通知, **Then** 系統導向帳單預覽頁面，流程與手動掃描相同

---

### User Story 6 - 可擴充的銀行 Parser 架構 (Priority: P2)

系統設計為可擴充的架構，當需要支援新銀行時，開發者只需新增一個銀行解析器（包含郵件搜尋條件、PDF 密碼規則、帳單表格解析邏輯），無需修改核心掃描或匯入流程。

**Why this priority**: 可擴充架構是長期維護的關鍵。初始版本需要支援至少 8 家銀行，如果沒有良好的架構設計，每新增一家銀行就需要大量重複程式碼。

**Independent Test**: 可以獨立測試——開發者按照定義好的介面新增一家測試銀行的解析器，驗證該解析器能正確搜尋、解密、解析帳單，且核心程式碼不需修改。

**Acceptance Scenarios**:

1. **Given** 系統已支援多家銀行, **When** 開發者需要新增一家銀行的支援, **Then** 只需實作該銀行的解析器（搜尋條件 + 解密規則 + 表格解析），無需修改掃描或匯入邏輯
2. **Given** 開發者實作了新的銀行解析器, **When** 系統啟動時, **Then** 新銀行自動出現在支援的銀行清單中
3. **Given** 系統使用可擴充架構, **When** 某家銀行更改帳單格式, **Then** 只需更新該銀行的解析器，不影響其他銀行

---

### User Story 7 - 掃描歷史紀錄 (Priority: P3)

使用者想要查看過去的掃描與匯入紀錄，了解哪些帳單已處理、哪些被跳過。系統提供掃描歷史清單，包含每次掃描的時間、找到的帳單數、匯入狀態。

**Why this priority**: 歷史紀錄是輔助功能，幫助使用者追溯過去的操作，但不影響核心的掃描與匯入流程。

**Independent Test**: 可以獨立測試——執行幾次掃描（手動或自動）後，使用者在歷史頁面可看到所有掃描記錄及其結果。

**Acceptance Scenarios**:

1. **Given** 使用者已執行過多次掃描, **When** 使用者進入掃描歷史頁面, **Then** 系統顯示所有掃描記錄，按時間倒序排列
2. **Given** 使用者查看某次掃描紀錄, **When** 使用者點擊該紀錄, **Then** 系統顯示該次掃描找到的帳單清單及每份帳單的處理狀態（已匯入/已跳過/匯入失敗）

---

### Edge Cases

- PDF 解密失敗：銀行帳單 PDF 密碼不正確或密碼規則已變更，系統應明確提示「PDF 解密失敗，請確認密碼設定」，並記錄失敗的帳單供使用者重試
- 帳單格式變更：銀行更改帳單 PDF 的表格格式或版面配置，導致解析失敗。系統應記錄原始 PDF 供人工檢視，並標記該帳單為「解析失敗」
- Gmail 授權過期：OAuth2 token 過期或被使用者撤銷，系統在下次掃描時提示重新授權
- 同一帳單重複寄送：銀行可能重寄帳單郵件，系統應以帳單期間+銀行名稱識別唯一帳單，避免重複處理
- 非信用卡帳單 PDF：搜尋結果中可能包含銀行寄送的其他 PDF（如行銷文件），系統應能辨識並跳過非帳單 PDF
- 大量歷史帳單：使用者首次連接時可能有大量歷史帳單郵件，系統應支援設定掃描的起始日期，避免一次處理過多帳單
- 網路連線中斷：Gmail API 呼叫或 PDF 下載過程中網路中斷，系統應能重試並從中斷處繼續
- 多張信用卡同一銀行：使用者可能在同一家銀行有多張信用卡，帳單可能合併或分開寄送，系統應能正確處理
- LLM 解析不確定：使用 LLM 解析帳單時結果可信度低，系統應標記為「需人工確認」並顯示原始 PDF 內容供比對

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST provide Gmail OAuth2 connection flow, requesting only read-only email permission
- **FR-002**: System MUST securely store OAuth2 credentials (access token, refresh token) and automatically refresh expired tokens
- **FR-003**: System MUST support searching Gmail for credit card statement emails using bank-specific search queries (sender address + keywords)
- **FR-004**: System MUST download PDF attachments from matched statement emails
- **FR-005**: System MUST decrypt password-protected PDF attachments using bank-specific password rules configured by the user
- **FR-006**: System MUST parse credit card statement PDFs to extract transaction details (date, merchant name, amount, transaction type)
- **FR-007**: System MUST support an extensible bank parser architecture where adding a new bank requires only implementing a parser module without modifying core logic
- **FR-008**: System MUST initially support at least 8 Taiwan banks: 中國信託, 台北富邦, 國泰世華, 星展, 匯豐, 華南, 玉山, 永豐
- **FR-009**: System MUST display a scan results page showing found statements with bank name, billing period, transaction count, and total amount
- **FR-010**: System MUST allow users to preview individual statement transaction details before importing
- **FR-011**: System MUST suggest expense categories for each transaction based on merchant name keywords (reusing existing category suggestion logic)
- **FR-012**: System MUST allow users to modify suggested categories before confirming import
- **FR-013**: System MUST detect duplicate statements by matching billing period + bank, preventing the same statement from being processed twice
- **FR-014**: System MUST detect duplicate transactions within a statement by matching date + amount + existing transactions, warning users before import
- **FR-015**: System MUST execute statement import as an atomic operation (all transactions succeed or all are rolled back)
- **FR-016**: System MUST create each imported transaction as a double-entry record (credit card liability account to expense account)
- **FR-017**: System MUST allow users to configure which banks to scan and their PDF decryption passwords
- **FR-018**: System MUST store PDF decryption passwords in encrypted form, never in plaintext
- **FR-019**: System MUST support scheduled automatic scanning (configurable frequency: daily, weekly)
- **FR-020**: System MUST notify users when automatic scan finds new statements pending confirmation
- **FR-021**: System MUST maintain a scan history log showing scan time, statements found, and import status
- **FR-022**: System MUST allow users to set a scan start date to limit how far back the initial scan searches
- **FR-023**: System MUST allow users to disconnect Gmail and remove all stored credentials
- **FR-024**: System MUST support using LLM assistance for parsing complex or non-standard PDF formats, with the ability to flag low-confidence results for manual review

### Data Integrity Requirements _(required for features modifying financial data)_

- **DI-001**: System MUST validate all parsed amounts from PDF (format, range, precision - max 2 decimal places for TWD)
- **DI-002**: System MUST create audit trail entries for all imported transactions, marking source as "gmail-statement-import" with reference to email message ID and bank name
- **DI-003**: System MUST enforce double-entry bookkeeping for all imported transactions (debit from credit card account = credit to expense account)
- **DI-004**: System MUST require explicit user confirmation before executing import (no auto-import without review)
- **DI-005**: System MUST preserve original transaction dates from the bank statement
- **DI-006**: System MUST NOT allow partial imports — atomic operation ensures all or nothing
- **DI-007**: System MUST retain original PDF files (or references) for audit purposes until user explicitly deletes them

### Key Entities _(include if feature involves data)_

- **GmailConnection**: Represents a user's Gmail OAuth2 connection — stores encrypted credentials, connected email address, connection status, last scan timestamp
- **BankParserConfig**: Represents a supported bank's configuration — email search query, PDF password rule description, parser identifier, enabled/disabled status per user
- **StatementScanJob**: Represents a single scan execution — scan trigger type (manual/scheduled), start time, completion time, status, statements found count
- **DiscoveredStatement**: Represents a credit card statement found during scanning — bank name, billing period, email message ID, PDF attachment reference, parse status, import status
- **ParsedStatementTransaction**: Represents a single transaction extracted from a statement — date, merchant name, amount, currency, suggested category, confidence score
- **UserBankSetting**: Represents user-specific bank configuration — which banks are enabled, encrypted PDF password per bank, associated credit card account in the ledger

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Users can connect Gmail and complete their first manual scan in under 3 minutes from starting the setup
- **SC-002**: System correctly identifies and downloads credit card statement emails for all 8 supported banks with 95% accuracy (no missed statements, less than 5% false positives)
- **SC-003**: PDF decryption succeeds for 98% of correctly-configured bank statements
- **SC-004**: Statement parsing extracts transaction details (date, merchant, amount) with 90% accuracy across all supported banks
- **SC-005**: 70% of suggested expense categories are accepted by users without modification
- **SC-006**: Users can review and confirm import of a monthly statement (typically 20-50 transactions) in under 2 minutes
- **SC-007**: Zero data corruption incidents — all imports maintain double-entry balance integrity
- **SC-008**: Adding support for a new bank requires implementing only the bank-specific parser module, with no changes to the scanning, downloading, or importing pipeline
- **SC-009**: Duplicate detection prevents 100% of same-statement re-imports

## Assumptions

- Users will have their credit card statements delivered to Gmail as PDF email attachments (not as inline HTML or links to external portals)
- Each supported bank has a consistent email sender address and subject line pattern that can be reliably matched via Gmail search
- PDF decryption passwords follow documented conventions per bank (typically Taiwan national ID number with first letter capitalized); users who have customized their passwords can manually enter the correct one
- The system runs locally or on a trusted server — OAuth2 credentials and PDF passwords are stored locally, not transmitted to third-party services (privacy by design)
- LLM-assisted parsing (when used) sends only extracted text content to the LLM API, not the raw PDF binary, to minimize data exposure
- Initial scan date defaults to 6 months ago to provide useful historical data without overwhelming the system
- The existing category suggestion engine from 006-data-import can be reused and extended for Gmail-imported transactions
- Each bank statement PDF follows a relatively stable format within the same bank; major format changes are infrequent (once per year or less)
- Users typically have 1-3 active credit cards across 1-3 banks, resulting in 1-3 statements per month per user

## Out of Scope

- Parsing bank statements from sources other than Gmail (e.g., Yahoo Mail, Outlook, direct bank portal downloads)
- Support for non-PDF statement formats (HTML email statements, OFX/QFX files)
- Automatic import without user confirmation (all imports require manual review and confirmation)
- Support for banks outside of Taiwan
- Real-time bank API integration (Open Banking APIs)
- Statement dispute or correction workflows
- Credit card payment tracking (only expense transactions from statements)
- Multi-user support for the same Gmail account
