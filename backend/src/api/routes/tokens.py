"""API Token management endpoints.

Based on contracts/api-tokens.md from 007-api-for-mcp feature.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlmodel import Session

from src.api.deps import get_session
from src.models.user import User
from src.schemas.api_token import (
    TokenCreate,
    TokenListItem,
    TokenListResponse,
    TokenResponse,
    TokenRevokeResponse,
)
from src.services.api_token_service import ApiTokenService

router = APIRouter(prefix="/tokens", tags=["tokens"])


def get_token_user_id(
    session: Annotated[Session, Depends(get_session)],
    x_user_id: Annotated[str | None, Header(alias="X-User-ID")] = None,
) -> uuid.UUID:
    """Get user ID for token operations.

    Supports X-User-ID header for testing, falls back to first user (single-user mode).
    """
    if x_user_id:
        try:
            return uuid.UUID(x_user_id)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-User-ID header format",
            ) from e

    # Fall back to single-user mode
    user = session.query(User).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user found",
        )
    return user.id


@router.get("", response_model=TokenListResponse)
def list_tokens(
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[uuid.UUID, Depends(get_token_user_id)],
) -> TokenListResponse:
    """List all API tokens for the current user."""
    service = ApiTokenService(session)
    tokens = service.list_tokens(user_id)

    return TokenListResponse(
        tokens=[
            TokenListItem(
                id=t.id,
                name=t.name,
                token_prefix=t.token_prefix,
                created_at=t.created_at,
                last_used_at=t.last_used_at,
                is_revoked=t.revoked_at is not None,
            )
            for t in tokens
        ]
    )


@router.post("", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def create_token(
    data: TokenCreate,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[uuid.UUID, Depends(get_token_user_id)],
) -> TokenResponse:
    """Create a new API token.

    The full token is only returned once. Store it securely.
    """
    service = ApiTokenService(session)

    try:
        result = service.create_token(user_id, data.name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    return TokenResponse(
        id=result.token.id,
        name=result.token.name,
        token=result.raw_token,
        token_prefix=result.token.token_prefix,
        created_at=result.token.created_at,
    )


@router.delete("/{token_id}", response_model=TokenRevokeResponse)
def revoke_token(
    token_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    user_id: Annotated[uuid.UUID, Depends(get_token_user_id)],
) -> TokenRevokeResponse:
    """Revoke an API token.

    This is a soft delete - the token is marked as revoked but not removed.
    """
    service = ApiTokenService(session)

    # Get token first to return its details
    token = service.get_token(token_id, user_id)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TOKEN_NOT_FOUND", "message": "Token not found or already revoked"},
        )

    success = service.revoke_token(token_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "TOKEN_NOT_FOUND", "message": "Token not found or already revoked"},
        )

    # Refresh to get the revoked_at timestamp
    session.refresh(token)

    return TokenRevokeResponse(
        id=token.id,
        name=token.name,
        revoked_at=token.revoked_at,
    )
