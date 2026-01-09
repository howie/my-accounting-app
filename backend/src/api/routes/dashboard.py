"""Dashboard API routes.

Based on contracts/dashboard_service.md for feature 002-ui-layout-dashboard.
Provides read-only endpoints for dashboard and sidebar data.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from src.api.deps import SessionDep
from src.services.dashboard_service import DashboardService

router = APIRouter(tags=["dashboard"])


@router.get("/ledgers/{ledger_id}/dashboard")
def get_dashboard(
    ledger_id: uuid.UUID,
    session: SessionDep,
) -> dict:
    """Get aggregated dashboard data for a ledger.

    Returns total assets, current month income/expenses, and 6-month trends.
    """
    service = DashboardService(session)
    try:
        return service.get_dashboard_summary(ledger_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "LEDGER_NOT_FOUND", "message": str(e)}},
        )


@router.get("/ledgers/{ledger_id}/accounts/by-category")
def get_accounts_by_category(
    ledger_id: uuid.UUID,
    session: SessionDep,
) -> dict:
    """Get all accounts grouped by category type.

    Returns accounts in fixed order: ASSET, LIABILITY, INCOME, EXPENSE.
    Each category includes accounts sorted by sort_order (user-defined), then name.
    """
    service = DashboardService(session)
    try:
        return service.get_accounts_by_category(ledger_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": {"code": "LEDGER_NOT_FOUND", "message": str(e)}},
        )


@router.get("/accounts/{account_id}/transactions")
def get_account_transactions(
    account_id: uuid.UUID,
    session: SessionDep,
    page: Annotated[int, Query(ge=1, description="Page number (1-indexed)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, description="Items per page (max 100)")] = 50,
) -> dict:
    """Get paginated transactions for an account.

    Returns transactions sorted by date (newest first) with pagination info.
    """
    service = DashboardService(session)
    try:
        return service.get_account_transactions(account_id, page, page_size)
    except ValueError as e:
        error_message = str(e)
        if "not found" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {"code": "ACCOUNT_NOT_FOUND", "message": error_message}},
            )
        elif "page" in error_message.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "INVALID_PAGE", "message": error_message}},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {"code": "BAD_REQUEST", "message": error_message}},
            )
