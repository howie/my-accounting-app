"""Integration tests for the full channel binding flow.

Tests the complete lifecycle: generate code → verify → binding created →
query binding → unbind → binding inactive.
Per Constitution Principle II: Tests written BEFORE implementation.
"""

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


class TestFullBindingFlow:
    """Test the complete binding lifecycle."""

    def test_telegram_binding_full_flow(self, client: TestClient, ledger: Ledger):
        """Generate code → verify → list → unbind → list empty."""
        # Step 1: Generate code
        gen_response = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={
                "channel_type": "TELEGRAM",
                "default_ledger_id": str(ledger.id),
            },
        )
        assert gen_response.status_code == 200
        code = gen_response.json()["code"]
        assert len(code) == 6

        # Step 2: Verify code (simulates Telegram bot sending the code)
        verify_response = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={
                "code": code,
                "external_user_id": "telegram_user_42",
                "display_name": "Test Bot User",
            },
        )
        assert verify_response.status_code == 200
        binding_data = verify_response.json()
        binding_id = binding_data["id"]
        assert binding_data["channel_type"] == "TELEGRAM"
        assert binding_data["external_user_id"] == "telegram_user_42"
        assert binding_data["is_active"] is True

        # Step 3: List bindings — should show 1 active
        list_response = client.get("/api/v1/channels/bindings")
        assert list_response.status_code == 200
        bindings = list_response.json()
        assert len(bindings) == 1
        assert bindings[0]["id"] == binding_id

        # Step 4: Unbind
        unbind_response = client.delete(f"/api/v1/channels/bindings/{binding_id}")
        assert unbind_response.status_code == 200

        # Step 5: List bindings — should be empty (active only)
        list_response = client.get("/api/v1/channels/bindings")
        assert list_response.status_code == 200
        assert list_response.json() == []

        # Step 6: Verify unbound binding still visible with include_inactive
        list_response = client.get("/api/v1/channels/bindings", params={"include_inactive": True})
        assert list_response.status_code == 200
        bindings = list_response.json()
        assert len(bindings) == 1
        assert bindings[0]["is_active"] is False

    def test_line_binding_flow(self, client: TestClient):
        """Test LINE channel binding flow."""
        gen = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "LINE"},
        )
        assert gen.status_code == 200
        code = gen.json()["code"]

        verify = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code, "external_user_id": "line_U123456"},
        )
        assert verify.status_code == 200
        assert verify.json()["channel_type"] == "LINE"

    def test_multiple_channels_same_user(self, client: TestClient):
        """User can bind multiple different channel types."""
        # Bind Telegram
        gen1 = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "TELEGRAM"},
        )
        code1 = gen1.json()["code"]
        client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code1, "external_user_id": "tg_123"},
        )

        # Bind LINE
        gen2 = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "LINE"},
        )
        code2 = gen2.json()["code"]
        client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code2, "external_user_id": "line_456"},
        )

        # Should have 2 bindings
        list_response = client.get("/api/v1/channels/bindings")
        assert len(list_response.json()) == 2

    def test_code_cannot_be_reused(self, client: TestClient):
        """A verification code can only be used once."""
        gen = client.post(
            "/api/v1/channels/bindings/generate-code",
            json={"channel_type": "TELEGRAM"},
        )
        code = gen.json()["code"]

        # First use: success
        verify1 = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code, "external_user_id": "tg_123"},
        )
        assert verify1.status_code == 200

        # Second use: fail
        verify2 = client.post(
            "/api/v1/channels/bindings/verify-code",
            json={"code": code, "external_user_id": "tg_456"},
        )
        assert verify2.status_code == 400
