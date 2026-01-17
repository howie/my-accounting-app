# Research & Decisions: Advanced Transactions

**Status**: Phase 0 Complete
**Date**: 2026-01-17

## Technical Decisions

### Decision 1: Tagging Implementation

- **Choice**: Many-to-Many relationship table (`transaction_tags`) between `transactions` and a new `tags` table.
- **Rationale**: Allows for efficient querying/filtering by tags, easy renaming/deletion of tags without iterating through all transactions, and enables a single transaction to have multiple tags.
- **Alternatives Considered**:
  - **Comma-separated string column in `transactions`**: Rejected due to poor query performance (LIKE queries) and difficulty in renaming tags.
  - **JSON array column**: Better than string, but still harder to enforce referential integrity and perform efficient joins/counts compared to a normalized table.

### Decision 2: Recurring Transaction Storage

- **Choice**: A dedicated `recurring_transactions` table that acts as a template.
- **Rationale**: Separates the "schedule" definition from the actual "executed" transactions. Keeps the ledger clean and allows for editing the schedule without affecting past history.
- **Alternatives Considered**:
  - **Flagging regular transactions as recurring**: Rejected because it mixes historical data with future intent and makes it hard to manage the schedule itself (e.g., changing the amount for _future_ transactions only).

### Decision 3: Installment Plan Tracking

- **Choice**: A new `installment_plans` table linked to the `transactions` table via a `plan_id` foreign key.
- **Rationale**: Allows grouping of all installment transactions under a single "plan" entity. The plan can store the total amount, total installments, and status.
- **Alternatives Considered**:
  - **Linking transactions to the first transaction**: Rejected as it creates a dependency on a specific transaction row and makes it harder to query "plans" as distinct objects.

### Decision 4: Recurring Execution Mechanism

- **Choice**: "Pull" model with Manual Approval (per Spec). The frontend will query for "due" items from the `recurring_transactions` table based on the last execution date vs. current date and prompt the user.
- **Rationale**: Avoids the need for a background job scheduler (cron/Celery) which adds significant complexity to a self-hosted local web app. The user's presence triggers the check.
- **Alternatives Considered**:
  - **Background Worker (Celery/Cron)**: Overkill for a local single-user app; adds deployment complexity.

## Unknowns Resolved

- **Tag Overlap**: Filtering will support standard OR logic for initial discovery (match any selected tag), which is user-friendly. AND logic can be added later if needed.
- **Leap Years**: Python's `dateutil.relativedelta` or similar libraries handle month-end logic correctly (e.g., Jan 31 + 1 month = Feb 28/29). We will use standard libraries for date math.
- **Deleted Accounts**: Database Foreign Keys will be set to `ON DELETE RESTRICT` to prevent deleting accounts that are used in active recurring transactions or installment plans, preserving data integrity.

## Best Practices Adopted

- **Date Handling**: All dates stored as ISO 8601 strings or native Date types in DB.
- **Currency**: Monetary values stored as integers (cents) or high-precision decimals to avoid floating-point errors.
- **Audit**: `created_at` and `updated_at` timestamps on all new tables.
