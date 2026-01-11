# Quickstart: 006-data-import

**Date**: 2026-01-09
**Feature**: 資料匯入功能

## Prerequisites

- 已完成 001-core-accounting 功能
- PostgreSQL 16 資料庫已啟動
- Backend 和 Frontend 開發環境已設定

## Quick Setup

### 1. 建立 Migration

```bash
cd backend

# 建立 migration 檔案
alembic revision --autogenerate -m "add_import_sessions"

# 執行 migration
alembic upgrade head
```

### 2. 建立 Model 檔案

```bash
# 建立 import_session model
touch backend/src/models/import_session.py
```

```python
# backend/src/models/import_session.py
"""ImportSession model for tracking import operations."""

import uuid
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import Column
from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel


class ImportStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ImportType(str, Enum):
    MYAB_CSV = "MYAB_CSV"
    CREDIT_CARD = "CREDIT_CARD"


class ImportSession(SQLModel, table=True):
    __tablename__ = "import_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", index=True)
    import_type: ImportType = Field(sa_column=Column(SAEnum(ImportType)))
    source_filename: str = Field(max_length=255)
    source_file_hash: str = Field(max_length=64)
    status: ImportStatus = Field(
        default=ImportStatus.PENDING,
        sa_column=Column(SAEnum(ImportStatus))
    )
    progress_current: int = Field(default=0)
    progress_total: int = Field(default=0)
    imported_count: int = Field(default=0)
    skipped_count: int = Field(default=0)
    error_count: int = Field(default=0)
    created_accounts_count: int = Field(default=0)
    error_message: str | None = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)

    ledger: "Ledger" = Relationship(back_populates="import_sessions")
```

### 3. 建立服務層

```bash
# 建立服務檔案
touch backend/src/services/csv_parser.py
touch backend/src/services/import_service.py
touch backend/src/services/category_suggester.py
```

### 4. 建立 API 路由

```bash
touch backend/src/api/import_routes.py
```

### 5. 建立前端頁面

```bash
# 建立 import 頁面
mkdir -p frontend/src/app/\[locale\]/ledgers/\[ledgerId\]/import
touch frontend/src/app/\[locale\]/ledgers/\[ledgerId\]/import/page.tsx

# 建立元件
mkdir -p frontend/src/components/import
touch frontend/src/components/import/ImportTypeSelector.tsx
touch frontend/src/components/import/CsvUploader.tsx
touch frontend/src/components/import/ImportPreview.tsx
touch frontend/src/components/import/AccountMapper.tsx
touch frontend/src/components/import/ImportConfirmation.tsx
```

### 6. 新增 i18n 翻譯

在 `frontend/messages/zh-TW.json` 和 `frontend/messages/en.json` 新增：

```json
{
  "import": {
    "title": "批次匯入",
    "selectType": "選擇匯入類型",
    "myabCsv": "MyAB CSV 匯入",
    "creditCard": "信用卡帳單匯入",
    "uploadFile": "上傳檔案",
    "preview": "預覽",
    "confirm": "確認匯入",
    "cancel": "取消",
    "processing": "處理中...",
    "success": "匯入成功",
    "failed": "匯入失敗",
    "duplicateWarning": "偵測到可能重複的交易",
    "newAccounts": "將建立以下新科目",
    "transactionCount": "共 {count} 筆交易",
    "dateRange": "日期範圍：{start} 至 {end}",
    "errors": {
      "fileTooLarge": "檔案大小超過 10MB 限制",
      "invalidFormat": "CSV 格式錯誤，請確認檔案格式",
      "encodingError": "檔案編碼錯誤，請使用 UTF-8 或 Big5 編碼"
    }
  }
}
```

## Development Workflow

### 1. 撰寫測試 (TDD)

```bash
# 建立測試檔案
mkdir -p backend/tests/unit
mkdir -p backend/tests/integration
mkdir -p backend/tests/fixtures/csv

touch backend/tests/unit/test_csv_parser.py
touch backend/tests/unit/test_category_suggester.py
touch backend/tests/integration/test_import_service.py
```

### 2. 準備測試用 CSV 檔案

在 `backend/tests/fixtures/csv/` 建立測試資料：

```csv
# myab_sample.csv
日期,交易類型,支出科目,收入科目,從科目,到科目,金額,明細,發票號碼
2024/01/01,支出,E-餐飲費,,A-現金,,50,午餐,
2024/01/05,收入,,I-薪資,,A-銀行帳戶,30000,月薪,
2024/01/10,轉帳,,,A-現金,A-銀行存款,10000,存錢,
```

### 3. 執行測試

```bash
# Backend 測試
cd backend
pytest tests/unit/test_csv_parser.py -v
pytest tests/integration/test_import_service.py -v

# Frontend 測試
cd frontend
npm run test
```

### 4. 啟動開發伺服器

```bash
# Terminal 1: Backend
cd backend
uvicorn src.main:app --reload

# Terminal 2: Frontend
cd frontend
npm run dev
```

## Key Implementation Notes

### CSV 解析注意事項

1. **編碼處理**: 嘗試 UTF-8，失敗則嘗試 Big5
2. **日期格式**: 支援 yyyy/MM/dd、yyyy-MM-dd、MM/dd/yyyy
3. **金額格式**: 移除千分位逗號，處理負號

### 原子操作實作

```python
async def execute_import(session: AsyncSession, data: ImportData):
    async with session.begin():
        # 所有操作在同一個 transaction 中
        await create_accounts(session, data.new_accounts)
        await create_transactions(session, data.transactions)
        await update_balances(session, data.transactions)
        await create_audit_log(session, data)
        # 自動 commit，任何錯誤自動 rollback
```

### 重複偵測演算法

```python
def find_duplicates(new_txs, existing_txs):
    existing_keys = {
        (tx.date, tx.amount, tx.from_account_id, tx.to_account_id)
        for tx in existing_txs
    }
    return [
        tx for tx in new_txs
        if (tx.date, tx.amount, tx.from_account_id, tx.to_account_id) in existing_keys
    ]
```

## Verification Checklist

- [x] Migration 成功執行
- [x] `POST /api/ledgers/{id}/import/preview` 回傳正確預覽
- [x] `POST /api/ledgers/{id}/import/execute` 成功匯入交易
- [x] 重複偵測正確警告
- [x] 新科目自動建立
- [x] Audit log 正確記錄
- [x] 前端上傳介面運作正常
- [x] 進度條正確顯示
- [x] i18n 翻譯完整
