"""Chat API endpoints for AI assistant."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlmodel import Session

from src.api.deps import CurrentUserDep, get_session
from src.schemas.chat import ChatRequest, ChatResponse
from src.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages", response_model=ChatResponse)
def send_message(
    request: ChatRequest,
    session: Annotated[Session, Depends(get_session)],
    user: CurrentUserDep,
) -> ChatResponse:
    """Send a message to the AI assistant.

    The AI can help with:
    - Creating transactions
    - Listing accounts and balances
    - Querying transaction history
    - Managing ledgers
    """
    service = ChatService(session, user)
    return service.chat(
        message=request.message,
        ledger_id=str(request.ledger_id) if request.ledger_id else None,
    )
