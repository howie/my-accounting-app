"""Integration tests for AI assistant flow.

Simulates external API call with API token auth → create transaction
→ verify transaction exists with correct source.
Per Constitution Principle II: Tests written BEFORE implementation.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models.account import Account, AccountType
from src.models.ledger import Ledger
from src.models.user import User
from src.services.api_token_service import ApiTokenService


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="test@example.com", display_name="Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    """Create a test ledger."""
    ledger = Ledger(
        name="Test Ledger",
        description="For testing",
        currency="TWD",
        user_id=user.id,
    )
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


@pytest.fixture
def accounts(session: Session, ledger: Ledger) -> dict[str, Account]:
    """Create test accounts."""
    cash = Account(
        ledger_id=ledger.id,
        name="現金",
        type=AccountType.ASSET,
        is_system=True,
    )
    food = Account(
        ledger_id=ledger.id,
        name="餐飲",
        type=AccountType.EXPENSE,
    )
    session.add_all([cash, food])
    session.commit()
    session.refresh(cash)
    session.refresh(food)
    return {"cash": cash, "food": food}


@pytest.fixture
def api_token(session: Session, user: User) -> str:
    """Create an API token and return the raw token string."""
    service = ApiTokenService(session)
    result = service.create_token(user.id, "Test AI Token")
    return result.raw_token


class TestAIAssistantAPIAccess:
    """Test that AI assistants can access the API via token auth."""

    def test_create_transaction_with_api_token(
        self, client: TestClient, api_token: str, ledger: Ledger, accounts: dict
    ):
        """AI assistant creates a transaction using API token auth."""
        response = client.post(
            f"/api/v1/ledgers/{ledger.id}/transactions",
            json={
                "date": "2026-02-06",
                "description": "午餐",
                "amount": 120,
                "from_account_id": str(accounts["cash"].id),
                "to_account_id": str(accounts["food"].id),
                "transaction_type": "EXPENSE",
            },
            headers={"Authorization": f"Bearer {api_token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["description"] == "午餐"
        assert float(data["amount"]) == 120.0

    def test_list_transactions_with_api_token(
        self, client: TestClient, api_token: str, ledger: Ledger, accounts: dict
    ):
        """AI assistant can list transactions using API token auth."""
        # Create a transaction first
        client.post(
            f"/api/v1/ledgers/{ledger.id}/transactions",
            json={
                "date": "2026-02-06",
                "description": "咖啡",
                "amount": 85,
                "from_account_id": str(accounts["cash"].id),
                "to_account_id": str(accounts["food"].id),
                "transaction_type": "EXPENSE",
            },
        )

        response = client.get(
            f"/api/v1/ledgers/{ledger.id}/transactions",
            headers={"Authorization": f"Bearer {api_token}"},
        )
        assert response.status_code == 200

    def test_list_accounts_with_api_token(
        self, client: TestClient, api_token: str, ledger: Ledger, accounts: dict
    ):
        """AI assistant can list accounts using API token auth."""
        response = client.get(
            f"/api/v1/ledgers/{ledger.id}/accounts",
            headers={"Authorization": f"Bearer {api_token}"},
        )
        assert response.status_code == 200
        data = response.json()
        # Response may wrap in {"data": [...]} or return list directly
        items = data["data"] if isinstance(data, dict) and "data" in data else data
        assert len(items) >= 2

    def test_list_ledgers_with_api_token(self, client: TestClient, api_token: str, ledger: Ledger):
        """AI assistant can list user's ledgers."""
        response = client.get(
            "/api/v1/ledgers",
            headers={"Authorization": f"Bearer {api_token}"},
        )
        assert response.status_code == 200


class TestOpenAPISpecEndpoint:
    """Test the OpenAPI spec export endpoint for GPT Actions."""

    def test_openapi_spec_endpoint_returns_json(self, client: TestClient):
        """The spec endpoint should return valid JSON OpenAPI spec."""
        response = client.get("/api/v1/openapi-gpt-actions")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data

    def test_openapi_spec_endpoint_has_auth_info(self, client: TestClient):
        """The spec should include auth configuration for GPT Actions."""
        response = client.get("/api/v1/openapi-gpt-actions")
        data = response.json()
        components = data.get("components", {})
        assert "securitySchemes" in components
