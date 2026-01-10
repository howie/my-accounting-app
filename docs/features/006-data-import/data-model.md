# Data Model: 006-data-import

**Date**: 2026-01-09
**Feature**: 資料匯入功能

## Overview

本功能新增一個資料庫實體 `ImportSession` 用於追蹤匯入操作歷史。其他實體（`ImportPreview`、`AccountMapping`、`CategorySuggestion`）為記憶體中的暫存結構，不需持久化。

---

## New Entities

### ImportSession

追蹤每次匯入操作的紀錄，用於 audit trail。

```python
class ImportStatus(str, Enum):
    """匯入狀態"""
    PENDING = "PENDING"       # 預覽中，尚未執行
    PROCESSING = "PROCESSING" # 正在處理
    COMPLETED = "COMPLETED"   # 成功完成
    FAILED = "FAILED"         # 失敗

class ImportType(str, Enum):
    """匯入類型"""
    MYAB_CSV = "MYAB_CSV"           # MyAB CSV 匯入
    CREDIT_CARD = "CREDIT_CARD"     # 信用卡帳單匯入

class ImportSession(SQLModel, table=True):
    """
    匯入操作記錄。
    用於追蹤每次匯入的來源、狀態和結果。
    """
    __tablename__ = "import_sessions"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    ledger_id: uuid.UUID = Field(foreign_key="ledgers.id", index=True)

    # 匯入資訊
    import_type: ImportType = Field(sa_column=Column(SAEnum(ImportType)))
    source_filename: str = Field(max_length=255)  # 原始檔名
    source_file_hash: str = Field(max_length=64)  # SHA-256 hash 用於重複偵測

    # 狀態追蹤
    status: ImportStatus = Field(
        default=ImportStatus.PENDING,
        sa_column=Column(SAEnum(ImportStatus))
    )
    progress_current: int = Field(default=0)
    progress_total: int = Field(default=0)

    # 結果統計
    imported_count: int = Field(default=0)        # 成功匯入筆數
    skipped_count: int = Field(default=0)         # 跳過筆數（重複）
    error_count: int = Field(default=0)           # 錯誤筆數
    created_accounts_count: int = Field(default=0) # 新建科目數

    # 錯誤訊息（如有）
    error_message: str | None = Field(default=None, max_length=1000)

    # 時間戳記
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    completed_at: datetime | None = Field(default=None)

    # Relationships
    ledger: "Ledger" = Relationship(back_populates="import_sessions")
```

### Entity Relationship

```
Ledger (1) ──────── (N) ImportSession
   │
   └── import_sessions: list[ImportSession]
```

需在 `Ledger` model 新增 relationship：

```python
# In ledger.py
class Ledger(SQLModel, table=True):
    # ... existing fields ...

    # New relationship
    import_sessions: list["ImportSession"] = Relationship(back_populates="ledger")
```

---

## In-Memory Data Structures

以下結構用於匯入流程中的資料傳遞，不需持久化。

### ParsedTransaction

解析 CSV 後的單筆交易資料：

```python
@dataclass
class ParsedTransaction:
    """CSV 解析後的交易資料"""
    row_number: int              # CSV 行號（用於錯誤提示）
    date: date
    transaction_type: TransactionType
    from_account_name: str       # 來源科目名稱（含前綴如 A-現金）
    to_account_name: str         # 目標科目名稱
    amount: Decimal
    description: str
    invoice_number: str | None = None

    # 解析後的科目 ID（經過對應後填入）
    from_account_id: uuid.UUID | None = None
    to_account_id: uuid.UUID | None = None
```

### AccountMapping

科目對應設定：

```python
@dataclass
class AccountMapping:
    """CSV 科目名稱到系統科目的對應"""
    csv_account_name: str         # CSV 中的科目名稱
    csv_account_type: AccountType # 從前綴解析的科目類型
    system_account_id: uuid.UUID | None  # 對應的系統科目 ID（None 表示需新建）
    create_new: bool = False      # 是否建立新科目
    suggested_name: str | None = None  # 建議的新科目名稱
```

### ImportPreview

預覽階段的完整資料：

```python
@dataclass
class ImportPreview:
    """匯入預覽資料"""
    session_id: uuid.UUID         # ImportSession ID
    total_count: int
    date_range: tuple[date, date]
    transactions: list[ParsedTransaction]
    duplicates: list[DuplicateWarning]
    account_mappings: list[AccountMapping]
    validation_errors: list[ValidationError]

    @property
    def is_valid(self) -> bool:
        """是否可以執行匯入"""
        return len(self.validation_errors) == 0
```

### DuplicateWarning

重複交易警告：

```python
@dataclass
class DuplicateWarning:
    """重複交易警告"""
    new_transaction: ParsedTransaction
    existing_transactions: list[Transaction]  # 可能有多筆相同
    similarity_reason: str  # "同日期+同金額+同科目"
```

### CategorySuggestion

信用卡支出分類建議：

```python
@dataclass
class CategorySuggestion:
    """支出科目分類建議"""
    description: str           # 商店/摘要
    suggested_account_id: uuid.UUID | None  # 建議的支出科目
    suggested_account_name: str
    confidence: float          # 信心度 0.0-1.0
    matched_keyword: str | None  # 匹配到的關鍵字
```

---

## Database Migration

### New Table: import_sessions

```sql
CREATE TABLE import_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ledger_id UUID NOT NULL REFERENCES ledgers(id),
    import_type VARCHAR(20) NOT NULL,
    source_filename VARCHAR(255) NOT NULL,
    source_file_hash VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    progress_current INTEGER NOT NULL DEFAULT 0,
    progress_total INTEGER NOT NULL DEFAULT 0,
    imported_count INTEGER NOT NULL DEFAULT 0,
    skipped_count INTEGER NOT NULL DEFAULT 0,
    error_count INTEGER NOT NULL DEFAULT 0,
    created_accounts_count INTEGER NOT NULL DEFAULT 0,
    error_message VARCHAR(1000),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_import_sessions_ledger ON import_sessions(ledger_id);
CREATE INDEX idx_import_sessions_status ON import_sessions(status);
CREATE INDEX idx_import_sessions_created ON import_sessions(created_at);
```

### Alembic Migration

```python
# alembic/versions/xxx_add_import_sessions.py

def upgrade():
    op.create_table(
        'import_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('ledger_id', sa.UUID(), nullable=False),
        sa.Column('import_type', sa.String(20), nullable=False),
        sa.Column('source_filename', sa.String(255), nullable=False),
        sa.Column('source_file_hash', sa.String(64), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='PENDING'),
        sa.Column('progress_current', sa.Integer(), nullable=False, default=0),
        sa.Column('progress_total', sa.Integer(), nullable=False, default=0),
        sa.Column('imported_count', sa.Integer(), nullable=False, default=0),
        sa.Column('skipped_count', sa.Integer(), nullable=False, default=0),
        sa.Column('error_count', sa.Integer(), nullable=False, default=0),
        sa.Column('created_accounts_count', sa.Integer(), nullable=False, default=0),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['ledger_id'], ['ledgers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_import_sessions_ledger', 'import_sessions', ['ledger_id'])
    op.create_index('idx_import_sessions_status', 'import_sessions', ['status'])
    op.create_index('idx_import_sessions_created', 'import_sessions', ['created_at'])


def downgrade():
    op.drop_index('idx_import_sessions_created')
    op.drop_index('idx_import_sessions_status')
    op.drop_index('idx_import_sessions_ledger')
    op.drop_table('import_sessions')
```

---

## Validation Rules

### ImportSession Validation

| Field            | Rule                              |
| ---------------- | --------------------------------- |
| source_filename  | 必填，最大 255 字元               |
| source_file_hash | 必填，SHA-256 格式 (64 hex chars) |
| imported_count   | >= 0                              |
| progress_current | <= progress_total                 |

### ParsedTransaction Validation

| Field             | Rule                     |
| ----------------- | ------------------------ |
| date              | 有效日期，不可為未來日期 |
| amount            | > 0, 最多 2 位小數       |
| from_account_name | 必填，需符合科目前綴格式 |
| to_account_name   | 必填，需符合科目前綴格式 |

---

## State Transitions

### ImportSession Status Flow

```
PENDING ──► PROCESSING ──► COMPLETED
    │            │
    │            └────────► FAILED
    │
    └────────────────────► FAILED (validation error)
```

| From       | To         | Trigger                      |
| ---------- | ---------- | ---------------------------- |
| PENDING    | PROCESSING | 使用者確認執行匯入           |
| PENDING    | FAILED     | 驗證失敗或使用者取消         |
| PROCESSING | COMPLETED  | 所有交易成功匯入             |
| PROCESSING | FAILED     | 任一交易匯入失敗（原子回滾） |
