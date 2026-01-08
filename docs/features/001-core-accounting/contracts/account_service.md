# API Contract: Account Service

**Date**: 2026-01-02 (Updated from 2025-11-22)
**Feature**: Core Accounting System
**Base Path**: `/api/v1/ledgers/{ledger_id}/accounts`

## Overview

This service manages accounts (categories) within a specific ledger. Accounts are classified as Asset, Liability, Income, or Expense.

## Endpoints

### POST /api/v1/ledgers/{ledger_id}/accounts

Create a new account in the ledger.

**Request**:

```json
{
  "name": "Bank Account",
  "type": "ASSET"
}
```

**Response** (201 Created):

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "ledger_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Bank Account",
  "type": "ASSET",
  "balance": "0.00",
  "is_system": false,
  "created_at": "2026-01-02T10:00:00Z",
  "updated_at": "2026-01-02T10:00:00Z"
}
```

**Errors**:

- `400 Bad Request`: Invalid input (empty name, invalid type)
- `404 Not Found`: Ledger does not exist
- `409 Conflict`: Account with same name already exists in ledger

---

### GET /api/v1/ledgers/{ledger_id}/accounts

List all accounts for a ledger with calculated balances.

**Query Parameters**:

- `type` (optional): Filter by account type (ASSET, LIABILITY, INCOME, EXPENSE)

**Response** (200 OK):

```json
{
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Cash",
      "type": "ASSET",
      "balance": "10000.00",
      "is_system": true
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440002",
      "name": "Equity",
      "type": "ASSET",
      "balance": "-10000.00",
      "is_system": true
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440003",
      "name": "Food",
      "type": "EXPENSE",
      "balance": "0.00",
      "is_system": false
    }
  ]
}
```

---

### GET /api/v1/ledgers/{ledger_id}/accounts/{account_id}

Retrieve a single account with balance.

**Response** (200 OK):

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "ledger_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Cash",
  "type": "ASSET",
  "balance": "10000.00",
  "is_system": true,
  "created_at": "2026-01-02T10:00:00Z",
  "updated_at": "2026-01-02T10:00:00Z"
}
```

**Errors**:

- `404 Not Found`: Account does not exist

---

### PATCH /api/v1/ledgers/{ledger_id}/accounts/{account_id}

Update account name.

**Request**:

```json
{
  "name": "Savings Account"
}
```

**Response** (200 OK):

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Savings Account",
  "type": "ASSET",
  "balance": "10000.00",
  "is_system": false
}
```

**Errors**:

- `400 Bad Request`: Cannot rename system accounts (Cash, Equity)
- `409 Conflict`: Account with new name already exists

**Business Rules**:

- Account `type` cannot be changed after creation
- System accounts (is_system=true) cannot be renamed

---

### DELETE /api/v1/ledgers/{ledger_id}/accounts/{account_id}

Delete an account.

**Response** (204 No Content)

**Errors**:

- `400 Bad Request`: Cannot delete system accounts
- `409 Conflict`: Account has associated transactions
- `404 Not Found`: Account does not exist

**Business Rules**:

- System accounts (Cash, Equity) cannot be deleted (FR-004)
- Accounts with transactions cannot be deleted; delete transactions first

---

## Data Transfer Objects

### AccountCreate

```python
class AccountCreate(SQLModel):
    name: str = Field(min_length=1, max_length=100)
    type: AccountType
```

### AccountRead

```python
class AccountRead(SQLModel):
    id: uuid.UUID
    ledger_id: uuid.UUID
    name: str
    type: AccountType
    balance: Decimal
    is_system: bool
    created_at: datetime
    updated_at: datetime
```

### AccountListItem

```python
class AccountListItem(SQLModel):
    id: uuid.UUID
    name: str
    type: AccountType
    balance: Decimal
    is_system: bool
```

### AccountUpdate

```python
class AccountUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
```

---

## Service Interface

```python
class AccountService:
    async def create_account(
        self,
        ledger_id: UUID,
        data: AccountCreate
    ) -> Account:
        """Create a new account in the ledger."""
        ...

    async def get_accounts(
        self,
        ledger_id: UUID,
        type_filter: AccountType | None = None
    ) -> list[Account]:
        """
        List all accounts for a ledger.
        Balances are calculated from transactions.
        """
        ...

    async def get_account(
        self,
        account_id: UUID,
        ledger_id: UUID
    ) -> Account | None:
        """Get a single account with calculated balance."""
        ...

    async def update_account(
        self,
        account_id: UUID,
        ledger_id: UUID,
        data: AccountUpdate
    ) -> Account | None:
        """
        Update account name.
        Raises ValueError for system accounts.
        """
        ...

    async def delete_account(
        self,
        account_id: UUID,
        ledger_id: UUID
    ) -> bool:
        """
        Delete an account.
        Raises ValueError for system accounts or accounts with transactions.
        Returns True if deleted, False if not found.
        """
        ...

    async def calculate_balance(self, account_id: UUID) -> Decimal:
        """
        Calculate account balance from all transactions.
        Used for cache refresh and verification.
        """
        ...

    async def has_transactions(self, account_id: UUID) -> bool:
        """Check if account has any associated transactions."""
        ...
```

---

## Balance Calculation Rules

| Account Type | Balance Formula                     |
| ------------ | ----------------------------------- |
| ASSET        | SUM(to_account) - SUM(from_account) |
| LIABILITY    | SUM(to_account) - SUM(from_account) |
| INCOME       | SUM(from_account)                   |
| EXPENSE      | SUM(to_account)                     |

- Positive balance for ASSET = money you have
- Negative balance for ASSET = overdraft (show warning)
- Positive balance for EXPENSE = money spent
- Positive balance for INCOME = money earned
