"""API routes for LedgerOne."""

from fastapi import APIRouter

from src.api.routes import ledgers, accounts, transactions, users

api_router = APIRouter()

# Phase 3 (US1): Ledgers and Accounts
api_router.include_router(ledgers.router)
api_router.include_router(accounts.router)

# Phase 4 (US2): Transactions
api_router.include_router(transactions.router)

# Phase 6 (US4): Users
api_router.include_router(users.router)
