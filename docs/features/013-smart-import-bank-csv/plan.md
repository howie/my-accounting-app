# Implementation Plan: 銀行對帳單 CSV 匯入

**Feature**: 013-smart-import-bank-csv
**Created**: 2026-02-24
**Status**: Complete

---

## Architecture Overview

本 feature 在 006-data-import 既有框架上擴充，採 **per-bank adapter** 設計：

```
ImportType.BANK_STATEMENT
        ↓
BankStatementCsvParser(bank_code)
        ↓
BankStatementConfig（per-bank）
        ↓
ParsedTransaction（ASSET bank account）
        ↓
ImportService.execute_import（現有，不修改）
```

### 設計原則

1. **Open/Closed**：現有 CreditCardCsvParser 不修改，BankStatementCsvParser 獨立繼承 CsvParser
2. **Config-Driven**：每家銀行一個 BankStatementConfig dataclass entry，欄位修改無需改 parser 邏輯
3. **向下相容**：`GET /import/banks` 不加 `statement_type` 時維持回傳信用卡設定

---

## Step 0：格式文件（docs/integration/import-bank/）

**目的**：建立銀行 CSV 格式規格，作為 adapter 實作參考，並讓未來新增銀行有統一樣板

**產出**：

```
docs/integration/import-bank/
├── README.md
├── credit-card/
│   ├── cathay.md  ✅ 已知格式（有實際樣本）
│   ├── ctbc.md    ✅ 已知格式（有實際樣本）
│   ├── esun.md    ⚠️ 待樣本
│   ├── taishin.md ⚠️ 待樣本
│   └── fubon.md   ⚠️ 待樣本
└── bank-statement/
    ├── cathay.md  ⚠️ 待樣本
    ├── ctbc.md    ⚠️ 待樣本
    ├── esun.md    ⚠️ 待樣本
    ├── taishin.md ⚠️ 待樣本
    └── fubon.md   ⚠️ 待樣本
```

---

## Step 1：Schema（`backend/src/schemas/data_import.py`）

```python
class ImportType(str, Enum):
    MYAB_CSV = "MYAB_CSV"
    CREDIT_CARD = "CREDIT_CARD"
    BANK_STATEMENT = "BANK_STATEMENT"   # 新增
```

**影響範圍**：ImportSession.import_type、所有 import_type 判斷點

---

## Step 2：BankStatementConfig Adapter（`backend/src/services/bank_configs.py`）

**新增 dataclass**：

```python
@dataclass
class BankStatementConfig:
    code: str
    name: str
    bank_account_name: str    # e.g., "國泰世華.活期存款"
    date_column: int
    date_format: str
    description_column: int
    debit_column: int | None  # 提款欄（出帳）
    credit_column: int | None # 存款欄（入帳）
    amount_column: int | None # 帶正負號單欄
    balance_column: int | None = None
    skip_rows: int = 1
    encoding: str = "utf-8"
    header_marker: str | None = None
```

**5 家銀行初始設定**（debit_column=2, credit_column=3，需樣本確認）：

| 銀行    | 日期格式 | 編碼  |
| ------- | -------- | ----- |
| CATHAY  | %Y/%m/%d | utf-8 |
| CTBC    | %Y/%m/%d | utf-8 |
| ESUN    | %Y/%m/%d | utf-8 |
| TAISHIN | %Y/%m/%d | big5  |
| FUBON   | %Y-%m-%d | utf-8 |

**新增函式**：

- `get_supported_bank_statement_banks() -> list[BankStatementConfig]`
- `get_bank_statement_config(bank_code: str) -> BankStatementConfig | None`

---

## Step 3：BankStatementCsvParser（`backend/src/services/csv_parser.py`）

繼承 `CsvParser`，複用 `detect_encoding()` 和 BOM 處理邏輯。

**核心解析邏輯**：

```
for each data row:
    parse date → skip if invalid
    parse debit/credit amounts
    if debit > 0:
        → EXPENSE: from=bank(ASSET), to=expense_category
    if credit > 0:
        → INCOME: from=income_category, to=bank(ASSET)
    if both == 0:
        → skip (summary row)
```

**CategorySuggester**：對出帳（EXPENSE）描述做關鍵詞分類建議（同 CreditCardCsvParser）

---

## Step 4：API 路由（`backend/src/api/routes/import_routes.py`）

### Preview Endpoint 修改

```python
elif import_type == ImportType.BANK_STATEMENT:
    parser_bs = BankStatementCsvParser(bank_code)
    parsed_txs, validation_errors = parser_bs.parse(f)
```

### LLM 增強擴展

```python
if import_type in (ImportType.CREDIT_CARD, ImportType.BANK_STATEMENT) and parsed_txs:
    # BANK_STATEMENT 查詢 EXPENSE + INCOME 帳戶
    account_types = [EXPENSE, INCOME] if BANK_STATEMENT else [EXPENSE]
```

### Execute Endpoint 修改

```python
elif import_session.import_type == ImportType.BANK_STATEMENT:
    parser_bs = BankStatementCsvParser(import_session.bank_code)
    parsed_txs, _ = parser_bs.parse(f)
```

### GET /import/banks 修改

```python
@router.get("/import/banks")
async def list_supported_banks(
    statement_type: str = Query(default="CREDIT_CARD"),
) -> Any:
    if statement_type == "BANK_STATEMENT":
        banks = get_supported_bank_statement_banks()
    else:
        banks = get_supported_banks()  # 向下相容
```

---

## Step 5：前端 API（`frontend/src/lib/api/import.ts`）

```typescript
export enum ImportType {
  MYAB_CSV = 'MYAB_CSV',
  CREDIT_CARD = 'CREDIT_CARD',
  BANK_STATEMENT = 'BANK_STATEMENT',   // 新增
}

getBanks: async (statementType: string = 'CREDIT_CARD') => {
  return apiGet<{ banks: BankConfig[] }>(
    `/import/banks?statement_type=${statementType}`
  )
},
```

---

## Step 6：FileUploader（`frontend/src/components/import/FileUploader.tsx`）

```typescript
const requiresBankCode =
  importType === ImportType.CREDIT_CARD ||
  importType === ImportType.BANK_STATEMENT;

const handleImportTypeChange = (type: ImportType) => {
  setImportType(type);
  if (type === ImportType.MYAB_CSV) setBankCode(null);
};
```

- 新增 `<option value={ImportType.BANK_STATEMENT}>`
- BankSelector 改為 `{requiresBankCode && <BankSelector statementType={importType} />}`

---

## Step 7：BankSelector（`frontend/src/components/import/BankSelector.tsx`）

新增 `statementType?: string` prop（預設 `'CREDIT_CARD'`），傳給 `importApi.getBanks(statementType)`。useEffect 依賴加入 `statementType`，切換類型時自動重新 fetch 銀行清單。

---

## Step 8：翻譯

```json
// zh-TW.json
"bankStatement": "銀行對帳單",
"bankStatementAutoCategory": "銀行交易已自動分類。點擊類別可修改。"

// en.json
"bankStatement": "Bank Statement",
"bankStatementAutoCategory": "Bank transactions have been auto-categorized. Click to modify."
```

---

## 技術決策

| 決策             | 選擇                                        | 理由                                              |
| ---------------- | ------------------------------------------- | ------------------------------------------------- |
| 獨立 parser 類別 | BankStatementCsvParser                      | 與信用卡邏輯完全分離，避免 if/else 污染           |
| Config dataclass | BankStatementConfig（獨立於 BankCsvConfig） | 欄位不同（debit/credit vs amount），型別安全      |
| 入帳預設科目     | 「其他收入」                                | 通用 fallback，使用者可在科目對應步驟調整         |
| LLM 增強範圍     | EXPENSE 交易（出帳）                        | 入帳金額大多是薪資/轉帳，分類較固定，先套 EXPENSE |
| API 向下相容     | `statement_type=CREDIT_CARD`（預設）        | 現有前端不需修改即可繼續運作                      |

---

## 驗證 Checklist

- [ ] `GET /import/banks?statement_type=BANK_STATEMENT` → 回傳 5 家銀行
- [ ] `GET /import/banks` → 仍回傳信用卡設定（向下相容）
- [ ] 前端下拉出現「銀行對帳單」→ 選銀行後可上傳 CSV
- [ ] 上傳含提款/存款欄的測試 CSV → 預覽顯示 EXPENSE 和 INCOME 交易
- [ ] 出帳：from=銀行ASSET, to=支出科目；入帳：from=其他收入, to=銀行ASSET
- [ ] 執行匯入 → 交易正確建立，分層帳戶自動創建
- [ ] 匯入歷史顯示 `BANK_STATEMENT` 類型
- [ ] 切換匯入類型 CREDIT_CARD → BANK_STATEMENT → bank_code 保留；切換到 MYAB_CSV → bank_code 清除
