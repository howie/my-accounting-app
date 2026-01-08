# API Contract: Transaction Service

**Date**: 2026-01-02 (Updated from 2025-11-22)
**Feature**: Core Accounting System
**Base Path**: `/api/v1/ledgers/{ledger_id}/transactions`

## Overview

This service manages transactions within a specific ledger. All transactions follow double-entry bookkeeping principles with from/to account pairs.

## Endpoints

### POST /api/v1/ledgers/{ledger_id}/transactions

Create a new transaction.

**Request**:

```json
{
  "date": "2026-01-02",
  "description": "Lunch at restaurant",
  "amount": 25.5,
  "from_account_id": "660e8400-e29b-41d4-a716-446655440001",
  "to_account_id": "660e8400-e29b-41d4-a716-446655440003",
  "transaction_type": "EXPENSE"
}
```

**Response** (201 Created):

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440001",
  "ledger_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2026-01-02",
  "description": "Lunch at restaurant",
  "amount": "25.50",
  "from_account_id": "660e8400-e29b-41d4-a716-446655440001",
  "to_account_id": "660e8400-e29b-41d4-a716-446655440003",
  "transaction_type": "EXPENSE",
  "created_at": "2026-01-02T12:00:00Z",
  "updated_at": "2026-01-02T12:00:00Z"
}
```

**Errors**:

- `400 Bad Request`: Invalid input (see validation rules below)
- `404 Not Found`: Ledger or referenced account does not exist
- `422 Unprocessable Entity`: Transaction type doesn't match account types

**Business Rules**:

- Amount must be > 0 (FR-002)
- from_account_id != to_account_id
- Transaction type must match account types:
  - EXPENSE: from Asset/Liability → to Expense
  - INCOME: from Income → to Asset/Liability
  - TRANSFER: from Asset/Liability → to Asset/Liability
- Zero-amount transactions require confirmation (FR-013, handled by frontend)

---

### GET /api/v1/ledgers/{ledger_id}/transactions

List transactions with filtering and pagination.

**Query Parameters**:

- `cursor` (optional): Pagination cursor from previous response
- `limit` (optional): Number of results (default: 50, max: 100)
- `from_date` (optional): Filter by start date (ISO 8601)
- `to_date` (optional): Filter by end date (ISO 8601)
- `account_id` (optional): Filter by account (from or to)
- `search` (optional): Search in description
- `type` (optional): Filter by transaction type

**Response** (200 OK):

```json
{
  "data": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440001",
      "date": "2026-01-02",
      "description": "Lunch at restaurant",
      "amount": "25.50",
      "from_account": {
        "id": "660e8400-e29b-41d4-a716-446655440001",
        "name": "Cash",
        "type": "ASSET"
      },
      "to_account": {
        "id": "660e8400-e29b-41d4-a716-446655440003",
        "name": "Food",
        "type": "EXPENSE"
      },
      "transaction_type": "EXPENSE"
    }
  ],
  "cursor": "eyJpZCI6Ijc3MGU4NDAwLWUyOWItNDFkNC1hNzE2LTQ0NjY1NTQ0MDAwMSJ9",
  "has_more": true
}
```

---

### GET /api/v1/ledgers/{ledger_id}/transactions/{transaction_id}

Retrieve a single transaction.

**Response** (200 OK):

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440001",
  "ledger_id": "550e8400-e29b-41d4-a716-446655440000",
  "date": "2026-01-02",
  "description": "Lunch at restaurant",
  "amount": "25.50",
  "from_account_id": "660e8400-e29b-41d4-a716-446655440001",
  "to_account_id": "660e8400-e29b-41d4-a716-446655440003",
  "transaction_type": "EXPENSE",
  "created_at": "2026-01-02T12:00:00Z",
  "updated_at": "2026-01-02T12:00:00Z"
}
```

**Errors**:

- `404 Not Found`: Transaction does not exist

---

### PUT /api/v1/ledgers/{ledger_id}/transactions/{transaction_id}

Update a transaction (full replacement).

**Request**:

```json
{
  "date": "2026-01-02",
  "description": "Dinner at restaurant",
  "amount": 45.0,
  "from_account_id": "660e8400-e29b-41d4-a716-446655440001",
  "to_account_id": "660e8400-e29b-41d4-a716-446655440003",
  "transaction_type": "EXPENSE"
}
```

**Response** (200 OK):

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440001",
  "date": "2026-01-02",
  "description": "Dinner at restaurant",
  "amount": "45.00",
  "from_account_id": "660e8400-e29b-41d4-a716-446655440001",
  "to_account_id": "660e8400-e29b-41d4-a716-446655440003",
  "transaction_type": "EXPENSE",
  "updated_at": "2026-01-02T14:00:00Z"
}
```

**Business Rules**:

- Same validation rules as creation
- Account balances are recalculated after update (FR-009)
- `updated_at` timestamp is set automatically

---

### DELETE /api/v1/ledgers/{ledger_id}/transactions/{transaction_id}

Delete a transaction.

**Response** (204 No Content)

**Errors**:

- `404 Not Found`: Transaction does not exist

**Business Rules**:

- Frontend must show confirmation dialog (DI-004)
- Account balances are recalculated after deletion (FR-009)

---

### DELETE /api/v1/ledgers/{ledger_id}/transactions

Bulk delete transactions.

**Request**:

```json
{
  "ids": [
    "770e8400-e29b-41d4-a716-446655440001",
    "770e8400-e29b-41d4-a716-446655440002"
  ]
}
```

**Response** (200 OK):

```json
{
  "deleted_count": 2
}
```

**Business Rules**:

- Frontend must show confirmation dialog (DI-004)
- All affected account balances are recalculated

---

## Data Transfer Objects

### TransactionCreate

```python
class TransactionCreate(SQLModel):
    date: date
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    transaction_type: TransactionType

    @field_validator('from_account_id', 'to_account_id')
    def accounts_must_differ(cls, v, info):
        if 'from_account_id' in info.data and v == info.data['from_account_id']:
            raise ValueError('from_account and to_account must be different')
        return v
```

### TransactionRead

```python
class TransactionRead(SQLModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    date: date
    description: str
    amount: Decimal
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    transaction_type: TransactionType
    created_at: datetime
    updated_at: datetime
```

### TransactionListItem

```python
class AccountSummary(SQLModel):
    id: uuid.UUID
    name: str
    type: AccountType

class TransactionListItem(SQLModel):
    id: uuid.UUID
    date: date
    description: str
    amount: Decimal
    from_account: AccountSummary
    to_account: AccountSummary
    transaction_type: TransactionType
```

### TransactionUpdate

```python
class TransactionUpdate(SQLModel):
    date: date
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0, max_digits=15, decimal_places=2)
    from_account_id: uuid.UUID
    to_account_id: uuid.UUID
    transaction_type: TransactionType
```

### PaginatedResponse

```python
class PaginatedTransactions(SQLModel):
    data: list[TransactionListItem]
    cursor: str | None
    has_more: bool
```

---

## Service Interface

```python
class TransactionService:
    async def create_transaction(
        self,
        ledger_id: UUID,
        data: TransactionCreate
    ) -> Transaction:
        """
        Create a new transaction.
        Validates account types match transaction type.
        Recalculates affected account balances.
        """
        ...

    async def get_transactions(
        self,
        ledger_id: UUID,
        cursor: str | None = None,
        limit: int = 50,
        filters: TransactionFilters | None = None
    ) -> PaginatedTransactions:
        """
        List transactions with pagination and filtering.
        Includes account details for display.
        """
        ...

    async def get_transaction(
        self,
        transaction_id: UUID,
        ledger_id: UUID
    ) -> Transaction | None:
        """Get a single transaction."""
        ...

    async def update_transaction(
        self,
        transaction_id: UUID,
        ledger_id: UUID,
        data: TransactionUpdate
    ) -> Transaction | None:
        """
        Update a transaction.
        Recalculates affected account balances.
        """
        ...

    async def delete_transaction(
        self,
        transaction_id: UUID,
        ledger_id: UUID
    ) -> bool:
        """
        Delete a transaction.
        Recalculates affected account balances.
        Returns True if deleted, False if not found.
        """
        ...

    async def bulk_delete(
        self,
        ledger_id: UUID,
        transaction_ids: list[UUID]
    ) -> int:
        """
        Delete multiple transactions.
        Returns count of deleted transactions.
        """
        ...

    def validate_transaction_type(
        self,
        from_account: Account,
        to_account: Account,
        transaction_type: TransactionType
    ) -> bool:
        """
        Validate that transaction type matches account types.
        Raises ValueError with details if invalid.
        """
        ...
```

---

## Transaction Type Validation Matrix

| Transaction Type | From Account Types | To Account Types |
| ---------------- | ------------------ | ---------------- |
| EXPENSE          | ASSET, LIABILITY   | EXPENSE          |
| INCOME           | INCOME             | ASSET, LIABILITY |
| TRANSFER         | ASSET, LIABILITY   | ASSET, LIABILITY |

Invalid combinations return `422 Unprocessable Entity` with details:

```json
{
  "error": {
    "code": "INVALID_TRANSACTION_TYPE",
    "message": "EXPENSE transactions must go from Asset/Liability to Expense account",
    "details": {
      "from_account_type": "INCOME",
      "to_account_type": "EXPENSE",
      "transaction_type": "EXPENSE"
    }
  }
}
```
