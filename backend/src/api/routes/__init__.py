"""API routes for LedgerOne."""

from fastapi import APIRouter

from src.api.routes import (
    accounts,
    chat,
    dashboard,
    export,
    gmail_import_routes,
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

# Feature 011: Gmail CC Statement Import
api_router.include_router(gmail_import_routes.router, tags=["Gmail Import"])

# Feature 008: Data Export
api_router.include_router(export.router, prefix="/export", tags=["Export"])

# Feature 007: API Tokens for MCP
api_router.include_router(tokens.router)

# AI Chat Assistant
api_router.include_router(chat.router)

# Utilities (Health Check)
api_router.include_router(utils.router, tags=["Utils"])
