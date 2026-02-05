# Research: Gmail 信用卡帳單自動掃描匯入

**Feature**: 011-gmail-cc-statement-import
**Date**: 2026-02-05

## 1. Gmail API Integration

### Decision: google-api-python-client + google-auth-oauthlib

**Rationale**: This is Google's official Python client library, well-maintained, and supports the full Gmail API including message search, attachment download, and OAuth2 authentication. It's the standard choice for Python Gmail integration.

**Alternatives considered**:
- **imapclient**: Low-level IMAP access. Rejected because Gmail API provides superior search capabilities (Gmail query syntax) and better authentication (OAuth2 vs app passwords).
- **gmail-api-wrapper**: Third-party wrapper. Rejected due to less active maintenance and unnecessary abstraction over the official library.

### OAuth2 Flow

**Decision**: Use `InstalledAppFlow` for initial authorization, store tokens in database (encrypted), auto-refresh with `google.auth.transport.requests.Request`.

**Key considerations**:
- Scope: `https://www.googleapis.com/auth/gmail.readonly` (minimum required)
- Token storage: Encrypted in PostgreSQL `gmail_connections` table, not in filesystem `token.json`
- Refresh: Auto-refresh on each API call; if refresh fails, mark connection as "needs reauthorization"
- Redirect URI: Backend handles OAuth2 callback, then redirects to frontend

### Gmail Search Syntax

Each bank has a specific search query combining sender address + subject keywords:

| Bank     | Query                                             |
| -------- | ------------------------------------------------- |
| 中國信託 | `from:ctbcbank.com subject:信用卡電子帳單`        |
| 台北富邦 | `from:fubon.com subject:信用卡電子帳單`            |
| 國泰世華 | `from:cathaybk.com.tw subject:信用卡電子帳單`      |
| 星展     | `from:dbs.com subject:信用卡電子對帳單`            |
| 匯豐     | `from:hsbc.com.tw subject:e-Statement`             |
| 華南     | `from:hncb.com.tw subject:信用卡電子帳單`          |
| 玉山     | `from:esunbank.com.tw subject:信用卡電子帳單`      |
| 永豐     | `from:sinopac.com subject:信用卡電子帳單`          |

Additional filters applied per scan:
- `has:attachment filename:pdf` — ensure PDF attachment present
- `after:YYYY/MM/DD` — limit to scan start date or last scan date

## 2. PDF Decryption

### Decision: pikepdf

**Rationale**: pikepdf is the most robust Python library for PDF decryption, built on QPDF. It handles AES-256 and RC4 encryption commonly used by Taiwanese banks. It's more reliable than PyPDF2 for encrypted PDFs.

**Alternatives considered**:
- **PyPDF2/pypdf**: Can decrypt some PDFs but has known issues with AES-256 encryption used by some banks. Rejected for reliability concerns.
- **pdfplumber with password parameter**: pdfplumber delegates decryption to pdfminer, which has limited encryption support. Using pikepdf to decrypt first, then pdfplumber to parse, is more reliable.

### Decryption Workflow

1. Receive encrypted PDF bytes
2. Attempt decryption with pikepdf using user-configured password
3. If successful, save decrypted PDF to temporary file
4. Pass decrypted PDF to pdfplumber for table extraction
5. Clean up temporary files after processing

### Password Conventions

Most Taiwanese banks use the cardholder's national ID number (身分證字號) as the PDF password, with the first letter in uppercase. Exceptions:
- 匯豐 (HSBC): May use birth date (YYYYMMDD) or national ID
- Some banks may allow custom passwords set via online banking

Passwords are stored encrypted in the database using the `cryptography` library (Fernet symmetric encryption). The encryption key is derived from an environment variable.

## 3. PDF Parsing

### Decision: pdfplumber (primary) + optional LLM fallback

**Rationale**: pdfplumber excels at extracting tabular data from PDFs, which is exactly what credit card statements contain. It provides cell-level extraction with position information, making it suitable for parsing structured tables even when formatting varies between banks.

**Alternatives considered**:
- **tabula-py**: Java-based (requires JRE). Rejected for deployment complexity and slower startup time.
- **camelot**: Good for table extraction but requires Ghostscript dependency. Rejected for simpler dependency chain.
- **Pure LLM parsing**: Sending raw text to LLM for every statement. Rejected as primary approach due to cost, latency, and consistency concerns. Reserved as fallback.

### Parsing Strategy

1. **Primary**: Use pdfplumber to extract table rows from the transactions section
2. **Per-bank configuration**: Each bank parser defines:
   - Page range where transactions appear
   - Table header patterns (to locate the start of transaction data)
   - Column mapping (which columns contain date, merchant, amount)
   - Amount format (positive/negative convention, currency symbols)
   - Summary section markers (to detect end of transactions, avoid totals)
3. **LLM Fallback**: When pdfplumber extraction confidence is low (e.g., non-tabular format, image-based PDF), send extracted text to LLM with a structured prompt asking for JSON output

### LLM Integration

**Decision**: Optional, configurable via environment variable. Support Gemini API and Claude API.

**Rationale**: LLM provides resilience against format changes without code updates. However, it adds latency and cost, so it's used only as a fallback.

**Approach**:
- Extract raw text from PDF using pdfplumber
- If primary parsing fails or confidence is below threshold (< 0.7), invoke LLM
- LLM prompt includes: bank name, extracted text, expected JSON schema
- LLM response is validated against schema before use
- Results flagged as "LLM-parsed" for user review with confidence score

## 4. Bank Parser Architecture (Strategy Pattern)

### Decision: Abstract base class + per-bank implementations + auto-discovery registry

**Rationale**: Each bank has distinct email patterns, PDF layouts, and table formats. A Strategy pattern isolates bank-specific logic while the core scanning/import pipeline remains unchanged. Auto-discovery via a registry makes adding new banks zero-configuration.

### Architecture

```
BankStatementParser (ABC)
├── bank_code: str                      # Unique identifier (e.g., "CTBC")
├── bank_name: str                      # Display name (e.g., "中國信託")
├── email_query: str                    # Gmail search query
├── password_hint: str                  # Password convention description
├── parse_statement(pdf_path) -> list[ParsedStatementTransaction]
├── detect_billing_period(pdf_path) -> tuple[date, date]
└── validate_result(transactions) -> float  # Confidence score 0-1
```

### Registry Pattern

```python
# bank_parsers/__init__.py
PARSER_REGISTRY: dict[str, type[BankStatementParser]] = {}

def register_parser(cls):
    """Decorator to auto-register bank parsers."""
    PARSER_REGISTRY[cls.bank_code] = cls
    return cls

def get_parser(bank_code: str) -> BankStatementParser:
    """Get parser instance by bank code."""
    return PARSER_REGISTRY[bank_code]()

def get_all_parsers() -> list[BankStatementParser]:
    """Get all registered parsers."""
    return [cls() for cls in PARSER_REGISTRY.values()]
```

Adding a new bank requires only creating a new file in `bank_parsers/` with the `@register_parser` decorator.

## 5. Credential Encryption

### Decision: cryptography library with Fernet (AES-128-CBC + HMAC)

**Rationale**: Fernet provides authenticated encryption (encryption + integrity verification) and is the recommended approach from the `cryptography` library for encrypting application secrets at rest. Simple API, well-audited.

**Alternatives considered**:
- **AES-GCM via cryptography.hazmat**: Lower-level, requires managing nonces. Rejected for complexity without meaningful benefit for this use case.
- **Python keyring**: System-level credential storage. Rejected because it's platform-dependent and doesn't work well in containerized/server environments.
- **HashiCorp Vault**: Enterprise-grade secrets management. Rejected as overkill for single-user application.

### Implementation

- Encryption key: Derived from `GMAIL_ENCRYPTION_KEY` environment variable using PBKDF2
- Stored encrypted: OAuth2 tokens, PDF passwords
- Key rotation: Not needed for MVP; can be added later

## 6. Scheduling

### Decision: APScheduler with SQLAlchemy job store

**Rationale**: APScheduler is a lightweight, well-maintained Python scheduler that supports cron-style scheduling, persistent job storage (survives server restarts), and integrates well with FastAPI's async architecture.

**Alternatives considered**:
- **Celery + Redis**: Full-featured task queue. Rejected as overkill — adds Redis dependency for a simple recurring scan job.
- **cron**: System-level scheduling. Rejected because it's not portable and requires external configuration.
- **asyncio.create_task with sleep**: Simple but doesn't survive server restarts. Rejected for reliability.

### Implementation

- Job store: PostgreSQL (via SQLAlchemy, shares existing connection)
- Default schedule: Disabled (user must enable)
- Options: Daily (configurable hour) or Weekly (configurable day + hour)
- Job execution: Calls `gmail_import_service.execute_scan()` with the user's configured banks

## 7. Integration with Existing ImportService

### Decision: Reuse existing ImportService.execute_import() and CategorySuggester

**Rationale**: The existing import pipeline (account mapping, duplicate detection, atomic import, audit logging) is exactly what's needed. The Gmail feature adds a new *source* (Gmail PDF → parsed transactions) that feeds into the same pipeline.

### Integration Points

1. **ImportType enum**: Add `GMAIL_CC` value to existing `ImportType`
2. **ImportSession**: Reuse existing model, add `email_message_id` field for audit trail
3. **CategorySuggester**: Reuse as-is — merchant names from PDF statements match the same keyword patterns
4. **ImportService.execute_import()**: Pass parsed transactions (from PDF) through the same pipeline as CSV imports
5. **ImportService.find_duplicates()**: Reuse for transaction-level duplicate detection

### New Components (not reused)

- **GmailService**: Gmail API client (search, download, auth) — completely new
- **PdfParser**: PDF decryption + text extraction — completely new
- **BankStatementParser**: Per-bank PDF parsing — completely new
- **GmailImportService**: Orchestration layer connecting Gmail → PDF → Parser → ImportService — new
- **StatementScanJob/DiscoveredStatement**: New models for tracking scan jobs and discovered statements

## 8. Security Considerations

### Data Privacy

- Gmail API scope is read-only (`gmail.readonly`) — system cannot modify or delete emails
- OAuth2 credentials stored encrypted in database, not in filesystem
- PDF passwords stored encrypted using Fernet
- PDF files processed in memory or temporary directory, cleaned up immediately after parsing
- LLM calls (when used) send only extracted text, not raw PDF binary
- No financial data transmitted to external services except optional LLM API

### Authentication

- Google OAuth2 with minimum required scope
- OAuth2 callback validates state parameter to prevent CSRF
- Token refresh handled automatically; failed refresh triggers re-authorization prompt

### Secrets Management

- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET`: Environment variables for OAuth2 app credentials
- `GMAIL_ENCRYPTION_KEY`: Environment variable for encrypting stored tokens and passwords
- No secrets hardcoded; `.env` file for local development (gitignored)
