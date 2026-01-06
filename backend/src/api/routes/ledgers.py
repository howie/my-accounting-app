"""Ledger API routes.

Based on contracts/ledger_service.md
"""

import uuid
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from src.api.deps import get_session, get_current_user_id
from src.services.ledger_service import LedgerService
from src.schemas.ledger import LedgerCreate, LedgerRead, LedgerListItem, LedgerUpdate

router = APIRouter(prefix="/ledgers", tags=["ledgers"])


def get_ledger_service(
    session: Annotated[Session, Depends(get_session)]
) -> LedgerService:
    """Dependency to get LedgerService instance."""
    return LedgerService(session)


@router.post("", status_code=status.HTTP_201_CREATED, response_model=LedgerRead)
def create_ledger(
    data: LedgerCreate,
    service: Annotated[LedgerService, Depends(get_ledger_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> LedgerRead:
    """Create a new ledger with initial Cash and Equity accounts."""
    # Validate input
    if not data.name or not data.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty",
        )

    if data.initial_balance < Decimal("0"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Initial balance cannot be negative",
        )

    ledger = service.create_ledger(user_id, data)
    return LedgerRead(
        id=ledger.id,
        user_id=ledger.user_id,
        name=ledger.name,
        initial_balance=ledger.initial_balance,
        created_at=ledger.created_at,
    )


@router.get("", response_model=dict)
def list_ledgers(
    service: Annotated[LedgerService, Depends(get_ledger_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> dict:
    """List all ledgers for the authenticated user."""
    ledgers = service.get_ledgers(user_id)
    return {
        "data": [
            LedgerListItem(
                id=l.id,
                name=l.name,
                initial_balance=l.initial_balance,
                created_at=l.created_at,
            )
            for l in ledgers
        ]
    }


@router.get("/{ledger_id}", response_model=LedgerRead)
def get_ledger(
    ledger_id: uuid.UUID,
    service: Annotated[LedgerService, Depends(get_ledger_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> LedgerRead:
    """Retrieve a single ledger by ID."""
    ledger = service.get_ledger(ledger_id, user_id)
    if not ledger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger not found",
        )
    return LedgerRead(
        id=ledger.id,
        user_id=ledger.user_id,
        name=ledger.name,
        initial_balance=ledger.initial_balance,
        created_at=ledger.created_at,
    )


@router.patch("/{ledger_id}", response_model=LedgerRead)
def update_ledger(
    ledger_id: uuid.UUID,
    data: LedgerUpdate,
    service: Annotated[LedgerService, Depends(get_ledger_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> LedgerRead:
    """Update ledger name."""
    # Validate input
    if data.name is not None and not data.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty",
        )

    ledger = service.update_ledger(ledger_id, user_id, data)
    if not ledger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger not found",
        )
    return LedgerRead(
        id=ledger.id,
        user_id=ledger.user_id,
        name=ledger.name,
        initial_balance=ledger.initial_balance,
        created_at=ledger.created_at,
    )


@router.delete("/{ledger_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ledger(
    ledger_id: uuid.UUID,
    service: Annotated[LedgerService, Depends(get_ledger_service)],
    user_id: Annotated[uuid.UUID, Depends(get_current_user_id)],
) -> None:
    """Delete a ledger and all associated accounts/transactions."""
    deleted = service.delete_ledger(ledger_id, user_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ledger not found",
        )
