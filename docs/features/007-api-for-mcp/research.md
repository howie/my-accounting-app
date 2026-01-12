# Research: MCP API 對話式記帳介面

**Feature**: 007-api-for-mcp
**Date**: 2026-01-11

## 1. MCP Python SDK Selection

### Decision: Use official `mcp` Python SDK with FastMCP

### Rationale

- Official Anthropic-maintained SDK with high reliability
- FastMCP provides decorator-based tool definitions similar to FastAPI
- Native support for streamable-http transport (integrates with existing web server)
- Active development with comprehensive documentation
- Benchmark score: 89.2 (highest among options)

### Alternatives Considered

| Option                | Pros                          | Cons                                          | Why Rejected                     |
| --------------------- | ----------------------------- | --------------------------------------------- | -------------------------------- |
| mcp-use framework     | More features (3134 snippets) | Heavier dependency, overkill for simple tools | Over-engineered for our use case |
| Custom implementation | Full control                  | Maintenance burden, protocol compliance risk  | Not worth the effort             |

### Implementation Notes

```python
# Basic FastMCP setup
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("LedgerOne Accounting", json_response=True)

@mcp.tool()
def create_transaction(
    amount: float,
    from_account: str,
    to_account: str,
    description: str,
    date: str | None = None,
    notes: str | None = None
) -> dict:
    """Create a new accounting transaction."""
    # Implementation wraps existing TransactionService
    pass
```

## 2. FastAPI Integration Approach

### Decision: Mount MCP as Starlette sub-application

### Rationale

- MCP SDK's streamable-http transport is ASGI-compatible
- Can mount alongside existing FastAPI routes
- Shares application lifecycle (database connections, services)
- Single deployment artifact

### Alternatives Considered

| Option           | Pros          | Cons                                          | Why Rejected                 |
| ---------------- | ------------- | --------------------------------------------- | ---------------------------- |
| Separate process | Isolation     | Complexity, IPC overhead, separate deployment | Overkill for single-user app |
| stdio transport  | Simpler setup | Requires separate process spawning            | Not web-compatible           |

### Implementation Notes

```python
# Mount MCP to existing FastAPI app
from starlette.routing import Mount

app = FastAPI()

# Existing API routes
app.include_router(transactions_router)
app.include_router(accounts_router)

# Mount MCP server
app.mount("/mcp", mcp.streamable_http_app())
```

## 3. Authentication Strategy

### Decision: Bearer token in Authorization header

### Rationale

- Standard HTTP authentication pattern
- Compatible with MCP client configurations
- Long-lived tokens simplify AI assistant setup
- Revocation provides security without expiration complexity

### Token Design

- **Format**: UUID v4 (32 hex characters with dashes)
- **Storage**: Hashed in database (SHA-256)
- **Metadata**: Name, created_at, last_used_at, user_id
- **Revocation**: Soft delete with revoked_at timestamp

### Alternatives Considered

| Option          | Pros              | Cons                             | Why Rejected    |
| --------------- | ----------------- | -------------------------------- | --------------- |
| OAuth2          | Industry standard | Complex for personal use         | Over-engineered |
| API key in URL  | Simple            | Security risk (logs, referrer)   | Bad practice    |
| Session cookies | Browser-native    | Not suitable for CLI/API clients | Wrong use case  |

## 4. MCP Tool Design

### Decision: Five core tools with consistent response format

### Tools Defined

| Tool                 | Purpose                        | Parameters                                                       |
| -------------------- | ------------------------------ | ---------------------------------------------------------------- |
| `create_transaction` | Record expense/income/transfer | amount, from_account, to_account, description, date?, notes?     |
| `list_accounts`      | Get all accounts with balances | ledger_id?, type?                                                |
| `get_account`        | Get single account details     | account_id or name, ledger_id?                                   |
| `list_transactions`  | Query transaction history      | ledger_id?, account_id?, start_date?, end_date?, limit?, offset? |
| `list_ledgers`       | Get available ledgers          | (none)                                                           |

### Response Format

```python
# Success response
{
    "success": True,
    "data": { ... },
    "message": "Transaction created successfully"
}

# Error response
{
    "success": False,
    "error": {
        "code": "ACCOUNT_NOT_FOUND",
        "message": "Account '早餐' not found",
        "suggestions": ["餐飲", "早午餐", "外食"]
    }
}
```

## 5. Account Fuzzy Matching

### Decision: Simple substring + Levenshtein distance

### Rationale

- Handles common typos and partial names
- No external ML dependencies
- Fast enough for small account sets (<100 accounts)

### Implementation Notes

```python
from difflib import SequenceMatcher

def find_similar_accounts(query: str, accounts: list[Account], threshold: float = 0.6) -> list[Account]:
    """Find accounts with similar names."""
    results = []
    for account in accounts:
        ratio = SequenceMatcher(None, query.lower(), account.name.lower()).ratio()
        if ratio >= threshold or query.lower() in account.name.lower():
            results.append((account, ratio))
    return [a for a, _ in sorted(results, key=lambda x: -x[1])[:5]]
```

### Alternatives Considered

| Option        | Pros                  | Cons                       | Why Rejected                 |
| ------------- | --------------------- | -------------------------- | ---------------------------- |
| Elasticsearch | Powerful fuzzy search | Heavy dependency, overkill | Too complex for account list |
| ML embeddings | Semantic matching     | Requires model, latency    | Premature optimization       |

## 6. Date Handling

### Decision: AI assistant handles relative date parsing

### Rationale

- Per spec: "AI assistants are responsible for natural language understanding"
- MCP API receives ISO date strings (YYYY-MM-DD)
- Simpler API contract, less ambiguity
- AI assistants (Claude, ChatGPT) excel at date parsing

### Implementation Notes

- API accepts: `date: str | None` in ISO format
- Default: Today's date if not provided
- Validation: Must be valid date, not in future (configurable)

## 7. Dependencies

### New Python Dependencies

```toml
[project.dependencies]
# Add to existing
mcp = ">=1.0.0"  # Model Context Protocol SDK
```

### No New Frontend Dependencies

- Token management UI uses existing React + TanStack Query patterns

## Summary

All technical decisions align with the principle of simplicity while meeting functional requirements. The MCP SDK provides a clean, decorator-based API that integrates naturally with the existing FastAPI codebase. Authentication uses straightforward bearer tokens, and the tool design mirrors the existing service layer methods.
