# API Contract: Ledger Service

**Date**: 2026-01-02 (Updated from 2025-11-22)
**Feature**: Core Accounting System
**Base Path**: `/api/v1/ledgers`

## Overview

This service manages ledgers (account books) for users. Each ledger is an independent container for accounts and transactions.

## Endpoints

### POST /api/v1/ledgers

Create a new ledger with initial Cash and Equity accounts.

**Request**:
```json
{
  "name": "2024 Personal",
  "initial_balance": 10000.00
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "2024 Personal",
  "initial_balance": "10000.00",
  "created_at": "2026-01-02T10:00:00Z"
}
```

**Errors**:
- `400 Bad Request`: Invalid input (empty name, negative balance)
- `401 Unauthorized`: Not authenticated

**Business Rules**:
- On creation, system automatically creates:
  - "Cash" account (ASSET, is_system=true) with initial_balance
  - "Equity" account (ASSET, is_system=true)
  - Initial transaction: Equity → Cash for initial_balance amount

---

### GET /api/v1/ledgers

List all ledgers for the authenticated user.

**Response** (200 OK):
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "2024 Personal",
      "initial_balance": "10000.00",
      "created_at": "2026-01-02T10:00:00Z"
    }
  ]
}
```

---

### GET /api/v1/ledgers/{ledger_id}

Retrieve a single ledger by ID.

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "name": "2024 Personal",
  "initial_balance": "10000.00",
  "created_at": "2026-01-02T10:00:00Z"
}
```

**Errors**:
- `404 Not Found`: Ledger does not exist or belongs to another user

---

### PATCH /api/v1/ledgers/{ledger_id}

Update ledger name.

**Request**:
```json
{
  "name": "2024 Personal Budget"
}
```

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "2024 Personal Budget",
  "initial_balance": "10000.00",
  "created_at": "2026-01-02T10:00:00Z"
}
```

**Business Rules**:
- `initial_balance` cannot be modified after creation

---

### DELETE /api/v1/ledgers/{ledger_id}

Delete a ledger and all associated accounts/transactions.

**Response** (204 No Content)

**Errors**:
- `404 Not Found`: Ledger does not exist

**Business Rules**:
- This is a destructive operation; frontend must show confirmation dialog (DI-004)
- Deletes all associated accounts and transactions (cascade)

---

## Data Transfer Objects

### LedgerCreate
```python
class LedgerCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0, max_digits=15, decimal_places=2)
```

### LedgerRead
```python
class LedgerRead(SQLModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    initial_balance: Decimal
    created_at: datetime
```

### LedgerUpdate
```python
class LedgerUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
```

---

## Service Interface

```python
class LedgerService:
    async def create_ledger(
        self,
        user_id: UUID,
        data: LedgerCreate
    ) -> Ledger:
        """
        Create a new ledger with initial system accounts.

        Side effects:
        - Creates Cash account with initial_balance
        - Creates Equity account with 0 balance
        - Creates initial transaction from Equity to Cash
        """
        ...

    async def get_ledgers(self, user_id: UUID) -> list[Ledger]:
        """List all ledgers for a user."""
        ...

    async def get_ledger(self, ledger_id: UUID, user_id: UUID) -> Ledger | None:
        """Get a single ledger, ensuring ownership."""
        ...

    async def update_ledger(
        self,
        ledger_id: UUID,
        user_id: UUID,
        data: LedgerUpdate
    ) -> Ledger | None:
        """Update ledger name."""
        ...

    async def delete_ledger(self, ledger_id: UUID, user_id: UUID) -> bool:
        """
        Delete ledger and all associated data.
        Returns True if deleted, False if not found.
        """
        ...
```
