"""User account service.

Based on contracts/user_account_service.md
"""

from sqlmodel import Session, select

from src.models.user import User, UserSetup


class UserService:
    """Service for user account operations.

    For MVP, this manages a single-user setup. Full authentication
    will be implemented in a future feature.
    """

    def __init__(self, session: Session) -> None:
        """Initialize service with database session."""
        self.session = session

    def get_current_user(self) -> User | None:
        """Get the current user.

        In MVP, returns the single default user.
        Returns None if no user exists.
        """
        statement = select(User).limit(1)
        return self.session.exec(statement).first()

    def setup_user(self, data: UserSetup) -> User:
        """Create the initial user (MVP).

        Args:
            data: User setup data with email

        Returns:
            The created user

        Raises:
            ValueError: If a user already exists (single-user mode)
        """
        # Check if user already exists
        existing = self.get_current_user()
        if existing is not None:
            raise ValueError("User already exists. Only one user allowed in MVP mode.")

        # Create the user
        user = User(email=data.email)
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def get_or_create_default_user(self) -> User:
        """Get the default user, creating if needed.

        Used for initial application setup.

        Returns:
            The existing or newly created default user
        """
        user = self.get_current_user()
        if user is not None:
            return user

        # Create default user
        user = User(email="user@localhost")
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user

    def is_setup_needed(self) -> bool:
        """Check if initial user setup is needed.

        Returns:
            True if no user exists, False otherwise
        """
        return self.get_current_user() is None
