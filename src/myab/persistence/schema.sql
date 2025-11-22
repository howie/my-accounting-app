PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user_accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ledgers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_account_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_account_id) REFERENCES user_accounts(id) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_ledgers_user_id ON ledgers(user_account_id);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('Asset', 'Liability', 'Income', 'Expense')),
    initial_balance TEXT NOT NULL DEFAULT '0.00',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ledger_id) REFERENCES ledgers(id) ON DELETE CASCADE,
    UNIQUE(ledger_id, name)
);
CREATE INDEX IF NOT EXISTS idx_accounts_ledger_id ON accounts(ledger_id);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('Expense', 'Income', 'Transfer')),
    debit_account_id INTEGER NOT NULL,
    credit_account_id INTEGER NOT NULL,
    amount TEXT NOT NULL CHECK(amount GLOB '[0-9]*.[0-9][0-9]'),
    description TEXT NOT NULL CHECK(length(description) <= 125),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    modified_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ledger_id) REFERENCES ledgers(id) ON DELETE CASCADE,
    FOREIGN KEY (debit_account_id) REFERENCES accounts(id),
    FOREIGN KEY (credit_account_id) REFERENCES accounts(id),
    CHECK (debit_account_id != credit_account_id)
);
CREATE INDEX IF NOT EXISTS idx_transactions_ledger_date ON transactions(ledger_id, date);
CREATE INDEX IF NOT EXISTS idx_transactions_debit ON transactions(debit_account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_credit ON transactions(credit_account_id);
