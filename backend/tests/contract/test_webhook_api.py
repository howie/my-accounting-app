"""Contract tests for webhook endpoints.

Tests Telegram/LINE/Slack webhook endpoints per contracts/webhook-api.yaml:
- Valid signature → 200
- Invalid signature → 401
- Rate limited → 429

Per Constitution Principle II: Tests written BEFORE implementation.
"""

import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from src.core.config import Settings
from src.models.channel_binding import ChannelType
from src.models.ledger import Ledger
from src.models.user import User


@pytest.fixture
def mock_settings():
    """Create a mock Settings object for testing."""
    settings = MagicMock(spec=Settings)
    settings.telegram_webhook_secret = "test_telegram_secret"
    settings.line_channel_secret = "test_line_secret"
    settings.slack_signing_secret = "test_slack_secret"
    return settings


@pytest.fixture(autouse=True, scope="function")
def reset_rate_limiter_per_test():
    """Reset rate limiter before each test to avoid cross-test pollution."""
    from src.api.rate_limit import limiter

    # Reset shared limiter storage (used by both app.state and webhook routes)
    if hasattr(limiter, "_storage"):
        limiter._storage.reset()

    yield

    if hasattr(limiter, "_storage"):
        limiter._storage.reset()


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="webhook@example.com", display_name="Webhook Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    """Create a test ledger."""
    ledger = Ledger(
        name="Webhook Ledger",
        description="For webhook testing",
        currency="TWD",
        user_id=user.id,
    )
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


@pytest.fixture
def telegram_binding(session: Session, user: User, ledger: Ledger):
    """Create a Telegram channel binding."""
    from src.models.channel_binding import ChannelBinding

    binding = ChannelBinding(
        user_id=user.id,
        channel_type=ChannelType.TELEGRAM,
        external_user_id="123456",
        display_name="Test Telegram User",
        is_active=True,
        default_ledger_id=ledger.id,
    )
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


@pytest.fixture
def line_binding(session: Session, user: User, ledger: Ledger):
    """Create a LINE channel binding."""
    from src.models.channel_binding import ChannelBinding

    binding = ChannelBinding(
        user_id=user.id,
        channel_type=ChannelType.LINE,
        external_user_id="line_U123456789",
        display_name="Test LINE User",
        is_active=True,
        default_ledger_id=ledger.id,
    )
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


@pytest.fixture
def slack_binding(session: Session, user: User, ledger: Ledger):
    """Create a Slack channel binding."""
    from src.models.channel_binding import ChannelBinding

    binding = ChannelBinding(
        user_id=user.id,
        channel_type=ChannelType.SLACK,
        external_user_id="U987654321",
        display_name="Test Slack User",
        is_active=True,
        default_ledger_id=ledger.id,
    )
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


class TestTelegramWebhook:
    """POST /webhooks/telegram"""

    def test_valid_telegram_webhook_returns_200(
        self, client: TestClient, telegram_binding, mock_settings
    ):
        """Valid webhook with correct secret token should succeed."""
        webhook_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123456,
                    "first_name": "Test",
                },
                "chat": {"id": 123456, "type": "private"},
                "date": 1234567890,
                "text": "午餐 120 元",
            },
        }

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            response = client.post(
                "/webhooks/telegram",
                json=webhook_payload,
                headers={"X-Telegram-Bot-Api-Secret-Token": "test_telegram_secret"},
            )

        assert response.status_code == 200

    def test_invalid_telegram_signature_returns_401(self, client: TestClient, mock_settings):
        """Invalid signature should return 401 Unauthorized."""
        webhook_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123, "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "date": 1234567890,
                "text": "午餐 120 元",
            },
        }

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            response = client.post(
                "/webhooks/telegram",
                json=webhook_payload,
                headers={"X-Telegram-Bot-Api-Secret-Token": "wrong_secret"},
            )

        assert response.status_code == 401

    def test_missing_telegram_signature_returns_401(self, client: TestClient):
        """Missing signature header should return 401."""
        webhook_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123, "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "date": 1234567890,
                "text": "午餐 120 元",
            },
        }

        response = client.post("/webhooks/telegram", json=webhook_payload)

        assert response.status_code == 401


class TestLINEWebhook:
    """POST /webhooks/line"""

    def _compute_line_signature(self, body: str, secret: str) -> str:
        """Compute LINE HMAC-SHA256 signature."""
        return hmac.new(
            secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def test_valid_line_webhook_returns_200(self, client: TestClient, line_binding, mock_settings):
        """Valid LINE webhook with correct signature should succeed."""
        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "id": "123456789",
                        "text": "午餐 120 元",
                    },
                    "source": {
                        "type": "user",
                        "userId": "line_U123456789",
                    },
                    "replyToken": "test_reply_token",
                },
            ],
        }

        body = json.dumps(webhook_payload)
        signature = self._compute_line_signature(body, "test_line_secret")

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            response = client.post(
                "/webhooks/line",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Line-Signature": signature,
                },
            )

        assert response.status_code == 200

    def test_invalid_line_signature_returns_401(self, client: TestClient, mock_settings):
        """Invalid LINE signature should return 401."""
        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "id": "123456789",
                        "text": "午餐 120 元",
                    },
                    "source": {
                        "type": "user",
                        "userId": "line_U123456789",
                    },
                    "replyToken": "test_reply_token",
                },
            ],
        }

        body = json.dumps(webhook_payload)

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            response = client.post(
                "/webhooks/line",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Line-Signature": "invalid_signature",
                },
            )

        assert response.status_code == 401

    def test_missing_line_signature_returns_401(self, client: TestClient):
        """Missing LINE signature header should return 401."""
        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "message": {
                        "type": "text",
                        "id": "123456789",
                        "text": "午餐 120 元",
                    },
                    "source": {
                        "type": "user",
                        "userId": "line_U123456789",
                    },
                    "replyToken": "test_reply_token",
                },
            ],
        }

        response = client.post(
            "/webhooks/line",
            json=webhook_payload,
        )

        assert response.status_code == 401


class TestSlackWebhook:
    """POST /webhooks/slack"""

    def _compute_slack_signature(self, body: str, timestamp: str, secret: str) -> str:
        """Compute Slack HMAC-SHA256 signature."""
        base_string = f"v0:{timestamp}:{body}"
        return (
            "v0="
            + hmac.new(
                secret.encode("utf-8"),
                base_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        )

    def test_valid_slack_webhook_returns_200(
        self, client: TestClient, slack_binding, mock_settings
    ):
        """Valid Slack webhook with correct signature should succeed."""
        webhook_payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C123456",
                "user": "U987654321",
                "text": "午餐 120 元",
                "ts": "1234567890.123456",
            },
        }

        body = json.dumps(webhook_payload)
        timestamp = str(int(time.time()))
        signature = self._compute_slack_signature(body, timestamp, "test_slack_secret")

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            response = client.post(
                "/webhooks/slack",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Signature": signature,
                    "X-Slack-Request-Timestamp": timestamp,
                },
            )

        assert response.status_code == 200

    def test_invalid_slack_signature_returns_401(self, client: TestClient, mock_settings):
        """Invalid Slack signature should return 401."""
        webhook_payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C123456",
                "user": "U987654321",
                "text": "午餐 120 元",
                "ts": "1234567890.123456",
            },
        }

        body = json.dumps(webhook_payload)
        timestamp = str(int(time.time()))

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            response = client.post(
                "/webhooks/slack",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Signature": "v0=invalid_signature",
                    "X-Slack-Request-Timestamp": timestamp,
                },
            )

        assert response.status_code == 401

    def test_missing_slack_signature_returns_401(self, client: TestClient):
        """Missing Slack signature should return 401."""
        webhook_payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C123456",
                "user": "U987654321",
                "text": "午餐 120 元",
                "ts": "1234567890.123456",
            },
        }

        response = client.post(
            "/webhooks/slack",
            json=webhook_payload,
            headers={"X-Slack-Request-Timestamp": str(int(time.time()))},
        )

        assert response.status_code == 401

    def test_slack_timestamp_replay_attack_rejected(self, client: TestClient, mock_settings):
        """Old timestamp (>5 min) should be rejected to prevent replay attacks."""
        webhook_payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C123456",
                "user": "U987654321",
                "text": "午餐 120 元",
                "ts": "1234567890.123456",
            },
        }

        body = json.dumps(webhook_payload)
        # Timestamp from 10 minutes ago
        old_timestamp = str(int(time.time()) - 600)
        signature = self._compute_slack_signature(body, old_timestamp, "test_slack_secret")

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            response = client.post(
                "/webhooks/slack",
                content=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Slack-Signature": signature,
                    "X-Slack-Request-Timestamp": old_timestamp,
                },
            )

        # Should reject due to old timestamp
        assert response.status_code == 401

    def test_slack_url_verification_challenge(self, client: TestClient, mock_settings):
        """Slack url_verification challenge should be echoed back."""
        challenge_payload = {
            "type": "url_verification",
            "challenge": "test_challenge_string_12345",
        }

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            response = client.post(
                "/webhooks/slack",
                json=challenge_payload,
            )

        # Should echo back the challenge
        assert response.status_code == 200
        assert response.json()["challenge"] == "test_challenge_string_12345"


class TestWebhookRateLimit:
    """Rate limiting tests for webhook endpoints (FR-012)."""

    def test_telegram_webhook_rate_limit(self, client: TestClient, telegram_binding, mock_settings):
        """Telegram webhook should enforce rate limit (30 req/min per user)."""
        webhook_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123456, "first_name": "Test"},
                "chat": {"id": 123456, "type": "private"},
                "date": 1234567890,
                "text": "Test",
            },
        }

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            # Send 31 requests rapidly
            for i in range(31):
                response = client.post(
                    "/webhooks/telegram",
                    json={**webhook_payload, "update_id": 123456789 + i},
                    headers={"X-Telegram-Bot-Api-Secret-Token": "test_telegram_secret"},
                )
                if i < 30:
                    assert response.status_code in [200, 201]
                else:
                    # 31st request should be rate limited
                    assert response.status_code == 429

    def test_line_webhook_rate_limit(self, client: TestClient, line_binding, mock_settings):
        """LINE webhook should enforce rate limit (30 req/min per user)."""

        def _compute_line_signature(body: str, secret: str) -> str:
            return hmac.new(
                secret.encode("utf-8"),
                body.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            # Send 31 requests rapidly
            for i in range(31):
                webhook_payload = {
                    "events": [
                        {
                            "type": "message",
                            "message": {
                                "type": "text",
                                "id": str(123456789 + i),
                                "text": f"Test {i}",
                            },
                            "source": {
                                "type": "user",
                                "userId": "line_U123456789",
                            },
                            "replyToken": f"token_{i}",
                        },
                    ],
                }
                body = json.dumps(webhook_payload)
                signature = _compute_line_signature(body, "test_line_secret")

                response = client.post(
                    "/webhooks/line",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Line-Signature": signature,
                    },
                )

                if i < 30:
                    assert response.status_code in [200, 201]
                else:
                    # 31st request should be rate limited
                    assert response.status_code == 429

    def test_slack_webhook_rate_limit(self, client: TestClient, slack_binding, mock_settings):
        """Slack webhook should enforce rate limit (30 req/min per user)."""

        def _compute_slack_signature(body: str, timestamp: str, secret: str) -> str:
            base_string = f"v0:{timestamp}:{body}"
            return (
                "v0="
                + hmac.new(
                    secret.encode("utf-8"),
                    base_string.encode("utf-8"),
                    hashlib.sha256,
                ).hexdigest()
            )

        with (
            patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.line_adapter.get_settings", return_value=mock_settings),
            patch("src.bots.slack_adapter.get_settings", return_value=mock_settings),
        ):
            # Send 31 requests rapidly
            for i in range(31):
                webhook_payload = {
                    "type": "event_callback",
                    "event": {
                        "type": "message",
                        "channel": "C123456",
                        "user": "U987654321",
                        "text": f"Test {i}",
                        "ts": f"1234567890.{i}",
                    },
                }
                body = json.dumps(webhook_payload)
                timestamp = str(int(time.time()))
                signature = _compute_slack_signature(body, timestamp, "test_slack_secret")

                response = client.post(
                    "/webhooks/slack",
                    content=body,
                    headers={
                        "Content-Type": "application/json",
                        "X-Slack-Signature": signature,
                        "X-Slack-Request-Timestamp": timestamp,
                    },
                )

                if i < 30:
                    assert response.status_code in [200, 201]
                else:
                    # 31st request should be rate limited
                    assert response.status_code == 429
