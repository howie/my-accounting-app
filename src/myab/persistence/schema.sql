CREATE TABLE IF NOT EXISTS user_account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    creation_timestamp TEXT NOT NULL,
    modification_timestamp TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_account_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    creation_date TEXT NOT NULL,
    creation_timestamp TEXT NOT NULL,
    modification_timestamp TEXT NOT NULL,
    FOREIGN KEY (user_account_id) REFERENCES user_account (id)
);

CREATE TABLE IF NOT EXISTS account (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    is_predefined INTEGER NOT NULL DEFAULT 0,
    creation_timestamp TEXT NOT NULL,
    modification_timestamp TEXT NOT NULL,
    FOREIGN KEY (ledger_id) REFERENCES ledger (id)
);

CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ledger_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    type TEXT NOT NULL,
    amount INTEGER NOT NULL,
    debit_account_id INTEGER NOT NULL,
    credit_account_id INTEGER NOT NULL,
    description TEXT,
    invoice_number TEXT,
    creation_timestamp TEXT NOT NULL,
    modification_timestamp TEXT NOT NULL,
    FOREIGN KEY (ledger_id) REFERENCES ledger (id),
    FOREIGN KEY (debit_account_id) REFERENCES account (id),
    FOREIGN KEY (credit_account_id) REFERENCES account (id)
);