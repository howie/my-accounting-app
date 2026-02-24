# Tasks: 銀行對帳單 CSV 匯入

**Input**: Design documents from `/docs/features/013-smart-import-bank-csv/`
**Prerequisites**: spec.md, plan.md
**Related**: 006-data-import（本 feature 為其延伸）

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 可並行（不同檔案，無依賴）
- **[Story]**: 對應 user story（US1/US2/US3）
- 已完成用 `[x]`，待辦用 `[ ]`

---

## Phase 0：格式文件

**目的**：建立 docs/integration/import-bank/ 格式規格，供 adapter 實作與未來維護參考

- [x] T001 建立 docs/integration/import-bank/README.md（總覽、兩種匯入類型說明、如何新增銀行）
- [x] T002 [P] 建立 docs/integration/import-bank/credit-card/cathay.md（從 fixture 提取，已知格式）
- [x] T003 [P] 建立 docs/integration/import-bank/credit-card/ctbc.md（從 fixture 提取，已知格式）
- [x] T004 [P] 建立 docs/integration/import-bank/credit-card/esun.md（待樣本，提供樣板）
- [x] T005 [P] 建立 docs/integration/import-bank/credit-card/taishin.md（待樣本，提供樣板）
- [x] T006 [P] 建立 docs/integration/import-bank/credit-card/fubon.md（待樣本，提供樣板）
- [x] T007 [P] 建立 docs/integration/import-bank/bank-statement/cathay.md（待樣本）
- [x] T008 [P] 建立 docs/integration/import-bank/bank-statement/ctbc.md（待樣本）
- [x] T009 [P] 建立 docs/integration/import-bank/bank-statement/esun.md（待樣本）
- [x] T010 [P] 建立 docs/integration/import-bank/bank-statement/taishin.md（待樣本）
- [x] T011 [P] 建立 docs/integration/import-bank/bank-statement/fubon.md（待樣本）

**Checkpoint**: 格式文件目錄建立完成。

---

## Phase 1：後端 Schema 與 Config

- [x] T012 [US1] 在 backend/src/schemas/data_import.py 新增 `ImportType.BANK_STATEMENT`
- [x] T013 [P] [US1] 在 backend/src/services/bank_configs.py 新增 `BankStatementConfig` dataclass
- [x] T014 [US1] 在 backend/src/services/bank_configs.py 建立 `BANK_STATEMENT_CONFIGS`（5 家銀行初始設定）
- [x] T015 [US1] 在 backend/src/services/bank_configs.py 新增 `get_supported_bank_statement_banks()` 和 `get_bank_statement_config()` 函式

**Checkpoint**: Schema 和 config 完成，可開始實作 parser。

---

## Phase 2：後端 Parser

- [x] T016 [US1] 在 backend/src/services/csv_parser.py 新增 `BankStatementCsvParser` 類別，繼承 `CsvParser`
  - `_find_data_start_row()` 支援 header_marker 動態定位
  - `_parse_amount()` 工具方法
  - `parse()` 主方法：支援 debit+credit 雙欄 及 amount 單欄
  - 出帳 → EXPENSE（from=BankASET, to=支出科目）
  - 入帳 → INCOME（from=其他收入, to=BankASET）
  - 跳過 debit=0 且 credit=0 的行
  - 使用 CategorySuggester 對出帳描述建議分類

**Checkpoint**: Parser 完成，可手動測試解析結果。

---

## Phase 3：後端 API 路由

- [x] T017 [US1] 更新 backend/src/api/routes/import_routes.py 的 `create_import_preview`：
  - 加入 `elif import_type == ImportType.BANK_STATEMENT` 分支
  - LLM 增強擴展：BANK_STATEMENT 同 CREDIT_CARD 一起套用，查詢 EXPENSE + INCOME 帳戶
  - ImportSession.bank_code 在 BANK_STATEMENT 時也保存
- [x] T018 [US1] 更新 `execute_import`：加入 BANK_STATEMENT 分支使用 BankStatementCsvParser
- [x] T019 [US2] 更新 `GET /import/banks`：新增 `statement_type` query 參數，BANK_STATEMENT 時回傳活期帳戶銀行清單，預設向下相容

**Checkpoint**: 後端 API 完整支援，可用 curl/httpie 手動測試。

---

## Phase 4：前端

- [x] T020 [P] [US2] 在 frontend/src/lib/api/import.ts 新增 `ImportType.BANK_STATEMENT`，更新 `getBanks(statementType)` 參數
- [x] T021 [US2] 更新 frontend/src/components/import/FileUploader.tsx：
  - 計算 `requiresBankCode`（CREDIT_CARD 或 BANK_STATEMENT）
  - `handleImportTypeChange`：切換到 MYAB_CSV 才清 bankCode
  - 新增「銀行對帳單」選項
  - BankSelector 改傳 `statementType={importType}`
  - 統一用 `requiresBankCode` 取代硬寫的 CREDIT_CARD 條件
- [x] T022 [US2] 更新 frontend/src/components/import/BankSelector.tsx：
  - 新增 `statementType?: string` prop
  - `getBanks(statementType)` 傳入 statementType
  - useEffect deps 加入 `statementType`

**Checkpoint**: 前端可切換三種匯入類型，BANK_STATEMENT 顯示活期帳戶銀行清單。

---

## Phase 5：翻譯

- [x] T023 [P] 在 frontend/messages/zh-TW.json 新增：
  - `"bankStatement": "銀行對帳單"`
  - `"bankStatementAutoCategory": "銀行交易已自動分類。點擊類別可修改。"`
- [x] T024 [P] 在 frontend/messages/en.json 新增：
  - `"bankStatement": "Bank Statement"`
  - `"bankStatementAutoCategory": "Bank transactions have been auto-categorized. Click to modify."`

---

## Phase 6：測試（待補）

> 注意：Phase 1-5 為快速實作，測試補於此 Phase

- [ ] T025 [P] [US1] 撰寫 BankStatementCsvParser unit tests in backend/tests/unit/test_csv_parser.py
  - 雙欄模式（debit+credit）：出帳、入帳、兩者皆 0（skip）
  - 帶正負號單欄模式
  - header_marker 動態定位
  - 空白列跳過
  - 金額格式（帶逗號、帶 $）
- [ ] T026 [P] [US1] 撰寫 BankStatementConfig unit tests in backend/tests/unit/test_bank_configs.py
  - `get_bank_statement_config()` 回傳正確設定
  - `get_supported_bank_statement_banks()` 回傳 5 家
- [ ] T027 [P] [US2] 撰寫 API integration tests in backend/tests/integration/test_import_api.py
  - `GET /import/banks?statement_type=BANK_STATEMENT` → 5 家銀行
  - `GET /import/banks` → 信用卡清單（向下相容）
  - `POST /import/preview` with BANK_STATEMENT → 正確解析
- [ ] T028 建立 backend/tests/fixtures/csv/bankstatement_cathay.csv（測試樣本）
- [ ] T029 建立 backend/tests/fixtures/csv/bankstatement_ctbc.csv（測試樣本）

---

## Phase 7：實際銀行樣本驗證（持續進行）

> 取得各銀行實際 CSV 後更新格式文件與 config

- [ ] T030 取得國泰世華活期存款實際 CSV，更新 docs/integration/import-bank/bank-statement/cathay.md 並校正 BankStatementConfig
- [ ] T031 取得中國信託活期存款實際 CSV，更新文件並校正 config
- [ ] T032 取得玉山銀行活期存款實際 CSV，更新文件並校正 config
- [ ] T033 取得台新銀行活期存款實際 CSV，更新文件並校正 config
- [ ] T034 取得富邦銀行活期存款實際 CSV，更新文件並校正 config

---

## Dependencies & Execution Order

```
Phase 0（文件） → 可與 Phase 1 並行
Phase 1（Schema + Config） → Phase 2（Parser）
Phase 2（Parser） → Phase 3（API）、Phase 4（前端）
Phase 3 + 4 → 可並行
Phase 5（翻譯） → 可與 Phase 2 並行
Phase 6（測試） → 可在任何時間補充
Phase 7（樣本驗證） → 持續進行
```

---

## Summary

| Phase              | 任務          | 狀態        |
| ------------------ | ------------- | ----------- |
| 0. 格式文件        | T001-T011     | ✅ 完成     |
| 1. Schema + Config | T012-T015     | ✅ 完成     |
| 2. Parser          | T016          | ✅ 完成     |
| 3. API 路由        | T017-T019     | ✅ 完成     |
| 4. 前端            | T020-T022     | ✅ 完成     |
| 5. 翻譯            | T023-T024     | ✅ 完成     |
| 6. 測試            | T025-T029     | ⏳ 待補     |
| 7. 銀行樣本驗證    | T030-T034     | ⏳ 待樣本   |
| **核心實作**       | **T001-T024** | **✅ 完成** |

---

## 已知待改善事項

- **測試缺口**：BankStatementCsvParser 尚無 unit/integration tests，需補齊（T025-T029）
- **樣本未確認**：5 家銀行活期帳戶 config 均為估計值，取得實際 CSV 後需驗證欄位順序是否正確（T030-T034）
- **INCOME 分類**：入帳目前固定為「其他收入」，未來可加入針對收入描述的分類建議（如薪資、租金收入等）
- **Transfer 支援**：信用卡繳款（由活期帳戶出帳 → 轉入信用卡）目前被解析為 EXPENSE，未來可加入 Transfer 偵測邏輯
