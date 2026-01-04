"""Database session management."""

from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from src.core.config import get_settings

settings = get_settings()

engine = create_engine(
    settings.database_url,
    echo=settings.is_development,
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    """Create all database tables."""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session."""
    with Session(engine) as session:
        yield session
