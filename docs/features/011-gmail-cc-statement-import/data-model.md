# Data Model: Gmail 信用卡帳單自動掃描匯入

**Feature**: 011-gmail-cc-statement-import
**Date**: 2026-02-05

## Entity Relationship Overview

```
User (existing)
 └── GmailConnection (1:1)
      ├── UserBankSetting (1:N, one per bank)
      └── StatementScanJob (1:N)
           └── DiscoveredStatement (1:N)
                └── ImportSession (1:1, existing model, extended)
                     └── Transaction (1:N, existing model)
```

## New Entities

### GmailConnection

Stores the user's Gmail OAuth2 connection state and credentials.

| Field                  | Type         | Constraints                        | Description                               |
| ---------------------- | ------------ | ---------------------------------- | ----------------------------------------- |
| id                     | UUID         | PK, auto-generated                 | Unique identifier                         |
| user_id                | UUID         | FK → users.id, UNIQUE              | Owning user (one connection per user)     |
| email_address          | String(255)  | NOT NULL                           | Connected Gmail address                   |
| encrypted_access_token | Text         | NOT NULL                           | Fernet-encrypted OAuth2 access token      |
| encrypted_refresh_token| Text         | NOT NULL                           | Fernet-encrypted OAuth2 refresh token     |
| token_expiry           | DateTime     | NULL                               | Access token expiry time                  |
| status                 | Enum         | NOT NULL, default: CONNECTED       | CONNECTED / EXPIRED / DISCONNECTED        |
| scan_start_date        | Date         | NOT NULL, default: 6 months ago    | Earliest date to scan for statements      |
| schedule_frequency     | Enum         | NULL                               | DAILY / WEEKLY / null (disabled)          |
| schedule_hour          | Integer      | NULL, 0-23                         | Hour of day for scheduled scan            |
| schedule_day_of_week   | Integer      | NULL, 0-6                          | Day of week for weekly scan (0=Monday)    |
| last_scan_at           | DateTime     | NULL                               | Timestamp of last completed scan          |
| created_at             | DateTime     | NOT NULL, auto                     | Record creation timestamp                 |
| updated_at             | DateTime     | NOT NULL, auto                     | Record update timestamp                   |

**State transitions**:
- `CONNECTED` → `EXPIRED` (when token refresh fails)
- `EXPIRED` → `CONNECTED` (when user re-authorizes)
- `CONNECTED` / `EXPIRED` → `DISCONNECTED` (when user disconnects)
- `DISCONNECTED` → `CONNECTED` (when user reconnects)

**Validation rules**:
- One GmailConnection per user (UNIQUE on user_id)
- schedule_day_of_week only valid when schedule_frequency = WEEKLY
- schedule_hour required when schedule_frequency is not null

---

### UserBankSetting

Stores per-user configuration for each bank (enabled status, PDF password).

| Field                 | Type         | Constraints                        | Description                                |
| --------------------- | ------------ | ---------------------------------- | ------------------------------------------ |
| id                    | UUID         | PK, auto-generated                 | Unique identifier                          |
| user_id               | UUID         | FK → users.id                      | Owning user                                |
| bank_code             | String(20)   | NOT NULL                           | Bank identifier (e.g., CTBC, CATHAY)       |
| is_enabled            | Boolean      | NOT NULL, default: false           | Whether to scan this bank                  |
| encrypted_pdf_password| Text         | NULL                               | Fernet-encrypted PDF decryption password   |
| credit_card_account_id| UUID         | FK → accounts.id, NULL             | Linked credit card account in ledger       |
| created_at            | DateTime     | NOT NULL, auto                     | Record creation timestamp                  |
| updated_at            | DateTime     | NOT NULL, auto                     | Record update timestamp                    |

**Constraints**:
- UNIQUE on (user_id, bank_code) — one setting per bank per user
- credit_card_account_id references an existing account of type LIABILITY

**Validation rules**:
- encrypted_pdf_password required when is_enabled = true (most banks require password)
- bank_code must be a valid registered parser code

---

### StatementScanJob

Tracks each scan execution (manual or scheduled).

| Field              | Type         | Constraints                        | Description                                |
| ------------------ | ------------ | ---------------------------------- | ------------------------------------------ |
| id                 | UUID         | PK, auto-generated                 | Unique identifier                          |
| gmail_connection_id| UUID         | FK → gmail_connections.id          | Associated Gmail connection                |
| trigger_type       | Enum         | NOT NULL                           | MANUAL / SCHEDULED                         |
| status             | Enum         | NOT NULL, default: PENDING         | PENDING / SCANNING / COMPLETED / FAILED    |
| banks_scanned      | JSON         | NOT NULL, default: []              | List of bank codes scanned                 |
| statements_found   | Integer      | NOT NULL, default: 0               | Number of statements discovered            |
| error_message      | Text         | NULL                               | Error details if failed                    |
| started_at         | DateTime     | NULL                               | Scan start timestamp                       |
| completed_at       | DateTime     | NULL                               | Scan completion timestamp                  |
| created_at         | DateTime     | NOT NULL, auto                     | Record creation timestamp                  |

**State transitions**:
- `PENDING` → `SCANNING` (scan starts)
- `SCANNING` → `COMPLETED` (scan finishes successfully)
- `SCANNING` → `FAILED` (scan encounters fatal error)

---

### DiscoveredStatement

Represents a credit card statement found during scanning.

| Field              | Type         | Constraints                        | Description                                |
| ------------------ | ------------ | ---------------------------------- | ------------------------------------------ |
| id                 | UUID         | PK, auto-generated                 | Unique identifier                          |
| scan_job_id        | UUID         | FK → statement_scan_jobs.id        | Parent scan job                            |
| bank_code          | String(20)   | NOT NULL                           | Bank identifier                            |
| bank_name          | String(100)  | NOT NULL                           | Bank display name                          |
| billing_period_start| Date        | NULL                               | Statement billing period start             |
| billing_period_end | Date         | NULL                               | Statement billing period end               |
| email_message_id   | String(255)  | NOT NULL                           | Gmail message ID for traceability          |
| email_subject      | String(500)  | NOT NULL                           | Email subject line                         |
| email_date         | DateTime     | NOT NULL                           | Email received date                        |
| pdf_attachment_id  | String(255)  | NOT NULL                           | Gmail attachment ID                        |
| pdf_filename       | String(255)  | NOT NULL                           | Original PDF filename                      |
| parse_status       | Enum         | NOT NULL, default: PENDING         | PENDING / PARSED / PARSE_FAILED / LLM_PARSED |
| parse_confidence   | Float        | NULL, 0.0-1.0                      | Parsing confidence score                   |
| transaction_count  | Integer      | NOT NULL, default: 0               | Number of transactions extracted           |
| total_amount       | Decimal(12,2)| NULL                               | Sum of all transaction amounts             |
| import_status      | Enum         | NOT NULL, default: NOT_IMPORTED    | NOT_IMPORTED / IMPORTED / SKIPPED          |
| import_session_id  | UUID         | FK → import_sessions.id, NULL      | Linked import session (after import)       |
| error_message      | Text         | NULL                               | Parse error details                        |
| created_at         | DateTime     | NOT NULL, auto                     | Record creation timestamp                  |

**Constraints**:
- UNIQUE on (bank_code, billing_period_start, billing_period_end) — prevent duplicate statement processing
- If billing period is null (parse failed), uniqueness falls back to email_message_id

**State transitions (parse_status)**:
- `PENDING` → `PARSED` (pdfplumber extraction succeeded)
- `PENDING` → `PARSE_FAILED` (extraction failed)
- `PARSE_FAILED` → `LLM_PARSED` (LLM fallback succeeded)
- `PENDING` → `LLM_PARSED` (primary parsing low confidence, LLM used)

**State transitions (import_status)**:
- `NOT_IMPORTED` → `IMPORTED` (user confirmed import)
- `NOT_IMPORTED` → `SKIPPED` (user chose to skip)

---

## Extended Existing Entities

### ImportSession (extended)

Add field to existing `import_sessions` table:

| Field              | Type         | Constraints                        | Description                                |
| ------------------ | ------------ | ---------------------------------- | ------------------------------------------ |
| email_message_id   | String(255)  | NULL                               | Gmail message ID (for GMAIL_CC imports)    |

### ImportType Enum (extended)

Add new value to existing enum:

```
GMAIL_CC = "GMAIL_CC"
```

---

## Transient Data Structures (not persisted)

### ParsedStatementTransaction

Used during PDF parsing, before import. Not stored in database.

| Field              | Type         | Description                                |
| ------------------ | ------------ | ------------------------------------------ |
| date               | date         | Transaction date                           |
| merchant_name      | str          | Merchant/store name                        |
| amount             | Decimal      | Transaction amount (positive)              |
| currency           | str          | Currency code (default: TWD)               |
| original_description| str         | Raw description from PDF                   |
| category_suggestion| str \| None  | Suggested category from CategorySuggester  |
| confidence         | float        | Category suggestion confidence (0-1)       |
| is_foreign         | bool         | Whether this is a foreign currency transaction |
| installment_info   | str \| None  | Installment details if applicable          |

---

## Accounting Logic

### Double-Entry Mapping for Credit Card Statements

Each credit card transaction creates a double-entry record:

```
From Account (Debit):  Expense category account (e.g., 餐飲費)
To Account (Credit):   Credit card liability account (e.g., 國泰世華信用卡)
Amount:                Transaction amount from statement
Transaction Type:      EXPENSE
```

Note: In our system's convention (matching existing 006-data-import):
- `from_account` = the expense category (where money goes)
- `to_account` = the credit card (source of funds / liability)

This aligns with how the existing CSV import treats credit card transactions:
- Credit card is a LIABILITY account
- Each purchase increases the liability (credit) and records an expense (debit)

### Category Mapping

Reuses existing `CategorySuggester` from 006-data-import:
1. Extract merchant name from parsed PDF transaction
2. Run through keyword matching (餐飲費, 交通費, 日用品, etc.)
3. Return suggestion with confidence score
4. User can modify before confirming import

---

## Migration Notes

### New Tables

1. `gmail_connections` — GmailConnection
2. `user_bank_settings` — UserBankSetting
3. `statement_scan_jobs` — StatementScanJob
4. `discovered_statements` — DiscoveredStatement

### Altered Tables

1. `import_sessions` — Add `email_message_id` column (nullable String)

### Enum Changes

1. `ImportType` — Add `GMAIL_CC` value

### Indexes

- `gmail_connections`: UNIQUE index on `user_id`
- `user_bank_settings`: UNIQUE index on `(user_id, bank_code)`
- `discovered_statements`: UNIQUE index on `(bank_code, billing_period_start, billing_period_end)` (partial, where billing period is not null)
- `discovered_statements`: Index on `email_message_id`
- `statement_scan_jobs`: Index on `gmail_connection_id`
