"""Transaction API routes.

Based on contracts/transaction_service.md
"""

import uuid
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from src.api.deps import get_current_user_id, get_session
from src.models.transaction import TransactionType
from src.schemas.transaction import (
    PaginatedTransactions,
    TransactionCreate,
    TransactionRead,
    TransactionUpdate,
)
from src.services.ledger_service import LedgerService
from src.services.transaction_service import TransactionService

router = APIRouter(prefix="/ledgers/{ledger_id}/transactions", tags=["transactions"])


def get_transaction_service(
    session: Annotated[Session, Depends(get_session)]
) -> TransactionService:
    """Dependency to get TransactionService instance."""
    return TransactionService(session)


def get_ledger_service(
    session: Annotated[Session, Depends(get_session)]
) -> LedgerService:
    """Dependency to get LedgerService instance."""
    return LedgerService(session)


def verify_ledger_exists(
    ledger_id: uuid.UUID,
    ledger_service: Annotated[LedgerService, Depends(get_ledger_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> uuid.UUID:
    """Verify ledger exists and belongs to user."""
    ledger = ledger_service.get_ledger(ledger_id, user_id)
    if not ledger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger not found",
        )
    return ledger_id


@router.post("", status_code=status.HTTP_201_CREATED, response_model=TransactionRead)
def create_transaction(
    data: TransactionCreate,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionRead:
    """Create a new transaction."""
    try:
        transaction = service.create_transaction(ledger_id, data)
    except ValueError as e:
        error_msg = str(e).lower()
        if "same account" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="From and to accounts must be different",
            )
        if "not found" in error_msg or "does not belong" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        if "type" in error_msg or "must be" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Return full transaction details
    return service.get_transaction(transaction.id, ledger_id)


@router.get("", response_model=PaginatedTransactions)
def list_transactions(
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    cursor: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query(description="Search in description")] = None,
    from_date: Annotated[date | None, Query(description="Filter from date (inclusive)")] = None,
    to_date: Annotated[date | None, Query(description="Filter to date (inclusive)")] = None,
    account_id: Annotated[uuid.UUID | None, Query(description="Filter by account")] = None,
    transaction_type: Annotated[TransactionType | None, Query(description="Filter by type")] = None,
) -> PaginatedTransactions:
    """List transactions for a ledger with pagination and filters."""
    return service.get_transactions(
        ledger_id,
        limit=limit,
        cursor=cursor,
        search=search,
        from_date=from_date,
        to_date=to_date,
        account_id=account_id,
        transaction_type=transaction_type,
    )


@router.get("/{transaction_id}", response_model=TransactionRead)
def get_transaction(
    transaction_id: uuid.UUID,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionRead:
    """Retrieve a single transaction."""
    transaction = service.get_transaction(transaction_id, ledger_id)
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
    return transaction


@router.put("/{transaction_id}", response_model=TransactionRead)
def update_transaction(
    transaction_id: uuid.UUID,
    data: TransactionUpdate,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> TransactionRead:
    """Update a transaction (full replacement)."""
    try:
        transaction = service.update_transaction(transaction_id, ledger_id, data)
    except ValueError as e:
        error_msg = str(e).lower()
        if "same account" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="From and to accounts must be different",
            )
        if "not found" in error_msg or "does not belong" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(
    transaction_id: uuid.UUID,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[TransactionService, Depends(get_transaction_service)],
) -> None:
    """Delete a transaction."""
    deleted = service.delete_transaction(transaction_id, ledger_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )
