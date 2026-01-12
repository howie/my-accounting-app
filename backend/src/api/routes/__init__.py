"""API routes for LedgerOne."""

from fastapi import APIRouter

from src.api.routes import (
    accounts,
    dashboard,
    import_routes,
    ledgers,
    templates,
    tokens,
    transactions,
    users,
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

# Feature 007: API Tokens for MCP
api_router.include_router(tokens.router)
