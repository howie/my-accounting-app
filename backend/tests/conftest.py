"""Pytest configuration and fixtures for backend tests."""

import os

# Set test environment BEFORE any imports that read settings
os.environ["ENVIRONMENT"] = "test"

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.api.deps import get_session
from src.api.main import app

# Import all models to register them with SQLModel metadata
from src.models import (  # noqa: F401
    Account,
    AuditLog,
    Ledger,
    Transaction,
    TransactionTemplate,
    User,
)


@pytest.fixture(name="engine")
def engine_fixture() -> Generator[Any, None, None]:
    """Create an in-memory SQLite engine for testing."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    yield engine
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(name="session")
def session_fixture(engine: Any) -> Generator[Session, None, None]:
    """Create a new database session for testing."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create a test client with overridden database session."""

    def get_session_override() -> Generator[Session, None, None]:
        yield session

    app.dependency_overrides[get_session] = get_session_override
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "display_name": "Test User",
    }


@pytest.fixture
def sample_ledger_data() -> dict[str, Any]:
    """Sample ledger data for testing."""
    return {
        "name": "Personal Finance",
        "description": "My personal finance ledger",
        "currency": "USD",
    }


@pytest.fixture
def sample_account_data() -> dict[str, Any]:
    """Sample account data for testing."""
    return {
        "code": "1000",
        "name": "Cash",
        "account_type": "asset",
        "description": "Cash on hand",
    }


@pytest.fixture
def sample_transaction_data() -> dict[str, Any]:
    """Sample transaction data for testing."""
    return {
        "date": "2024-01-15",
        "description": "Initial deposit",
        "amount": "1000.00",
        "memo": "Opening balance",
    }
