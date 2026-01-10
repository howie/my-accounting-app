# Data Model: Transaction Entry

**Feature**: 004-transaction-entry
**Date**: 2026-01-09
**Database**: PostgreSQL 16

## Entity Overview

This feature extends the existing Transaction model and introduces a new TransactionTemplate entity.

```
┌─────────────┐       ┌──────────────────────┐       ┌─────────────┐
│   Ledger    │───────│   TransactionTemplate │───────│   Account   │
└─────────────┘       └──────────────────────┘       └─────────────┘
      │                        │                           │
      │                        │ (references)              │
      │                        ▼                           │
      │               ┌─────────────────┐                  │
      └───────────────│   Transaction   │──────────────────┘
                      │   (extended)    │
                      └─────────────────┘
```

## Entities

### Transaction (Extended)

Extends existing model from 001-core-accounting with new fields.

| Field                 | Type          | Constraints    | Description                               |
| --------------------- | ------------- | -------------- | ----------------------------------------- |
| id                    | UUID          | PK             | Primary key                               |
| ledger_id             | UUID          | FK, NOT NULL   | Reference to ledger                       |
| date                  | DATE          | NOT NULL       | Transaction business date                 |
| description           | VARCHAR(200)  | NOT NULL       | Transaction description                   |
| amount                | DECIMAL(15,2) | NOT NULL, >= 0 | Transaction amount                        |
| from_account_id       | UUID          | FK, NOT NULL   | Source account (credit)                   |
| to_account_id         | UUID          | FK, NOT NULL   | Destination account (debit)               |
| transaction_type      | ENUM          | NOT NULL       | EXPENSE, INCOME, TRANSFER                 |
| **notes**             | VARCHAR(500)  | NULL           | **NEW** Optional detailed notes           |
| **amount_expression** | VARCHAR(100)  | NULL           | **NEW** Original expression if calculated |
| created_at            | TIMESTAMP     | NOT NULL       | Creation timestamp                        |
| updated_at            | TIMESTAMP     | NOT NULL       | Last update timestamp                     |

**New Fields:**

- `notes`: Optional field for additional transaction details (max 500 chars)
- `amount_expression`: Stores original expression (e.g., "50+40+10") for audit trail

**Validation Rules:**

- `description` must not be empty and max 200 characters
- `notes` max 500 characters (optional)
- `amount` must be between 0.01 and 999,999,999.99
- `from_account_id` must differ from `to_account_id`
- If `amount_expression` provided, backend validates it matches `amount`

### TransactionTemplate (New)

Stores reusable transaction presets for quick entry.

| Field            | Type          | Constraints                 | Description                   |
| ---------------- | ------------- | --------------------------- | ----------------------------- |
| id               | UUID          | PK                          | Primary key                   |
| ledger_id        | UUID          | FK, NOT NULL                | Reference to ledger           |
| name             | VARCHAR(50)   | NOT NULL, UNIQUE per ledger | Template display name         |
| transaction_type | ENUM          | NOT NULL                    | EXPENSE, INCOME, TRANSFER     |
| from_account_id  | UUID          | FK, NOT NULL                | Default source account        |
| to_account_id    | UUID          | FK, NOT NULL                | Default destination account   |
| amount           | DECIMAL(15,2) | NOT NULL                    | Default amount                |
| description      | VARCHAR(200)  | NOT NULL                    | Default description           |
| sort_order       | INTEGER       | NOT NULL, DEFAULT 0         | Display order (for drag-drop) |
| created_at       | TIMESTAMP     | NOT NULL                    | Creation timestamp            |
| updated_at       | TIMESTAMP     | NOT NULL                    | Last update timestamp         |

**Validation Rules:**

- `name` must be unique within the same ledger
- Maximum 50 templates per ledger
- `from_account_id` must differ from `to_account_id`
- `amount` must be between 0.01 and 999,999,999.99

**Indexes:**

- `idx_template_ledger_sort`: (ledger_id, sort_order) for ordered listing
- `idx_template_ledger_name`: (ledger_id, name) for uniqueness check

## State Transitions

### Transaction States

Transactions in this feature follow the existing state model from 001-core-accounting:

```
[New] ──create──▶ [Active] ──void──▶ [Voided]
```

- **New**: Form filled, not yet saved
- **Active**: Saved and affecting account balances
- **Voided**: Soft-deleted, no longer affects balances

### Template States

Templates have a simpler lifecycle:

```
[New] ──save──▶ [Active] ──delete──▶ [Deleted]
                   │
                   └──edit──▶ [Active]
```

- **New**: Form filled, not yet saved
- **Active**: Available for use
- **Deleted**: Hard-deleted from database

## Relationships

### TransactionTemplate → Account

```sql
-- Template references two accounts
ALTER TABLE transaction_templates
ADD CONSTRAINT fk_template_from_account
FOREIGN KEY (from_account_id) REFERENCES accounts(id)
ON DELETE RESTRICT;

ALTER TABLE transaction_templates
ADD CONSTRAINT fk_template_to_account
FOREIGN KEY (to_account_id) REFERENCES accounts(id)
ON DELETE RESTRICT;
```

**ON DELETE RESTRICT**: Prevents deleting accounts that are referenced by templates. User must update or delete templates first.

### TransactionTemplate → Ledger

```sql
ALTER TABLE transaction_templates
ADD CONSTRAINT fk_template_ledger
FOREIGN KEY (ledger_id) REFERENCES ledgers(id)
ON DELETE CASCADE;
```

**ON DELETE CASCADE**: Deleting a ledger deletes all its templates.

## Migration Plan

### Migration 1: Add notes field to transactions

```sql
-- Add notes column (nullable)
ALTER TABLE transactions
ADD COLUMN notes VARCHAR(500) NULL;

-- Add amount_expression column (nullable)
ALTER TABLE transactions
ADD COLUMN amount_expression VARCHAR(100) NULL;
```

### Migration 2: Create transaction_templates table

```sql
CREATE TABLE transaction_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ledger_id UUID NOT NULL REFERENCES ledgers(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    from_account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    to_account_id UUID NOT NULL REFERENCES accounts(id) ON DELETE RESTRICT,
    amount DECIMAL(15,2) NOT NULL,
    description VARCHAR(200) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_template_ledger_name UNIQUE (ledger_id, name),
    CONSTRAINT chk_template_different_accounts CHECK (from_account_id != to_account_id),
    CONSTRAINT chk_template_amount_range CHECK (amount >= 0.01 AND amount <= 999999999.99),
    CONSTRAINT chk_template_type CHECK (transaction_type IN ('EXPENSE', 'INCOME', 'TRANSFER'))
);

CREATE INDEX idx_template_ledger_sort ON transaction_templates(ledger_id, sort_order);
```

## SQLModel Definitions

### Transaction (Extended)

```python
class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ledger_id: UUID = Field(foreign_key="ledgers.id")
    date: date
    description: str = Field(max_length=200)
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    from_account_id: UUID = Field(foreign_key="accounts.id")
    to_account_id: UUID = Field(foreign_key="accounts.id")
    transaction_type: TransactionType
    notes: str | None = Field(default=None, max_length=500)  # NEW
    amount_expression: str | None = Field(default=None, max_length=100)  # NEW
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### TransactionTemplate (New)

```python
class TransactionTemplate(SQLModel, table=True):
    __tablename__ = "transaction_templates"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    ledger_id: UUID = Field(foreign_key="ledgers.id")
    name: str = Field(max_length=50)
    transaction_type: TransactionType
    from_account_id: UUID = Field(foreign_key="accounts.id")
    to_account_id: UUID = Field(foreign_key="accounts.id")
    amount: Decimal = Field(max_digits=15, decimal_places=2)
    description: str = Field(max_length=200)
    sort_order: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    ledger: "Ledger" = Relationship(back_populates="templates")
    from_account: "Account" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TransactionTemplate.from_account_id]"}
    )
    to_account: "Account" = Relationship(
        sa_relationship_kwargs={"foreign_keys": "[TransactionTemplate.to_account_id]"}
    )
```

## TypeScript Types

```typescript
// Transaction (extended)
interface Transaction {
  id: string;
  ledgerId: string;
  date: string; // ISO date YYYY-MM-DD
  description: string;
  amount: number;
  fromAccountId: string;
  toAccountId: string;
  transactionType: "EXPENSE" | "INCOME" | "TRANSFER";
  notes?: string; // NEW
  amountExpression?: string; // NEW
  createdAt: string;
  updatedAt: string;
}

// TransactionTemplate (new)
interface TransactionTemplate {
  id: string;
  ledgerId: string;
  name: string;
  transactionType: "EXPENSE" | "INCOME" | "TRANSFER";
  fromAccountId: string;
  toAccountId: string;
  amount: number;
  description: string;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
}

// Create transaction request
interface CreateTransactionRequest {
  date: string;
  description: string;
  amount: number;
  fromAccountId: string;
  toAccountId: string;
  transactionType: "EXPENSE" | "INCOME" | "TRANSFER";
  notes?: string;
  amountExpression?: string;
}

// Create template request
interface CreateTemplateRequest {
  name: string;
  transactionType: "EXPENSE" | "INCOME" | "TRANSFER";
  fromAccountId: string;
  toAccountId: string;
  amount: number;
  description: string;
}
```
