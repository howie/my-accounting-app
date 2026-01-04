"""FastAPI dependency injection."""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session

from src.db.session import get_session
from src.models.user import User

# Database session dependency
SessionDep = Annotated[Session, Depends(get_session)]


def get_current_user(session: SessionDep) -> User:
    """Get current user.

    For MVP, this returns the default user (single-user mode).
    Full authentication will be implemented in a future feature.
    """
    # Query for the first user (MVP: single-user mode)
    user = session.query(User).first()
    if not user:
        # Create default user if none exists
        user = User(email="user@localhost")
        session.add(user)
        session.commit()
        session.refresh(user)
    return user


def get_current_user_id(session: SessionDep) -> uuid.UUID:
    """Get current user's ID.

    Convenience dependency that returns just the user ID.
    """
    user = get_current_user(session)
    return user.id


# Current user dependency
CurrentUserDep = Annotated[User, Depends(get_current_user)]
