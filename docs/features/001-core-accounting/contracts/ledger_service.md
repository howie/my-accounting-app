# Service Contract: LedgerService

**Responsibility**: Manage ledgers (account books).

## Methods

### `create_ledger`
Creates a new ledger with default accounts (Cash, Equity).

- **Input**:
  - `user_id`: int
  - `name`: string
  - `initial_cash`: Decimal (optional, default 0)
- **Output**:
  - `ledger_id`: int
- **Side Effects**:
  - Creates "A-Cash" account.
  - Creates "A-Equity" account.
  - If initial_cash > 0, records initial balance transaction.

### `get_ledger`
Retrieves ledger metadata.

- **Input**: `ledger_id`: int
- **Output**: Ledger object

### `list_ledgers`
Lists ledgers for a user.

- **Input**: `user_id`: int
- **Output**: List[Ledger]

### `delete_ledger`
Permanently removes a ledger and all its contents.

- **Input**: `ledger_id`: int
- **Output**: void
- **Errors**:
  - `LedgerNotFoundError`
