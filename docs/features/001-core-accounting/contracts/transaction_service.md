# Service Contract: TransactionService

**Responsibility**: Record and retrieve financial transactions.

## Methods

### `record_transaction`
Creates a double-entry transaction.

- **Input**:
  - `ledger_id`: int
  - `date`: date
  - `type`: string (Expense|Income|Transfer)
  - `debit_account_id`: int
  - `credit_account_id`: int
  - `amount`: Decimal
  - `description`: string
- **Output**:
  - `transaction_id`: int
- **Logic**:
  - Validates double-entry rules based on `type`.
  - Validates amount (positive, 2 decimals).
  - Validates account ownership (must belong to ledger).

### `search_transactions`
Filters transaction history.

- **Input**:
  - `ledger_id`: int
  - `query`: string (optional description match)
  - `account_id`: int (optional)
  - `date_from`: date (optional)
  - `date_to`: date (optional)
- **Output**: List[Transaction]

### `update_transaction`
Edits an existing transaction.

- **Input**: `transaction_id`, (fields to update)
- **Logic**:
  - Re-validates all constraints.
  - Updates `modified_at`.

### `delete_transaction`
Removes a transaction.

- **Input**: `transaction_id`
- **Output**: void
