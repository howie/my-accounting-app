# Research: LedgerOne Core Accounting System

**Feature**: 001-core-accounting
**Date**: 2026-01-02 (Updated from 2025-11-22)
**Status**: Complete

## Overview

本研究文件記錄 LedgerOne 核心記帳系統的技術決策、最佳實踐和架構選擇。

---

## 1. Architecture Decision: Next.js + FastAPI + PostgreSQL

### Decision

採用前後端分離架構：Next.js (Frontend) + Python FastAPI (Backend) + PostgreSQL (Database)

### Rationale

1. **關注點分離 (Separation of Concerns)**
   - Frontend 專注 UI/UX，Backend 專注業務邏輯
   - 便於獨立部署和擴展

2. **技術優勢互補**
   - Next.js 15: 優秀的 SSR、路由、開發體驗
   - Python/FastAPI: 強大的數據處理能力（Pandas、NumPy）、AI 整合潛力
   - PostgreSQL: 成熟的 ACID 支援、JSON 彈性、優秀的效能

3. **未來擴展性**
   - 獨立後端便於 AI 功能整合（004-ai-import feature）
   - API-first 設計支援多平台客戶端

### Alternatives Considered

| Alternative                      | Reason Rejected                    |
| -------------------------------- | ---------------------------------- |
| Full-stack Next.js (API Routes)  | 難以整合 Python 數據處理能力       |
| Django + HTMX                    | 前端互動性受限，不符合現代 UX 期望 |
| Electron + SQLite                | 難以支援未來的 Web/Mobile 擴展     |
| PyQt6 + SQLite (previous design) | 不符合新的 Web-first 架構需求      |

---

## 2. Double-Entry Bookkeeping Implementation

### Decision

採用簡化的雙重記帳模型：每筆交易有 `from_account_id` 和 `to_account_id`，金額永遠為正值

### Rationale

1. **直覺性**: from/to 模型比 debit/credit 更易理解
2. **簡化驗證**: 只需確認兩個帳戶不同且金額為正
3. **交易類型推導**:
   - Expense: Asset/Liability → Expense
   - Income: Income → Asset/Liability
   - Transfer: Asset/Liability → Asset/Liability

### Implementation Pattern

```python
class Transaction:
    from_account_id: UUID  # Credit side (source of funds)
    to_account_id: UUID    # Debit side (destination of funds)
    amount: Decimal        # Always positive

# Balance calculation
# For Asset/Liability: SUM(to_account) - SUM(from_account)
# For Income: SUM(from_account)
# For Expense: SUM(to_account)
```

### Best Practices

1. **永不直接修改 balance 欄位** - 只透過交易計算
2. **Balance 欄位為快取** - 可隨時由交易重新計算驗證
3. **交易金額不可為負** - 需要沖銷時使用反向交易

---

## 3. Decimal Precision and Rounding

### Decision

使用 `Decimal(15, 2)` 並採用 Banker's Rounding

### Rationale

1. **15,2 精度**: 支援最大 9,999,999,999,999.99 的金額
2. **Banker's Rounding (Round Half to Even)**:
   - 統計上無偏差
   - 會計軟體標準做法
   - Python `decimal` 模組原生支援

### Implementation

```python
from decimal import Decimal, ROUND_HALF_EVEN

def round_amount(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)

# Examples:
# 2.445 → 2.44 (rounds to even)
# 2.435 → 2.44 (rounds to even)
# 2.455 → 2.46 (rounds to even)
```

### Database Configuration

```sql
-- PostgreSQL
amount NUMERIC(15, 2) NOT NULL
```

---

## 4. API Design Patterns

### Decision

RESTful API with resource-based endpoints, cursor-based pagination

### Endpoint Structure

```
/api/v1/ledgers
/api/v1/ledgers/{ledger_id}/accounts
/api/v1/ledgers/{ledger_id}/transactions
```

### Pagination Strategy

Cursor-based pagination for transaction lists (better for real-time data)

```json
{
  "data": [...],
  "cursor": "eyJpZCI6MTAwfQ==",
  "has_more": true
}
```

### Error Response Format

```json
{
  "error": {
    "code": "UNBALANCED_TRANSACTION",
    "message": "Transaction debits must equal credits",
    "details": {
      "from_account": "...",
      "to_account": "..."
    }
  }
}
```

---

## 5. Frontend State Management

### Decision

Server State: TanStack Query (React Query)
Client State: React Context (minimal)

### Rationale

1. **TanStack Query 優勢**:
   - 自動快取和失效
   - 樂觀更新支援
   - 錯誤重試機制
   - DevTools 除錯

2. **避免過度工程**:
   - 不使用 Redux/Zustand（狀態簡單）
   - 利用 URL 作為單一事實來源

### Pattern

```typescript
// Queries
const { data: accounts } = useQuery({
  queryKey: ["accounts", ledgerId],
  queryFn: () => api.getAccounts(ledgerId),
});

// Mutations with optimistic updates
const createTransaction = useMutation({
  mutationFn: api.createTransaction,
  onMutate: async (newTx) => {
    // Optimistic update
  },
  onSettled: () => {
    queryClient.invalidateQueries(["transactions"]);
    queryClient.invalidateQueries(["accounts"]); // Refresh balances
  },
});
```

---

## 6. UI List Rendering for Large Datasets

### Context

The specification requires that the transaction list remains responsive with large datasets.

### Decision

Use TanStack Virtual for virtualized scrolling in React

### Rationale

1. Only renders visible rows (efficient DOM usage)
2. Smooth scrolling experience
3. Works seamlessly with TanStack Query

### Implementation

```typescript
import { useVirtualizer } from "@tanstack/react-virtual";

const rowVirtualizer = useVirtualizer({
  count: transactions.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 48, // row height
});
```

### Alternatives Considered

- **react-window**: Smaller bundle but less features
- **Full list rendering**: Not viable for 10k+ records

---

## 7. Database Migration Strategy

### Decision

Alembic for Python backend migrations

### Rationale

1. SQLModel/SQLAlchemy 原生整合
2. 版本控制遷移歷史
3. 可逆遷移支援

### Migration Workflow

```bash
# Generate migration
alembic revision --autogenerate -m "add_transactions_table"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 8. Testing Strategy

### Decision

分層測試：Unit → Integration → Contract → E2E

### Backend Testing (pytest)

```
tests/
├── unit/           # Service logic, pure functions
├── integration/    # Database operations, multi-service
└── contract/       # API endpoint contracts
```

### Frontend Testing (Vitest + Testing Library)

```
tests/
├── components/     # Component rendering, interactions
└── integration/    # API mocking, user flows
```

### Key Test Scenarios

1. **Double-entry validation**: Unbalanced transactions blocked
2. **Balance calculation**: Correct after CRUD operations
3. **System account protection**: Cash/Equity cannot be deleted
4. **Decimal precision**: Banker's rounding applied correctly

---

## 9. Development Environment

### Decision

Docker Compose for local development

### Services

```yaml
services:
  postgres:
    image: postgres:16
    ports: ["5432:5432"]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    depends_on: [postgres]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
```

### Alternative: Supabase

For hosted PostgreSQL with built-in auth (future feature consideration)

---

## 10. Security Considerations (MVP Scope)

### Decision

MVP focuses on single-user local deployment; auth deferred

### Current Scope

- No authentication (single-user assumption)
- CORS configured for local development
- Input validation via Pydantic

### Future Features

- User authentication (separate feature)
- API rate limiting
- HTTPS enforcement

---

## 11. Performance Considerations

### Database Indexing

```sql
-- Essential indexes
CREATE INDEX idx_transactions_ledger_date ON transactions(ledger_id, date DESC);
CREATE INDEX idx_transactions_from_account ON transactions(from_account_id);
CREATE INDEX idx_transactions_to_account ON transactions(to_account_id);
CREATE INDEX idx_accounts_ledger ON accounts(ledger_id);
```

### Balance Caching

- `accounts.balance` 為快取欄位
- 交易 CRUD 後觸發更新
- 可透過 SUM(transactions) 驗證

### Virtual Scrolling

Frontend 使用 TanStack Virtual 處理大量交易列表

---

## Summary

| Topic        | Decision                            | Key Rationale                                  |
| ------------ | ----------------------------------- | ---------------------------------------------- |
| Architecture | Next.js + FastAPI + PostgreSQL      | Separation of concerns, Python data processing |
| Double-Entry | from/to model with positive amounts | Intuitive, simple validation                   |
| Precision    | Decimal(15,2), Banker's Rounding    | Industry standard, unbiased                    |
| API          | RESTful, cursor pagination          | Standard patterns, real-time friendly          |
| State        | TanStack Query                      | Caching, optimistic updates                    |
| UI Lists     | TanStack Virtual                    | Efficient large list rendering                 |
| Migrations   | Alembic                             | SQLModel integration                           |
| Testing      | pytest + Vitest                     | Layered coverage                               |
| Dev Env      | Docker Compose                      | Reproducible setup                             |
