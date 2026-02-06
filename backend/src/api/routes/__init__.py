"""API routes for LedgerOne."""

from typing import Any

from fastapi import APIRouter

from src.api.routes import (
    accounts,
    channels,
    chat,
    dashboard,
    export,
    import_routes,
    installments,  # Added
    ledgers,
    recurring,
    reports,
    tags,
    templates,
    tokens,
    transactions,
    users,
    utils,
    webhooks,  # noqa: F401 - mounted in main.py directly
)

api_router = APIRouter()

# Feature 002: Dashboard (must be registered before accounts to avoid route conflicts)
api_router.include_router(dashboard.router)

# Phase 3 (US1): Ledgers and Accounts
api_router.include_router(ledgers.router)
api_router.include_router(accounts.router)

# Phase 4 (US2): Transactions
api_router.include_router(transactions.router)

# Feature 009: Reports
api_router.include_router(reports.router)

# Feature 004: Transaction Templates
api_router.include_router(templates.router)

# Feature 010: Tags
api_router.include_router(tags.router, prefix="/tags", tags=["Tags"])

# Feature 010: Recurring Transactions
api_router.include_router(recurring.router, prefix="/recurring", tags=["Recurring"])

# Feature 010: Installments
api_router.include_router(installments.router, prefix="/installments", tags=["Installments"])

# Phase 6 (US4): Users
api_router.include_router(users.router)

# Feature 006: Data Import
api_router.include_router(import_routes.router, tags=["Import"])

# Feature 008: Data Export
api_router.include_router(export.router, prefix="/export", tags=["Export"])

# Feature 007: API Tokens for MCP
api_router.include_router(tokens.router)

# Feature 012: Channel Binding
api_router.include_router(channels.router)

# AI Chat Assistant
api_router.include_router(chat.router)

# Utilities (Health Check)
api_router.include_router(utils.router, tags=["Utils"])


# Feature 012: OpenAPI spec export for AI assistant integration
@api_router.get("/openapi-gpt-actions", tags=["AI Integration"])
def get_gpt_actions_spec() -> dict[str, Any]:
    """Get simplified OpenAPI spec for ChatGPT GPT Actions."""
    from src.api.openapi_export import generate_gpt_actions_spec

    return generate_gpt_actions_spec()
