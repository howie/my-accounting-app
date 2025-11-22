# Service Contract: AccountService

**Responsibility**: Manage chart of accounts.

## Methods

### `create_account`
Adds a new account to a ledger.

- **Input**:
  - `ledger_id`: int
  - `name`: string (raw name, e.g. "Bank")
  - `type`: string (Asset|Liability|Income|Expense)
  - `initial_balance`: Decimal (default 0)
- **Output**:
  - `account_id`: int
- **Logic**:
  - Prepends prefix to name (e.g. "A-Bank").
  - Validates unique name within ledger.

### `get_account_balance`
Calculates current balance.

- **Input**: `account_id`: int
- **Output**: Decimal

### `list_accounts`
Retrieves chart of accounts for a ledger.

- **Input**: `ledger_id`: int
- **Output**: List[Account]

### `delete_account`
Removes an account.

- **Input**: `account_id`: int
- **Logic**:
  - Checks if "Cash" or "Equity" (prevent delete).
  - Checks if has associated transactions (prevent delete).
- **Errors**:
  - `SystemAccountDeleteError`
  - `AccountHasTransactionsError`
