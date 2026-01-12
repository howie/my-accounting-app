# Data Model: MCP API 對話式記帳介面

**Feature**: 007-api-for-mcp
**Date**: 2026-01-11

## Overview

This feature adds one new entity (`ApiToken`) and reuses existing entities from 001-core-accounting. The MCP tools operate on existing data models without modification.

## New Entity

### ApiToken

Represents a long-lived API token for MCP authentication.

```
┌─────────────────────────────────────────────────────────────┐
│                        ApiToken                             │
├─────────────────────────────────────────────────────────────┤
│ id: UUID                    [PK]                            │
│ user_id: UUID               [FK → users.id]                 │
│ name: str(100)              # User-friendly label           │
│ token_hash: str(64)         # SHA-256 hash of token         │
│ token_prefix: str(8)        # First 8 chars for display     │
│ created_at: datetime        # UTC timestamp                 │
│ last_used_at: datetime?     # Last successful auth          │
│ revoked_at: datetime?       # Soft delete timestamp         │
└─────────────────────────────────────────────────────────────┘
```

#### Field Details

| Field        | Type         | Constraints             | Description                                   |
| ------------ | ------------ | ----------------------- | --------------------------------------------- |
| id           | UUID         | PK, auto-generated      | Unique identifier                             |
| user_id      | UUID         | FK, NOT NULL, indexed   | Owner of the token                            |
| name         | VARCHAR(100) | NOT NULL                | Human-readable label (e.g., "Claude Desktop") |
| token_hash   | VARCHAR(64)  | NOT NULL, UNIQUE        | SHA-256 hash of the raw token                 |
| token_prefix | VARCHAR(8)   | NOT NULL                | First 8 characters for identification         |
| created_at   | TIMESTAMP    | NOT NULL, default NOW() | Creation timestamp (UTC)                      |
| last_used_at | TIMESTAMP    | NULL                    | Last successful authentication                |
| revoked_at   | TIMESTAMP    | NULL                    | Revocation timestamp (soft delete)            |

#### Validation Rules

- `name`: 1-100 characters, non-empty
- `token_hash`: Exactly 64 hex characters (SHA-256)
- `token_prefix`: Exactly 8 characters
- Active token: `revoked_at IS NULL`

#### State Transitions

```
┌─────────┐    create()    ┌────────┐    revoke()    ┌─────────┐
│ (none)  │ ──────────────→│ Active │ ──────────────→│ Revoked │
└─────────┘                └────────┘                └─────────┘
                               │
                               │ authenticate()
                               ▼
                          [update last_used_at]
```

## Existing Entities (Referenced)

The MCP tools interact with these existing entities from 001-core-accounting:

### Ledger (read-only via MCP)

```
┌─────────────────────────────────────────────────────────────┐
│                        Ledger                               │
├─────────────────────────────────────────────────────────────┤
│ id: UUID                    [PK]                            │
│ user_id: UUID               [FK → users.id]                 │
│ name: str(100)                                              │
│ description: str(500)?                                      │
│ created_at: datetime                                        │
│ updated_at: datetime                                        │
└─────────────────────────────────────────────────────────────┘
```

### Account (read-only via MCP)

```
┌─────────────────────────────────────────────────────────────┐
│                        Account                              │
├─────────────────────────────────────────────────────────────┤
│ id: UUID                    [PK]                            │
│ ledger_id: UUID             [FK → ledgers.id]               │
│ name: str(100)                                              │
│ type: AccountType           [ASSET|LIABILITY|INCOME|EXPENSE]│
│ balance: Decimal(15,2)                                      │
│ is_system: bool                                             │
│ parent_id: UUID?            [FK → accounts.id]              │
│ depth: int                  [1-3]                           │
│ sort_order: int                                             │
│ created_at: datetime                                        │
│ updated_at: datetime                                        │
└─────────────────────────────────────────────────────────────┘
```

### Transaction (create via MCP)

```
┌─────────────────────────────────────────────────────────────┐
│                      Transaction                            │
├─────────────────────────────────────────────────────────────┤
│ id: UUID                    [PK]                            │
│ ledger_id: UUID             [FK → ledgers.id]               │
│ date: date                                                  │
│ description: str(255)                                       │
│ amount: Decimal(15,2)                                       │
│ from_account_id: UUID       [FK → accounts.id]              │
│ to_account_id: UUID         [FK → accounts.id]              │
│ transaction_type: TransactionType                           │
│ notes: str(500)?                                            │
│ amount_expression: str(100)?                                │
│ created_at: datetime                                        │
│ updated_at: datetime                                        │
└─────────────────────────────────────────────────────────────┘
```

## Entity Relationships

```
┌─────────┐
│  User   │
└────┬────┘
     │ 1:N
     ▼
┌──────────┐     ┌─────────┐
│ ApiToken │     │ Ledger  │
└──────────┘     └────┬────┘
                      │ 1:N
          ┌───────────┴───────────┐
          ▼                       ▼
     ┌─────────┐            ┌─────────────┐
     │ Account │◄───────────│ Transaction │
     └─────────┘  from/to   └─────────────┘
```

## Database Migration

### New Table: api_tokens

```sql
CREATE TABLE api_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    token_prefix VARCHAR(8) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_api_tokens_user_id ON api_tokens(user_id);
CREATE INDEX idx_api_tokens_token_hash ON api_tokens(token_hash) WHERE revoked_at IS NULL;
```

## MCP Response Schemas

### AccountSummary (for list_accounts, get_account)

```json
{
  "id": "uuid",
  "name": "string",
  "type": "ASSET|LIABILITY|INCOME|EXPENSE",
  "balance": "decimal",
  "parent_id": "uuid?",
  "depth": "int"
}
```

### TransactionSummary (for list_transactions, create_transaction)

```json
{
  "id": "uuid",
  "date": "YYYY-MM-DD",
  "description": "string",
  "amount": "decimal",
  "from_account": {
    "id": "uuid",
    "name": "string"
  },
  "to_account": {
    "id": "uuid",
    "name": "string"
  },
  "notes": "string?"
}
```

### LedgerSummary (for list_ledgers)

```json
{
  "id": "uuid",
  "name": "string",
  "description": "string?",
  "account_count": "int",
  "transaction_count": "int"
}
```
