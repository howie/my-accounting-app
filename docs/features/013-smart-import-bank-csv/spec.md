# Feature Specification: 銀行對帳單 CSV 匯入（Per-Bank Adapter 架構）

**Feature Branch**: `013-smart-import-bank-csv`
**Created**: 2026-02-24
**Status**: Complete（核心實作已完成）
**Input**: 擴充 006-data-import 已有的批次匯入功能，新增銀行活期/存款帳戶對帳單匯入，採 per-bank adapter 設計

---

## Background

006-data-import 已支援「MyAB CSV」與「信用卡帳單」兩種格式。本 feature 延伸支援**銀行活期存款對帳單**，由於每家銀行 CSV 格式差異大（欄位順序、金額格式、日期格式、編碼、標題行結構各異），採 **per-bank adapter** 架構：每家銀行有獨立的 config dataclass，易於新增與維護。

---

## 關鍵差異：信用卡 vs 銀行對帳單

| 面向      | 信用卡（CREDIT_CARD）    | 銀行對帳單（BANK_STATEMENT）                                         |
| --------- | ------------------------ | -------------------------------------------------------------------- |
| 帳戶類型  | LIABILITY                | ASSET（銀行存款帳戶）                                                |
| 交易方向  | 單向（支出）             | 雙向（出帳 + 入帳）                                                  |
| 金額欄    | 單一欄（正數=支出）      | 提款欄 + 存款欄，或帶正負號單一欄                                    |
| from / to | from=信用卡, to=支出科目 | 出帳：from=銀行帳戶, to=支出科目<br>入帳：from=收入科目, to=銀行帳戶 |

---

## Clarifications

### Session 2026-02-24

- Q: 初始支援哪幾家銀行？→ A: 5 家主要台灣銀行（國泰世華、中國信託、玉山、台新、富邦），欄位設定為估計值，需實際 CSV 樣本確認
- Q: 金額欄位如何處理？→ A: 支援兩種模式：(1) debit_column + credit_column 雙欄；(2) 帶正負號 amount_column 單欄
- Q: LLM 分類增強是否套用？→ A: 是，BANK_STATEMENT 同 CREDIT_CARD 一樣進 LLM 增強，但同時查詢 EXPENSE 和 INCOME 帳戶
- Q: 格式文件要放哪？→ A: `docs/integration/import-bank/`，作為 adapter 實作的規格參考

---

## User Scenarios & Testing

### User Story 1 - 銀行活期帳戶對帳單匯入 (Priority: P1)

使用者從銀行網銀下載活期存款對帳單 CSV，想要快速匯入所有出帳（支出）和入帳（收入）記錄。系統解析 CSV 後自動辨識每筆為出帳或入帳，分別建議支出/收入科目，讓使用者預覽後確認匯入。

**Why this priority**: 活期帳戶是日常資金流動的核心，手動記帳負擔最高，匯入功能能大幅降低記帳門檻。

**Independent Test**: 可獨立測試 - 準備一個含出帳和入帳的活期帳戶 CSV，上傳後驗證系統正確分類每筆交易方向並建立預覽。

**Acceptance Scenarios**:

1. **Given** 使用者選擇「銀行對帳單」匯入類型並選擇銀行, **When** 上傳對應格式的 CSV, **Then** 系統正確解析每筆交易的日期、描述、金額和方向（出帳/入帳）
2. **Given** 系統解析到出帳記錄, **When** 顯示預覽時, **Then** 交易類型為 EXPENSE，from=銀行帳戶（ASSET），to=建議支出科目
3. **Given** 系統解析到入帳記錄, **When** 顯示預覽時, **Then** 交易類型為 INCOME，from=其他收入（INCOME），to=銀行帳戶（ASSET）
4. **Given** 同一行同時有出帳和入帳金額（邊界情況）, **When** 解析時, **Then** 分別建立兩筆獨立交易
5. **Given** 使用者確認匯入, **When** 執行後, **Then** 系統正確建立雙分錄交易，銀行帳戶餘額正確反映

---

### User Story 2 - 前端選擇銀行對帳單類型 (Priority: P1)

使用者在匯入頁面選擇「銀行對帳單」後，看到銀行選單（顯示支援活期帳戶匯入的銀行清單），與信用卡帳單的銀行選單分開。

**Independent Test**: 切換匯入類型至「銀行對帳單」，驗證銀行下拉顯示的是活期帳戶設定（如「國泰世華.活期存款」），而非信用卡設定。

**Acceptance Scenarios**:

1. **Given** 使用者在匯入頁面, **When** 選擇「銀行對帳單」類型, **Then** 顯示「選擇銀行」下拉，列出支援銀行對帳單的銀行
2. **Given** 使用者選擇銀行對帳單的銀行後, **When** 上傳 CSV, **Then** 系統使用對應的 BankStatementConfig 解析
3. **Given** 使用者從「銀行對帳單」切換回「MyAB CSV」, **When** 切換後, **Then** 銀行選單消失，bank_code 清除

---

### User Story 3 - 格式文件維護 (Priority: P2)

開發者需要新增或更新某家銀行的對帳單格式設定。有完整的格式文件目錄 `docs/integration/import-bank/`，可查閱現有設定並依樣板新增。

**Independent Test**: 查閱 docs/integration/import-bank/ 下的文件，確認每家銀行有格式說明、欄位表格、設定範例。

**Acceptance Scenarios**:

1. **Given** 開發者要新增玉山銀行活期帳戶實際格式, **When** 查閱 docs/integration/import-bank/bank-statement/esun.md, **Then** 看到欄位樣板、待確認標記、取得樣本的說明
2. **Given** 開發者有實際 CSV 樣本, **When** 更新 docs/integration/import-bank/ 並修改 bank_configs.py, **Then** 系統即可解析該格式的對帳單

---

### Edge Cases

- **提款欄為空、存款欄有值**：正確識別為入帳（INCOME）
- **兩欄均為 0 或空**：跳過（頁首/合計行）
- **帶正負號單欄模式**：負數 → 出帳；正數 → 入帳
- **BOM**：同信用卡解析，自動移除 UTF-8 BOM
- **header_marker**：支援動態定位標題行（同 CreditCardCsvParser）
- **編碼自動偵測**：不指定 encoding 時使用 charset_normalizer
- **科目命名**：銀行帳戶名稱由 config 的 `bank_account_name` 決定（如「國泰世華.活期存款」），建立為 ASSET 型階層帳戶

---

## Requirements

### Functional Requirements

- **FR-001**: System MUST add `BANK_STATEMENT` as a new `ImportType` enum value
- **FR-002**: System MUST provide `BankStatementConfig` dataclass with debit/credit/amount column configuration
- **FR-003**: System MUST implement `BankStatementCsvParser` supporting dual-column (debit+credit) and single signed-amount modes
- **FR-004**: System MUST create EXPENSE transactions for debit rows: from=bank ASSET account, to=expense category
- **FR-005**: System MUST create INCOME transactions for credit rows: from=income category, to=bank ASSET account
- **FR-006**: System MUST skip rows where both debit and credit are zero (summary/header rows)
- **FR-007**: System MUST apply LLM category enhancement to EXPENSE transactions in BANK_STATEMENT imports
- **FR-008**: System MUST support `GET /import/banks?statement_type=BANK_STATEMENT` returning bank statement configs
- **FR-009**: System MUST maintain backwards compatibility: `GET /import/banks` (without query param) still returns credit card configs
- **FR-010**: System MUST persist `bank_code` in ImportSession for BANK_STATEMENT imports (same as CREDIT_CARD)
- **FR-011**: Frontend MUST add "銀行對帳單" option to import type selector
- **FR-012**: Frontend BankSelector MUST fetch different bank list based on `statementType` prop
- **FR-013**: System MUST provide format documentation in `docs/integration/import-bank/` for all supported banks

### Data Integrity Requirements

- **DI-001**: Bank statement ASSET accounts MUST be created as hierarchical accounts matching `bank_account_name` segments
- **DI-002**: All BANK_STATEMENT imports MUST maintain double-entry bookkeeping (debits = credits)
- **DI-003**: Imported transactions MUST be atomic - all succeed or all rolled back
- **DI-004**: Bank account path MUST use ASSET type, NOT LIABILITY (unlike credit cards)

### Key Entities

- **BankStatementConfig**: Per-bank adapter config with date/description/debit/credit/amount column indices, encoding, skip_rows, header_marker
- **BANK_STATEMENT_CONFIGS**: Dict mapping bank code → BankStatementConfig (5 banks initially)
- **BankStatementCsvParser**: Parser class extending CsvParser base, produces ParsedTransaction with ASSET-typed bank account paths

---

## Success Criteria

- **SC-001**: `GET /import/banks?statement_type=BANK_STATEMENT` returns 5 banks
- **SC-002**: `GET /import/banks` (no param) still returns credit card configs (backwards compatible)
- **SC-003**: Upload a test CSV with debit/credit columns → preview shows EXPENSE and INCOME transactions correctly
- **SC-004**: EXPENSE rows: from=BankASET, to=支出科目；INCOME rows: from=其他收入, to=BankASET
- **SC-005**: Execute import → transactions created, hierarchical accounts auto-created
- **SC-006**: Import history shows `BANK_STATEMENT` type correctly

---

## Assumptions

- 5 家銀行初始設定為估計值，實際欄位順序需實際 CSV 樣本確認後更新
- 銀行對帳單的入帳預設 from_account 為「其他收入」，使用者可在科目對應步驟調整
- 每家銀行對帳單（活期）欄位模式為 debit+credit 雙欄，實際確認後若有不同可切換為 amount_column 模式
- 格式文件 `docs/integration/import-bank/` 隨實際 CSV 樣本到位後逐步更新

---

## Out of Scope

- 自動偵測哪家銀行格式（仍由使用者選擇銀行）
- 信用卡繳款記錄（繳款到活期帳戶的 Transfer 交易）
- 定期存款、外幣帳戶等其他帳戶類型
- 即時連接銀行 API
- 未在初始 5 家銀行清單中的銀行
