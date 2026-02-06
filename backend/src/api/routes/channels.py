"""Channel binding API endpoints.

Based on contracts/channel-binding-api.yaml for 012-ai-multi-channel feature.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from src.api.deps import get_current_user, get_session
from src.models.user import User
from src.schemas.channel import (
    ChannelBindingRead,
    GenerateCodeRequest,
    GenerateCodeResponse,
    VerifyCodeRequest,
)
from src.services.channel_binding_service import ChannelBindingService

router = APIRouter(prefix="/channels", tags=["channels"])


def _get_service(session: Session) -> ChannelBindingService:
    return ChannelBindingService(session)


@router.get("/bindings", response_model=list[ChannelBindingRead])
def list_bindings(
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
    include_inactive: bool = False,
) -> list[ChannelBindingRead]:
    """List channel bindings for the current user."""
    service = _get_service(session)
    bindings = service.list_bindings(user_id=user.id, include_inactive=include_inactive)
    return [ChannelBindingRead.model_validate(b) for b in bindings]


@router.post("/bindings/generate-code", response_model=GenerateCodeResponse)
def generate_code(
    data: GenerateCodeRequest,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> GenerateCodeResponse:
    """Generate a 6-digit verification code for channel binding."""
    service = _get_service(session)
    code = service.generate_code(
        user_id=user.id,
        channel_type=data.channel_type,
        default_ledger_id=data.default_ledger_id,
    )
    return GenerateCodeResponse(code=code)


@router.post("/bindings/verify-code", response_model=ChannelBindingRead)
def verify_code(
    data: VerifyCodeRequest,
    session: Annotated[Session, Depends(get_session)],
) -> ChannelBindingRead:
    """Verify a binding code (called from bot side).

    No authentication required — the code itself is the proof.
    """
    service = _get_service(session)
    binding = service.verify_code(
        code=data.code,
        external_user_id=data.external_user_id,
        display_name=data.display_name,
    )
    if binding is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid, expired, or already used code",
        )
    return ChannelBindingRead.model_validate(binding)


@router.delete("/bindings/{binding_id}")
def unbind(
    binding_id: uuid.UUID,
    session: Annotated[Session, Depends(get_session)],
    user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Unbind a channel (soft delete)."""
    service = _get_service(session)
    success = service.unbind(binding_id=binding_id, user_id=user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Binding not found",
        )
    return {"status": "unbound"}
