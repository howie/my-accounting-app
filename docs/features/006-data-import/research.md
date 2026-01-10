# Research: 006-data-import

**Date**: 2026-01-09
**Feature**: 資料匯入功能

## 1. MyAB CSV 格式規範

### Decision

採用 MyAB 標準 CSV 匯出格式，包含 9 個固定欄位。

### CSV 格式定義

```csv
日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
```

**欄位說明**：

| 欄位     | 說明                               | 範例       |
| -------- | ---------------------------------- | ---------- |
| 日期     | 交易日期，格式 yyyy/MM/dd          | 2024/01/01 |
| 交易類型 | 支出、收入、轉帳                   | 支出       |
| 支出科目 | 支出交易時填寫，格式：E-科目名     | E-餐飲費   |
| 收入科目 | 收入交易時填寫，格式：I-科目名     | I-薪資     |
| 從科目   | 轉帳來源或支出來源，格式：X-科目名 | A-現金     |
| 到科目   | 轉帳目標或收入目標，格式：X-科目名 | A-銀行帳戶 |
| 金額     | 正整數或小數                       | 50、30000  |
| 明細     | 交易說明                           | 午餐       |
| 發票號碼 | 選填                               | AB12345678 |

**科目前綴對應**：

| 前綴 | AccountType |
| ---- | ----------- |
| A-   | ASSET       |
| L-   | LIABILITY   |
| I-   | INCOME      |
| E-   | EXPENSE     |

### 交易類型解析規則

1. **支出** (EXPENSE)
   - 從科目 (from_account): 解析「從科目」欄位 (ASSET)
   - 到科目 (to_account): 解析「支出科目」欄位 (EXPENSE)

2. **收入** (INCOME)
   - 從科目 (from_account): 解析「收入科目」欄位 (INCOME)
   - 到科目 (to_account): 解析「到科目」欄位 (ASSET)

3. **轉帳** (TRANSFER)
   - 從科目 (from_account): 解析「從科目」欄位
   - 到科目 (to_account): 解析「到科目」欄位

### Rationale

- 此格式為 MyAB 官方匯出格式，經過多年使用驗證
- 所有欄位位置固定，解析邏輯簡單
- 科目前綴可直接對應到系統的 AccountType enum

### Alternatives Considered

- **JSON 格式**: 較容易解析但 MyAB 不支援
- **自定義 CSV 格式**: 會與現有 MyAB 使用者不相容

---

## 2. 信用卡帳單 CSV 格式

### Decision

初期支援 5 家台灣主要銀行的信用卡帳單 CSV 格式：國泰世華、中國信託、玉山、台新、富邦。

### 共通欄位設計

透過銀行別設定檔定義各銀行 CSV 的欄位對應：

```python
@dataclass
class BankCsvConfig:
    bank_code: str          # 銀行代碼
    bank_name: str          # 銀行名稱
    date_column: int        # 日期欄位索引
    date_format: str        # 日期格式
    description_column: int # 商店/摘要欄位索引
    amount_column: int      # 金額欄位索引
    skip_rows: int          # 跳過的標題行數
    encoding: str           # 檔案編碼 (UTF-8 or Big5)
```

### 銀行格式設定（初始設定，實際需測試驗證）

| 銀行     | date_column | date_format | description_column | amount_column | encoding |
| -------- | ----------- | ----------- | ------------------ | ------------- | -------- |
| 國泰世華 | 0           | %Y/%m/%d    | 2                  | 3             | Big5     |
| 中國信託 | 0           | %Y-%m-%d    | 1                  | 2             | UTF-8    |
| 玉山銀行 | 0           | %Y/%m/%d    | 1                  | 2             | UTF-8    |
| 台新銀行 | 0           | %Y/%m/%d    | 2                  | 3             | Big5     |
| 富邦銀行 | 0           | %Y-%m-%d    | 1                  | 2             | UTF-8    |

**注意**：上述設定為初始假設，需取得實際帳單樣本後驗證調整。

### 信用卡交易轉換規則

所有信用卡交易都是「支出」類型：

- **from_account**: 使用者選擇的信用卡科目 (LIABILITY)
- **to_account**: 系統建議的支出科目 (EXPENSE)

### Rationale

- 使用設定檔模式，新增銀行只需新增設定，無需修改程式碼
- 初期支援 5 家銀行涵蓋台灣約 70% 信用卡市場
- 可依使用者回饋逐步擴充支援

### Alternatives Considered

- **通用欄位對應介面**: 讓使用者自行對應欄位，但操作複雜
- **固定格式**: 要求銀行提供統一格式，不切實際

---

## 3. 支出科目自動分類規則

### Decision

使用關鍵字比對進行支出科目建議，初期採用簡單的字串匹配。

### 分類規則設計

```python
CATEGORY_KEYWORDS = {
    "餐飲費": ["餐廳", "食品", "飲料", "咖啡", "麵包", "便當", "小吃"],
    "交通費": ["加油", "停車", "高鐵", "台鐵", "捷運", "Uber", "計程車"],
    "日用品": ["全聯", "家樂福", "好市多", "大潤發", "屈臣氏", "康是美"],
    "網路購物": ["蝦皮", "PChome", "momo", "博客來", "Amazon"],
    "娛樂費": ["電影", "KTV", "遊戲", "Netflix", "Spotify"],
    "醫療費": ["診所", "醫院", "藥局", "藥房"],
    "教育費": ["書店", "補習", "課程", "學費"],
}
```

### 匹配邏輯

1. 將信用卡交易的商店/摘要欄位進行關鍵字比對
2. 找到匹配的第一個分類作為建議
3. 若無匹配，預設為「其他支出」
4. 使用者可在預覽階段調整

### Rationale

- 簡單字串匹配足以處理大部分常見商家
- 規則可透過設定檔擴充，無需修改程式碼
- 70% 準確率的目標可達成

### Alternatives Considered

- **機器學習分類**: 需要大量訓練資料，初期不適用
- **商店代碼對應**: 需要維護大量商店資料庫

---

## 4. 重複交易偵測演算法

### Decision

使用「同日期 + 同金額 + 同科目」作為重複判斷條件。

### 演算法設計

```python
def find_duplicates(
    new_transactions: list[Transaction],
    existing_transactions: list[Transaction]
) -> list[DuplicateWarning]:
    """
    比對新匯入交易與現有交易，找出可能重複的項目。
    """
    duplicates = []

    # 建立現有交易的索引 (date, amount, account_id) -> transaction
    existing_index = {}
    for tx in existing_transactions:
        key = (tx.date, tx.amount, tx.from_account_id, tx.to_account_id)
        existing_index.setdefault(key, []).append(tx)

    # 檢查新交易
    for new_tx in new_transactions:
        key = (new_tx.date, new_tx.amount, new_tx.from_account_id, new_tx.to_account_id)
        if key in existing_index:
            duplicates.append(DuplicateWarning(
                new_transaction=new_tx,
                existing_transactions=existing_index[key]
            ))

    return duplicates
```

### 效能考量

- 建立雜湊索引，O(n) 時間複雜度
- 對於 2000 筆交易匯入 + 30000 筆現有交易，應在 1 秒內完成

### Rationale

- 寬鬆比對避免漏報，寧可多警告
- 忽略備註差異，因為同一筆交易可能有不同描述

### Alternatives Considered

- **完全比對**: 包含備註，但可能漏報真正重複
- **模糊比對**: 日期±1天，但可能誤報

---

## 5. 原子操作實作策略

### Decision

使用資料庫交易 (Database Transaction) 確保原子性。

### 實作方式

```python
async def execute_import(
    session: AsyncSession,
    import_data: ImportData
) -> ImportResult:
    """
    執行匯入操作，確保原子性。
    任何錯誤都會 rollback 整個操作。
    """
    try:
        # 開始交易
        async with session.begin():
            # 1. 建立新科目（如需要）
            created_accounts = await create_new_accounts(session, import_data.new_accounts)

            # 2. 批次建立交易
            transactions = await create_transactions(session, import_data.transactions)

            # 3. 更新科目餘額
            await update_account_balances(session, transactions)

            # 4. 建立 audit log
            await create_audit_log(session, import_data)

            # 交易自動 commit

        return ImportResult(success=True, count=len(transactions))

    except Exception as e:
        # 交易自動 rollback
        raise ImportError(f"匯入失敗: {str(e)}")
```

### Rationale

- SQLAlchemy/SQLModel 原生支援 async transaction
- PostgreSQL 提供強一致性保證
- 無需額外的補償機制

### Alternatives Considered

- **Saga Pattern**: 對於跨服務操作有用，但本功能為單一服務
- **兩階段提交**: 過度複雜

---

## 6. 檔案上傳與解析流程

### Decision

採用前端上傳 → 後端解析 → 回傳預覽 → 前端確認 → 後端執行的流程。

### 流程設計

```
┌─────────┐    ┌─────────┐    ┌──────────┐
│ Frontend │───▶│ Backend │───▶│ Database │
└─────────┘    └─────────┘    └──────────┘

1. [Frontend] 選擇檔案，檢查大小 (≤10MB)
2. [Frontend] POST /api/import/preview (multipart/form-data)
3. [Backend]  解析 CSV，驗證格式
4. [Backend]  偵測重複交易
5. [Backend]  回傳預覽資料 (transactions, duplicates, new_accounts)
6. [Frontend] 顯示預覽，讓使用者調整科目對應
7. [Frontend] POST /api/import/execute (JSON payload)
8. [Backend]  執行匯入（原子操作）
9. [Backend]  回傳結果摘要
```

### API 設計

```
POST /api/ledgers/{ledger_id}/import/preview
Content-Type: multipart/form-data

Response: ImportPreview {
  total_count: int
  date_range: { start: date, end: date }
  transactions: Transaction[]
  duplicates: DuplicateWarning[]
  new_accounts: NewAccount[]
  account_mappings: AccountMapping[]
}

POST /api/ledgers/{ledger_id}/import/execute
Content-Type: application/json

Request: ImportExecuteRequest {
  preview_id: uuid
  account_mappings: AccountMapping[]
  skip_duplicates: bool
}

Response: ImportResult {
  success: bool
  imported_count: int
  created_accounts: Account[]
  errors: ImportError[]
}
```

### Rationale

- 兩階段操作（preview → execute）符合使用者期望
- 預覽階段不寫入資料，確保安全
- preview_id 確保執行時使用的是同一份預覽資料

### Alternatives Considered

- **單一 API**: 上傳後直接匯入，但無法讓使用者確認
- **WebSocket**: 串流處理大檔案，但增加複雜度

---

## 7. 錯誤處理策略

### Decision

採用驗證前置 + 明確錯誤訊息的策略。

### 錯誤類型

```python
class ImportErrorType(Enum):
    FILE_TOO_LARGE = "FILE_TOO_LARGE"          # 檔案超過 10MB
    INVALID_FORMAT = "INVALID_FORMAT"          # CSV 格式錯誤
    ENCODING_ERROR = "ENCODING_ERROR"          # 編碼問題
    MISSING_COLUMN = "MISSING_COLUMN"          # 缺少必要欄位
    INVALID_DATE = "INVALID_DATE"              # 日期格式錯誤
    INVALID_AMOUNT = "INVALID_AMOUNT"          # 金額格式錯誤
    UNKNOWN_ACCOUNT_TYPE = "UNKNOWN_ACCOUNT_TYPE"  # 未知科目類型
    TRANSACTION_LIMIT = "TRANSACTION_LIMIT"    # 超過 2000 筆限制
```

### 錯誤訊息設計

每個錯誤類型對應清楚的使用者提示：

```python
ERROR_MESSAGES = {
    "FILE_TOO_LARGE": "檔案大小超過 10MB 限制，請分批匯入",
    "INVALID_FORMAT": "CSV 格式錯誤，請確認檔案為 MyAB 匯出格式",
    "ENCODING_ERROR": "檔案編碼錯誤，請嘗試以 UTF-8 或 Big5 格式儲存",
    "MISSING_COLUMN": "缺少必要欄位：{column_name}",
    "INVALID_DATE": "第 {row} 行日期格式錯誤：{value}",
    "INVALID_AMOUNT": "第 {row} 行金額格式錯誤：{value}",
    "UNKNOWN_ACCOUNT_TYPE": "第 {row} 行科目類型無法識別：{value}",
    "TRANSACTION_LIMIT": "交易筆數 ({count}) 超過 2000 筆限制",
}
```

### Rationale

- 使用者可自行理解並修正問題
- 包含行號便於定位錯誤
- 符合 SC-006 成功標準

---

## 8. 進度顯示策略

### Decision

使用輪詢 (Polling) 方式顯示匯入進度。

### 實作方式

對於大量資料（>1000 筆），匯入執行改為非同步：

```
1. POST /api/ledgers/{ledger_id}/import/execute
   Response: { job_id: uuid, status: "processing" }

2. GET /api/import/jobs/{job_id}
   Response: {
     status: "processing" | "completed" | "failed",
     progress: { current: 500, total: 2000 },
     result?: ImportResult
   }
```

### 前端實作

```typescript
const pollInterval = 500; // 0.5 秒
const maxPolls = 120; // 最多 60 秒

async function waitForCompletion(jobId: string) {
  for (let i = 0; i < maxPolls; i++) {
    const status = await fetchJobStatus(jobId);
    updateProgressBar(status.progress);

    if (status.status === "completed") return status.result;
    if (status.status === "failed") throw new Error(status.error);

    await sleep(pollInterval);
  }
  throw new Error("匯入逾時");
}
```

### Rationale

- 輪詢實作簡單，瀏覽器相容性好
- 0.5 秒更新頻率提供良好的使用者體驗
- 60 秒超時足夠處理 2000 筆交易

### Alternatives Considered

- **Server-Sent Events**: 較優雅但需額外設定
- **WebSocket**: 過度複雜

---

## Summary

所有技術決策已完成，無需進一步釐清。可進入 Phase 1 設計階段。
