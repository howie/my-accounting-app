# Implementation Plan: MCP API 對話式記帳介面

**Branch**: `007-api-for-mcp` | **Date**: 2026-01-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/docs/features/007-api-for-mcp/spec.md`

## Summary

Implement MCP (Model Context Protocol) server integrated into the existing FastAPI backend, enabling AI assistants (Claude, ChatGPT) to perform accounting operations through natural language conversations. The MCP server exposes tools for creating transactions, querying accounts/balances, listing transactions, and managing ledgers. Authentication uses long-lived bearer tokens that users generate from the web interface.

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x (Frontend for token management UI)
**Primary Dependencies**: FastAPI, mcp (Python SDK), SQLModel, Pydantic
**Storage**: PostgreSQL 16 (existing schema from 001-core-accounting)
**Testing**: pytest, pytest-asyncio, httpx
**Target Platform**: Linux server (Docker), macOS (development)
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Transaction creation < 2 seconds, balance queries < 1 second
**Constraints**: Integrated into existing FastAPI process, no rate limiting for initial release
**Scale/Scope**: Single user, multiple AI assistants per user, ~100 transactions/day

## Constitution Check

_GATE: Must pass before Phase 0 research. Re-check after Phase 1 design._

### I. Data-First Design (NON-NEGOTIABLE)

- [x] Does this feature preserve financial accuracy (calculations correct to the cent)?
  - Reuses existing transaction service with validated double-entry bookkeeping
- [x] Are audit trails maintained (all modifications logged with timestamp/reason)?
  - All MCP-created transactions marked with source="mcp" in audit log
- [x] Is data loss prevented (confirmations + backups for destructive operations)?
  - MCP API is read + create only; no delete/update operations exposed
- [x] Is input validation enforced (amounts, dates, account references)?
  - All inputs validated by existing Pydantic schemas before persistence
- [x] Are destructive operations reversible?
  - N/A - no destructive operations in this feature

**Violations**: None

### II. Test-First Development (NON-NEGOTIABLE)

- [x] Will tests be written BEFORE implementation?
- [x] Will tests be reviewed/approved before coding?
- [x] Are contract tests planned for service boundaries?
  - MCP tool contracts tested via pytest
- [x] Are integration tests planned for multi-account transactions?
  - Integration tests for create_transaction tool
- [x] Are edge case tests planned (rounding, currency, date boundaries)?
  - Tests for invalid accounts, malformed amounts, fuzzy matching

**Violations**: None

### III. Financial Accuracy & Audit Trail

- [x] Does design maintain double-entry bookkeeping (debits = credits)?
  - Reuses existing TransactionService which enforces this
- [x] Are transactions immutable once posted (void-and-reenter only)?
  - MCP API only creates; no modification endpoints
- [x] Are calculations traceable to source transactions?
  - Balance queries trace through existing account balance logic
- [x] Are timestamps tracked (created, modified, business date)?
  - Existing Transaction model has created_at, updated_at, date fields
- [x] Is change logging implemented (who, what, when, why)?
  - AuditLog entries created with source="mcp" and token reference

**Violations**: None

### IV. Simplicity & Maintainability

- [x] Is this feature actually needed (not speculative)?
  - User-requested feature for conversational accounting
- [x] Is the design clear over clever (human-auditable)?
  - Simple MCP tool decorators wrapping existing services
- [x] Are abstractions minimized (especially for financial calculations)?
  - Direct calls to existing service layer, no new abstractions
- [x] Are complex business rules documented with accounting references?
  - Transaction creation logic already documented in 001-core-accounting

**Violations**: None

### V. Cross-Platform Consistency

- [x] Will calculations produce identical results across platforms?
  - Same backend logic used by web UI and MCP
- [x] Is data format compatible between desktop and web?
  - Single PostgreSQL database, shared schema
- [x] Are platform-specific features clearly documented?
  - MCP is AI-assistant-specific interface, documented in spec
- [x] Do workflows follow consistent UX patterns?
  - N/A - no direct user UI in this feature
- [x] Does cloud sync maintain transaction ordering?
  - N/A - single database, no sync required

**Violations**: None

**Overall Assessment**: PASS

## Project Structure

### Documentation (this feature)

```text
docs/features/007-api-for-mcp/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (MCP tool schemas)
└── checklists/          # Quality checklists
```

### Source Code (repository root)

```text
backend/
├── src/
│   ├── api/
│   │   └── mcp/                 # NEW: MCP server integration
│   │       ├── __init__.py
│   │       ├── server.py        # FastMCP server setup
│   │       ├── tools/           # MCP tool definitions
│   │       │   ├── __init__.py
│   │       │   ├── transactions.py
│   │       │   ├── accounts.py
│   │       │   └── ledgers.py
│   │       └── auth.py          # Token validation for MCP
│   ├── models/
│   │   └── api_token.py         # NEW: API token model
│   ├── services/
│   │   └── api_token_service.py # NEW: Token CRUD service
│   └── schemas/
│       └── api_token.py         # NEW: Token Pydantic schemas
└── tests/
    ├── unit/
    │   └── mcp/                 # MCP tool unit tests
    └── integration/
        └── mcp/                 # MCP integration tests

frontend/
├── src/
│   ├── app/
│   │   └── [ledger]/settings/
│   │       └── api-tokens/      # NEW: Token management page
│   ├── components/
│   │   └── settings/
│   │       └── ApiTokenManager.tsx  # NEW: Token list/create/revoke
│   └── lib/
│       └── api/
│           └── tokens.ts        # NEW: Token API client
└── tests/
    └── components/
        └── ApiTokenManager.test.tsx
```

**Structure Decision**: Web application structure (Option 2) - extending existing backend/frontend layout with new MCP module and token management components.
