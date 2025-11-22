# Data Model: Core Accounting System

**Feature**: 001-core-accounting
**Database**: SQLite (Single file per user account or application instance)

## Schema Overview

The schema implements a double-entry bookkeeping system.

- **Strict Typing**: Uses `STRICT` tables where supported (SQLite 3.37+) or CHECK constraints.
- **Financial Accuracy**: All monetary values stored as `DECIMAL(19, 2)` (using `TEXT` or `INTEGER` storage class in SQLite to preserve precision).
- **Audit**: `created_at` and `modified_at` timestamps on all records.

## Tables

### 1. `user_accounts`
Represents a user of the application.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| `username` | TEXT | NOT NULL, UNIQUE | Alphanumeric username |
| `password_hash` | TEXT | NOT NULL | Hashed password |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | ISO8601 timestamp |
| `modified_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | ISO8601 timestamp |

### 2. `ledgers`
A container for a set of accounts and transactions (e.g., "Personal", "Business").

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| `user_account_id` | INTEGER | NOT NULL, FOREIGN KEY | Owner user |
| `name` | TEXT | NOT NULL | Ledger name (Unicode support) |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| `modified_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

**Indices**:
- `idx_ledgers_user_id` on `user_account_id`

### 3. `accounts`
Chart of accounts entities.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| `ledger_id` | INTEGER | NOT NULL, FOREIGN KEY | Parent ledger |
| `name` | TEXT | NOT NULL | Account name (e.g., "A-Bank") |
| `type` | TEXT | NOT NULL, CHECK(type IN ('Asset', 'Liability', 'Income', 'Expense')) | Accounting classification |
| `initial_balance` | TEXT | NOT NULL, DEFAULT '0.00' | Starting balance (Decimal string) |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| `modified_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

**Constraints**:
- UNIQUE(`ledger_id`, `name`) - No duplicate account names in a ledger.

**Indices**:
- `idx_accounts_ledger_id` on `ledger_id`

### 4. `transactions`
Double-entry transaction records.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | Unique ID |
| `ledger_id` | INTEGER | NOT NULL, FOREIGN KEY | Parent ledger (optimization for queries) |
| `date` | TEXT | NOT NULL | Business date (YYYY-MM-DD) |
| `type` | TEXT | NOT NULL, CHECK(type IN ('Expense', 'Income', 'Transfer')) | Transaction type |
| `debit_account_id` | INTEGER | NOT NULL, FOREIGN KEY | References `accounts(id)` |
| `credit_account_id` | INTEGER | NOT NULL, FOREIGN KEY | References `accounts(id)` |
| `amount` | TEXT | NOT NULL, CHECK(amount GLOB '[0-9]*.[0-9][0-9]') | Transaction amount (Decimal string) |
| `description` | TEXT | NOT NULL, CHECK(length(description) <= 125) | Transaction details |
| `created_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |
| `modified_at` | TEXT | NOT NULL, DEFAULT CURRENT_TIMESTAMP | |

**Constraints**:
- `amount > 0` (implied by logic, enforced by service, CHECK optional)
- `debit_account_id != credit_account_id`

**Indices**:
- `idx_transactions_ledger_date` on `ledger_id`, `date`
- `idx_transactions_debit` on `debit_account_id`
- `idx_transactions_credit` on `credit_account_id`

## Logic & Invariants

1. **Double Entry**: `SUM(debit amounts) == SUM(credit amounts)` is implicitly true per row because each row represents a single pair of balanced entries.
2. **Account Balances**:
   - For Asset/Expense: `initial_balance + SUM(debits) - SUM(credits)`
   - For Liability/Income: `initial_balance + SUM(credits) - SUM(debits)`
3. **Decimal Precision**: All amount fields MUST be treated as strings in SQL and converted to `decimal.Decimal` in Python.

## Validation Rules

1. **Usernames**: Alphanumeric only.
2. **Account Names**: Must start with correct prefix ("A-", "L-", "I-", "E-").
3. **Amounts**: Positive only for transactions. Negative balances allowed for accounts.
4. **Transaction Types**:
   - Expense: Debit Expense, Credit Asset/Liability
   - Income: Debit Asset/Liability, Credit Income
   - Transfer: Debit Asset/Liability, Credit Asset/Liability
