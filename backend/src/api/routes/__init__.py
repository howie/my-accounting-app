"""API routes for LedgerOne."""

from fastapi import APIRouter

from src.api.routes import (
    accounts,
    chat,
    dashboard,
    export,
    import_routes,
    ledgers,
    templates,
    tokens,
    transactions,
    users,
    utils,
)

api_router = APIRouter()

# Feature 002: Dashboard (must be registered before accounts to avoid route conflicts)
api_router.include_router(dashboard.router)

# Phase 3 (US1): Ledgers and Accounts
api_router.include_router(ledgers.router)
api_router.include_router(accounts.router)

# Phase 4 (US2): Transactions
api_router.include_router(transactions.router)

# Feature 004: Transaction Templates
api_router.include_router(templates.router)

# Phase 6 (US4): Users
api_router.include_router(users.router)

# Feature 006: Data Import
api_router.include_router(import_routes.router, tags=["Import"])

# Feature 008: Data Export
api_router.include_router(export.router, prefix="/export", tags=["Export"])

# Feature 007: API Tokens for MCP
api_router.include_router(tokens.router)

# AI Chat Assistant
# AI Chat Assistant
api_router.include_router(chat.router)

# Utilities (Health Check)
api_router.include_router(utils.router, tags=["Utils"])
