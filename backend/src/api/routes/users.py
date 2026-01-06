"""User API routes.

Based on contracts/user_account_service.md
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from src.api.deps import get_session
from src.models.user import UserRead, UserSetup
from src.services.user_account_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(
    session: Annotated[Session, Depends(get_session)]
) -> UserService:
    """Dependency to get UserService instance."""
    return UserService(session)


@router.get("/me", response_model=UserRead)
def get_current_user(
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """Get the current user.

    In MVP mode, returns the default user, creating one if needed.
    """
    user = service.get_or_create_default_user()
    return UserRead.model_validate(user)


@router.post("/setup", status_code=status.HTTP_201_CREATED, response_model=UserRead)
def setup_user(
    data: UserSetup,
    service: Annotated[UserService, Depends(get_user_service)],
) -> UserRead:
    """Initial user setup.

    Creates the initial user for the application.
    Only callable once - returns 409 if user already exists.
    """
    try:
        user = service.setup_user(data)
        return UserRead.model_validate(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.get("/status")
def get_setup_status(
    service: Annotated[UserService, Depends(get_user_service)],
) -> dict:
    """Check if initial setup is needed.

    Returns setup_needed: true if no user exists.
    """
    return {"setup_needed": service.is_setup_needed()}
