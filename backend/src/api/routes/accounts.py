"""Account API routes.

Based on contracts/account_service.md
Supports hierarchical account structure.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from src.api.deps import get_current_user_id, get_session
from src.models.account import AccountType
from src.schemas.account import (
    AccountCreate,
    AccountListItem,
    AccountRead,
    AccountUpdate,
)
from src.services.account_service import AccountService
from src.services.ledger_service import LedgerService

router = APIRouter(prefix="/ledgers/{ledger_id}/accounts", tags=["accounts"])


def get_account_service(
    session: Annotated[Session, Depends(get_session)]
) -> AccountService:
    """Dependency to get AccountService instance."""
    return AccountService(session)


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


@router.post("", status_code=status.HTTP_201_CREATED, response_model=AccountRead)
def create_account(
    data: AccountCreate,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[AccountService, Depends(get_account_service)],
) -> AccountRead:
    """Create a new account in the ledger."""
    # Validate input
    if not data.name or not data.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty",
        )

    try:
        account = service.create_account(ledger_id, data)
    except ValueError as e:
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return AccountRead(
        id=account.id,
        ledger_id=account.ledger_id,
        name=account.name,
        type=account.type,
        balance=account.balance,
        is_system=account.is_system,
        parent_id=account.parent_id,
        depth=account.depth,
        has_children=service.has_children(account.id),
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.get("", response_model=dict)
def list_accounts(
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[AccountService, Depends(get_account_service)],
    type: Annotated[AccountType | None, Query()] = None,
) -> dict:
    """List all accounts for a ledger with calculated balances."""
    accounts = service.get_accounts(ledger_id, type_filter=type)
    return {
        "data": [
            AccountListItem(
                id=a.id,
                name=a.name,
                type=a.type,
                balance=service.calculate_balance(a.id),
                is_system=a.is_system,
                parent_id=a.parent_id,
                depth=a.depth,
                has_children=service.has_children(a.id),
            )
            for a in accounts
        ]
    }


@router.get("/tree", response_model=dict)
def get_account_tree(
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[AccountService, Depends(get_account_service)],
    type: Annotated[AccountType | None, Query()] = None,
) -> dict:
    """Get hierarchical tree of accounts for a ledger.

    Returns only root-level accounts with nested children.
    Each node includes aggregated balance from all descendants.
    """
    tree = service.get_account_tree(ledger_id, type_filter=type)
    return {"data": tree}


@router.get("/{account_id}", response_model=AccountRead)
def get_account(
    account_id: uuid.UUID,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[AccountService, Depends(get_account_service)],
) -> AccountRead:
    """Retrieve a single account with balance."""
    account = service.get_account(account_id, ledger_id)
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
    return AccountRead(
        id=account.id,
        ledger_id=account.ledger_id,
        name=account.name,
        type=account.type,
        balance=service.calculate_balance(account.id),
        is_system=account.is_system,
        parent_id=account.parent_id,
        depth=account.depth,
        has_children=service.has_children(account.id),
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.patch("/{account_id}", response_model=AccountRead)
def update_account(
    account_id: uuid.UUID,
    data: AccountUpdate,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[AccountService, Depends(get_account_service)],
) -> AccountRead:
    """Update account name."""
    try:
        account = service.update_account(account_id, ledger_id, data)
    except ValueError as e:
        if "system account" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        if "already exists" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )

    return AccountRead(
        id=account.id,
        ledger_id=account.ledger_id,
        name=account.name,
        type=account.type,
        balance=service.calculate_balance(account.id),
        is_system=account.is_system,
        parent_id=account.parent_id,
        depth=account.depth,
        has_children=service.has_children(account.id),
        created_at=account.created_at,
        updated_at=account.updated_at,
    )


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(
    account_id: uuid.UUID,
    ledger_id: Annotated[uuid.UUID, Depends(verify_ledger_exists)],
    service: Annotated[AccountService, Depends(get_account_service)],
) -> None:
    """Delete an account."""
    try:
        deleted = service.delete_account(account_id, ledger_id)
    except ValueError as e:
        if "system account" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        if "has transactions" in str(e) or "has child accounts" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(e),
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found",
        )
