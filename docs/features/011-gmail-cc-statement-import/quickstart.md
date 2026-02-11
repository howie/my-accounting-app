# Quick Start: Gmail 信用卡帳單自動掃描匯入

**Feature**: 011-gmail-cc-statement-import
**Date**: 2026-02-05

## Prerequisites

### Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Gmail API** under "APIs & Services > Library"
4. Create OAuth2 credentials:
   - Go to "APIs & Services > Credentials"
   - Click "Create Credentials > OAuth client ID"
   - Application type: **Web application**
   - Authorized redirect URIs: `http://localhost:8000/api/v1/gmail/auth/callback`
5. Download the client configuration and note the **Client ID** and **Client Secret**

### Environment Variables

Add the following to your `.env` file:

```bash
# Google OAuth2 credentials
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Encryption key for storing sensitive data (generate a secure random key)
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
GMAIL_ENCRYPTION_KEY=your-fernet-key-here

# Optional: LLM API for complex PDF parsing fallback
# GEMINI_API_KEY=your-gemini-key-here
# ANTHROPIC_API_KEY=your-anthropic-key-here
```

### Python Dependencies

```bash
pip install google-api-python-client google-auth-oauthlib pdfplumber pikepdf cryptography apscheduler
```

Or add to `requirements.txt` / `pyproject.toml`:

```
google-api-python-client>=2.100.0
google-auth-oauthlib>=1.1.0
pdfplumber>=0.10.0
pikepdf>=8.0.0
cryptography>=41.0.0
APScheduler>=3.10.0
```

## Database Migration

After implementing the models, create and run the migration:

```bash
cd backend
alembic revision --autogenerate -m "add gmail import tables"
alembic upgrade head
```

New tables:
- `gmail_connections`
- `user_bank_settings`
- `statement_scan_jobs`
- `discovered_statements`

Modified tables:
- `import_sessions` — new `email_message_id` column

## Development Workflow

### 1. Connect Gmail

```
POST /api/v1/gmail/auth/connect?ledger_id={uuid}
→ Returns { auth_url: "https://accounts.google.com/..." }
→ Redirect user to auth_url
→ Google redirects back to /api/v1/gmail/auth/callback
→ Backend stores encrypted tokens, redirects to frontend settings page
```

### 2. Configure Banks

```
PUT /api/v1/gmail/banks/settings
{
  "bank_code": "CATHAY",
  "is_enabled": true,
  "pdf_password": "A123456789",
  "credit_card_account_id": "uuid-of-cathay-cc-account"
}
```

### 3. Trigger Scan

```
POST /api/v1/ledgers/{ledger_id}/gmail/scan
→ Returns { id: "scan-job-uuid", status: "SCANNING" }

GET /api/v1/gmail/scan/{scan_job_id}
→ Returns { status: "COMPLETED", statements_found: 2 }

GET /api/v1/gmail/scan/{scan_job_id}/statements
→ Returns list of discovered statements
```

### 4. Preview & Import

```
GET /api/v1/gmail/statements/{statement_id}/preview
→ Returns parsed transactions with category suggestions

POST /api/v1/ledgers/{ledger_id}/gmail/statements/{statement_id}/import
{
  "statement_id": "uuid",
  "category_overrides": [
    { "transaction_index": 3, "category_name": "交通費" }
  ],
  "skip_transaction_indices": [7]
}
→ Returns { success: true, imported_count: 45, skipped_count: 1 }
```

## Adding a New Bank Parser

To add support for a new bank, create a single file in `backend/src/services/bank_parsers/`:

```python
# backend/src/services/bank_parsers/newbank_parser.py

from decimal import Decimal
from datetime import date

from .base import BankStatementParser, ParsedStatementTransaction
from . import register_parser


@register_parser
class NewBankParser(BankStatementParser):
    bank_code = "NEWBANK"
    bank_name = "新銀行"
    email_query = 'from:newbank.com.tw subject:信用卡電子帳單'
    password_hint = "預設密碼為身分證字號（首字大寫）"

    def parse_statement(self, pdf_path: str) -> list[ParsedStatementTransaction]:
        """Parse transactions from the bank's PDF statement."""
        import pdfplumber

        transactions = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        # Bank-specific parsing logic here
                        tx = ParsedStatementTransaction(
                            date=self._parse_date(row[0]),
                            merchant_name=row[1].strip(),
                            amount=Decimal(row[2].replace(",", "")),
                            currency="TWD",
                            original_description=row[1],
                        )
                        transactions.append(tx)
        return transactions

    def detect_billing_period(self, pdf_path: str) -> tuple[date, date]:
        """Extract billing period from statement header."""
        # Bank-specific logic to find billing period
        ...

    def _parse_date(self, date_str: str) -> date:
        """Parse bank-specific date format."""
        # e.g., "2026/01/15" or "115/01/15" (ROC calendar)
        ...
```

That's it — no other files need to be modified. The `@register_parser` decorator auto-registers the parser, and it will appear in the bank list automatically.

## Testing

### Run unit tests

```bash
cd backend
pytest tests/unit/test_bank_parsers/ -v
pytest tests/unit/test_pdf_parser.py -v
pytest tests/unit/test_gmail_service.py -v
```

### Run integration tests

```bash
cd backend
pytest tests/integration/test_gmail_import_service.py -v
```

### Test with sample PDFs

Place sample bank statement PDFs in `backend/tests/fixtures/pdf/` for automated testing. Each bank parser test should have at least one sample PDF.

## Key Architecture Decisions

| Decision                     | Choice                        | Rationale                                     |
| ---------------------------- | ----------------------------- | --------------------------------------------- |
| Gmail API client             | google-api-python-client      | Official Google library, full API support      |
| PDF decryption               | pikepdf                       | Most reliable for AES-256 encrypted PDFs       |
| PDF table extraction         | pdfplumber                    | Best Python library for structured table data  |
| LLM fallback                 | Optional (Gemini/Claude)      | Resilience for format changes, not required    |
| Credential encryption        | cryptography (Fernet)         | Authenticated encryption, simple API           |
| Scheduling                   | APScheduler                   | Lightweight, persistent, FastAPI-compatible    |
| Bank parser architecture     | Strategy + Registry pattern   | Zero-config extensibility for new banks        |
| Import pipeline              | Reuse 006-data-import         | Proven pipeline for duplicate detection, audit |
