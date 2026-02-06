"""Contract tests for Channel Binding API.

Tests list bindings, generate code, and unbind endpoints
per contracts/channel-binding-api.yaml.
Per Constitution Principle II: Tests written BEFORE implementation.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.models.ledger import Ledger
from src.models.user import User


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


class TestListBindings:
    """GET /api/v1/channels/bindings"""

    def test_list_bindings_empty(self, client: TestClient):
        response = client.get("/api/v1/channels/bindings")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_bindings_returns_active_only_by_default(self, client: TestClient):
        # Generate code and bind
        gen_response = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "TELEGRAM"},
        )
        assert gen_response.status_code == 200
        code = gen_response.json()["code"]

        # Verify code (simulates bot-side verification)
        verify_response = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code, "external_user_id": "tg_123", "display_name": "TestBot"},
        )
        assert verify_response.status_code == 200

        response = client.get("/api/v1/channels/bindings")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["channel_type"] == "TELEGRAM"
        assert data[0]["is_active"] is True

    def test_list_bindings_includes_inactive_when_requested(self, client: TestClient):
        # Bind and unbind
        gen = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "TELEGRAM"},
        )
        code = gen.json()["code"]
        verify = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code, "external_user_id": "tg_123"},
        )
        binding_id = verify.json()["id"]
        client.delete(f"/api/v1/channels/bindings/{binding_id}")

        # Default: no inactive
        response = client.get("/api/v1/channels/bindings")
        assert len(response.json()) == 0

        # With include_inactive
        response = client.get("/api/v1/channels/bindings", params={"include_inactive": True})
        assert len(response.json()) == 1


class TestGenerateCode:
    """POST /api/v1/channels/bindings/generate-code"""

    def test_generate_code_success(self, client: TestClient):
        response = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "TELEGRAM"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert len(data["code"]) == 6
        assert data["code"].isdigit()
        assert data["expires_in_seconds"] == 300

    def test_generate_code_with_ledger_id(self, client: TestClient, ledger: Ledger):
        response = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "LINE", "default_ledger_id": str(ledger.id)},
        )
        assert response.status_code == 200

    def test_generate_code_invalid_channel_type(self, client: TestClient):
        response = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "INVALID"},
        )
        assert response.status_code == 422


class TestVerifyCode:
    """POST /api/v1/channels/bindings/verify-code"""

    def test_verify_code_success(self, client: TestClient):
        gen = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "TELEGRAM"},
        )
        code = gen.json()["code"]

        response = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code, "external_user_id": "tg_123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["channel_type"] == "TELEGRAM"
        assert data["external_user_id"] == "tg_123"
        assert data["is_active"] is True

    def test_verify_invalid_code(self, client: TestClient):
        response = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": "000000", "external_user_id": "tg_123"},
        )
        assert response.status_code == 400


class TestUnbind:
    """DELETE /api/v1/channels/bindings/{binding_id}"""

    def test_unbind_success(self, client: TestClient):
        # Bind first
        gen = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "TELEGRAM"},
        )
        code = gen.json()["code"]
        verify = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code, "external_user_id": "tg_123"},
        )
        binding_id = verify.json()["id"]

        response = client.delete(f"/api/v1/channels/bindings/{binding_id}")
        assert response.status_code == 200

    def test_unbind_nonexistent_returns_404(self, client: TestClient):
        response = client.delete(f"/api/v1/channels/bindings/{uuid.uuid4()}")
        assert response.status_code == 404
