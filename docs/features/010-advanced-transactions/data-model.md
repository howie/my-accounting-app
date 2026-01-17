# Data Model: Advanced Transactions

**Status**: Phase 1 Draft
**Date**: 2026-01-17

## Entity Relationship Diagram (Conceptual)

```mermaid
erDiagram
    Transaction }|--|{ Tag : "has many"
    RecurringTransaction ||--|{ Transaction : "generates"
    InstallmentPlan ||--|{ Transaction : "consists of"
    Account ||--o{ RecurringTransaction : "source/dest"

    Tag {
        int id PK
        string name "Unique, Indexed"
        string color "Hex code"
        datetime created_at
    }

    RecurringTransaction {
        int id PK
        string name
        int amount "Cents"
        string type "Expense/Income/Transfer"
        int source_account_id FK
        int dest_account_id FK
        string frequency "DAILY, WEEKLY, MONTHLY, YEARLY"
        date start_date
        date end_date "Nullable"
        date last_generated_date "Nullable"
        datetime created_at
        datetime updated_at
    }

    InstallmentPlan {
        int id PK
        string name
        int total_amount "Cents"
        int installment_count
        string frequency "MONTHLY"
        date start_date
        int source_account_id FK
        int dest_account_id FK
        datetime created_at
    }

    Transaction {
        int id PK
        ...existing_fields...
        int recurring_transaction_id FK "Nullable"
        int installment_plan_id FK "Nullable"
        int installment_number "Nullable, 1-based index"
    }
```

## Entity Details

### 1. Tag

- **Purpose**: Categorize transactions for filtering and reporting.
- **Constraints**:
  - Name must be unique.
  - Name cannot be empty.
  - Color should be a valid hex code (optional, default provided).

### 2. RecurringTransaction

- **Purpose**: Template for generating future transactions.
- **Fields**:
  - `frequency`: Enum (DAILY, WEEKLY, MONTHLY, YEARLY).
  - `last_generated_date`: updated each time a transaction is successfully created from this template.
- **Logic**:
  - Next Due Date = `start_date` + `frequency` \* N (where result > `last_generated_date`).

### 3. InstallmentPlan

- **Purpose**: Grouping entity for a set of related installment transactions.
- **Fields**:
  - `total_amount`: The full principal amount.
  - `installment_count`: Total number of payments.
- **Logic**:
  - Sum of linked transactions' amounts MUST equal `total_amount` (DI-001).

### 4. Transaction (Updates)

- **New Fields**:
  - `tags`: Relationship to Tag entity.
  - `recurring_transaction_id`: Link to parent template (if applicable).
  - `installment_plan_id`: Link to parent plan (if applicable).
  - `installment_number`: E.g., "1" of 12.

## Validation Rules

1.  **RecurringTransaction**:
    - `start_date` must be valid.
    - `amount` must be positive.
    - `source_account_id` and `dest_account_id` must differ.
2.  **InstallmentPlan**:
    - `total_amount` > 0.
    - `installment_count` > 1.
3.  **Tags**:
    - No duplicate names allowed (case-insensitive check recommended).

## State Transitions

- **RecurringTransaction**:
  - `Active` (implicitly, if `end_date` is null or future) -> `Expired` (if `end_date` passed).
- **InstallmentPlan**:
  - Created -> (Transactions Generated Immediately) -> Completed (implicitly, when all transactions posted).
