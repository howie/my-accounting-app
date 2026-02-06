"""Unit tests for Slack adapter.

Tests:
- HMAC-SHA256 signature verification (with timestamp)
- Event parsing (message events)
- Slash command handling
- url_verification challenge response
- Binding verification via OTP

Per Constitution Principle II: Tests written BEFORE implementation.
"""

import hashlib
import hmac
import json
import time
from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from src.models.channel_binding import ChannelType
from src.models.ledger import Ledger
from src.models.user import User


@pytest.fixture
def mock_settings():
    """Create a mock Settings object for testing."""
    from unittest.mock import MagicMock

    from src.core.config import Settings

    settings = MagicMock(spec=Settings)
    settings.slack_signing_secret = "test_signing_secret"
    settings.slack_bot_token = "xoxb-test-token"
    return settings


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="slack@example.com", display_name="Slack Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    """Create a test ledger."""
    ledger = Ledger(
        name="Slack Ledger",
        description="For Slack testing",
        currency="TWD",
        user_id=user.id,
    )
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


@pytest.fixture
def slack_binding(session: Session, user: User, ledger: Ledger):
    """Create a Slack channel binding."""
    from src.models.channel_binding import ChannelBinding

    binding = ChannelBinding(
        user_id=user.id,
        channel_type=ChannelType.SLACK,
        external_user_id="U987654321",
        display_name="Slack Test User",
        is_active=True,
        default_ledger_id=ledger.id,
    )
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def _get_adapter(session: Session):
    """Import and create SlackAdapter."""
    from src.bots.slack_adapter import SlackAdapter

    return SlackAdapter(session)


def _compute_slack_signature(body: str, timestamp: str, secret: str) -> str:
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


class TestSignatureVerification:
    """Tests for Slack HMAC-SHA256 signature verification."""

    def test_verify_signature_valid(self, session, mock_settings: Session):
        """Valid X-Slack-Signature with timestamp should pass."""
        adapter = _get_adapter(session)
        body = '{"type": "event_callback"}'
        timestamp = str(int(time.time()))
        secret = "test_signing_secret"
        signature = _compute_slack_signature(body, timestamp, secret)

        with patch("src.bots.slack_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(body, signature, timestamp)

        assert result is True

    def test_verify_signature_invalid(self, session, mock_settings: Session):
        """Invalid signature should fail."""
        adapter = _get_adapter(session)
        body = '{"type": "event_callback"}'
        timestamp = str(int(time.time()))
        secret = "test_signing_secret"

        with patch("src.bots.slack_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(body, "v0=invalid_signature", timestamp)

        assert result is False

    def test_verify_signature_missing(self, session, mock_settings: Session):
        """Missing signature should fail."""
        adapter = _get_adapter(session)
        body = '{"type": "event_callback"}'
        timestamp = str(int(time.time()))

        with patch("src.bots.slack_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(body, None, timestamp)

        assert result is False

    def test_verify_signature_replay_attack_protection(self, session, mock_settings: Session):
        """Old timestamp (>5 min) should fail to prevent replay attacks."""
        adapter = _get_adapter(session)
        body = '{"type": "event_callback"}'
        old_timestamp = str(int(time.time()) - 400)  # 400 seconds ago (>5 min)
        secret = "test_signing_secret"
        signature = _compute_slack_signature(body, old_timestamp, secret)

        with patch("src.bots.slack_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(body, signature, old_timestamp)

        # Should reject old timestamp
        assert result is False

    def test_verify_signature_body_tampered(self, session, mock_settings: Session):
        """Tampered body should fail signature verification."""
        adapter = _get_adapter(session)
        original_body = '{"type": "event_callback"}'
        tampered_body = '{"type": "event_callback", "malicious": true}'
        timestamp = str(int(time.time()))
        secret = "test_signing_secret"
        signature = _compute_slack_signature(original_body, timestamp, secret)

        with patch("src.bots.slack_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(tampered_body, signature, timestamp)

        assert result is False


class TestEventParsing:
    """Tests for parsing Slack event callbacks."""

    def test_parse_message_event(self, session: Session):
        """Should extract text and user ID from Slack message event."""
        adapter = _get_adapter(session)

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

        event = adapter.parse_event(webhook_payload)

        assert event is not None
        assert event["text"] == "午餐 120 元"
        assert event["external_user_id"] == "U987654321"
        assert event["event_type"] == "message"

    def test_parse_message_with_subtype_ignored(self, session: Session):
        """Messages with subtypes (bot_message, etc.) should be ignored."""
        adapter = _get_adapter(session)

        webhook_payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "subtype": "bot_message",
                "channel": "C123456",
                "bot_id": "B123",
                "text": "Bot message",
                "ts": "1234567890.123456",
            },
        }

        event = adapter.parse_event(webhook_payload)

        # Bot messages should be ignored
        assert event is None

    def test_parse_non_message_event_ignored(self, session: Session):
        """Non-message events (app_mention, etc.) should be ignored."""
        adapter = _get_adapter(session)

        webhook_payload = {
            "type": "event_callback",
            "event": {
                "type": "app_mention",
                "user": "U123",
                "text": "<@U456> hello",
                "ts": "1234567890.123456",
            },
        }

        event = adapter.parse_event(webhook_payload)

        # Only handle direct messages, not app mentions
        assert event is None


class TestSlashCommandHandling:
    """Tests for Slack slash command handling."""

    def test_parse_slash_command(self, session: Session):
        """Should parse slash command payload."""
        adapter = _get_adapter(session)

        command_payload = {
            "command": "/expense",
            "text": "午餐 120 元",
            "user_id": "U987654321",
            "channel_id": "C123456",
            "response_url": "https://hooks.slack.com/commands/...",
        }

        result = adapter.parse_slash_command(command_payload)

        assert result is not None
        assert result["text"] == "午餐 120 元"
        assert result["external_user_id"] == "U987654321"
        assert result["command"] == "/expense"

    @patch("src.services.bot_message_handler.BotMessageHandler.handle_message")
    def test_slash_command_response(
        self,
        mock_handle_message,
        session: Session,
        slack_binding,
    ):
        """Slash command should return immediate response."""
        adapter = _get_adapter(session)

        mock_result = MagicMock()
        mock_result.reply_text = "已記錄：午餐 120 元"
        mock_result.success = True
        mock_handle_message.return_value = mock_result

        command_payload = {
            "command": "/expense",
            "text": "午餐 120 元",
            "user_id": slack_binding.external_user_id,
            "channel_id": "C123456",
            "response_url": "https://hooks.slack.com/commands/...",
        }

        response = adapter.handle_slash_command(command_payload)

        assert response is not None
        assert response["response_type"] == "ephemeral"  # Only visible to user
        assert "已記錄" in response["text"]


class TestURLVerificationChallenge:
    """Tests for Slack url_verification challenge."""

    def test_url_verification_challenge_response(self, session: Session):
        """url_verification challenge should echo back challenge string."""
        adapter = _get_adapter(session)

        challenge_payload = {
            "type": "url_verification",
            "challenge": "test_challenge_string_12345",
        }

        response = adapter.handle_url_verification(challenge_payload)

        assert response is not None
        assert response["challenge"] == "test_challenge_string_12345"

    def test_url_verification_is_onetime_event(self, session: Session):
        """url_verification should not create message logs."""
        adapter = _get_adapter(session)

        challenge_payload = {
            "type": "url_verification",
            "challenge": "test_challenge_12345",
        }

        # Should just return challenge, not process as message
        response = adapter.handle_url_verification(challenge_payload)
        assert response["challenge"] == "test_challenge_12345"

        # Verify no message log was created
        from sqlmodel import select

        from src.models.channel_message_log import ChannelMessageLog

        session = adapter.session
        logs = session.exec(select(ChannelMessageLog)).all()
        assert len(logs) == 0


class TestOTPBindingFlow:
    """Tests for OTP binding verification flow."""

    def test_detect_otp_code_in_message(self, session: Session):
        """6-digit code should be detected as OTP."""
        adapter = _get_adapter(session)

        assert adapter.is_otp_code("123456") is True
        assert adapter.is_otp_code("000000") is True
        assert adapter.is_otp_code("999999") is True

    def test_detect_non_otp_message(self, session: Session):
        """Non-OTP messages should not be detected as OTP."""
        adapter = _get_adapter(session)

        assert adapter.is_otp_code("午餐 120 元") is False
        assert adapter.is_otp_code("12345") is False
        assert adapter.is_otp_code("1234567") is False

    def test_verify_otp_success(self, session: Session, user: User):
        """Valid OTP should create binding."""
        from src.services.channel_binding_service import ChannelBindingService

        service = ChannelBindingService(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.SLACK)

        adapter = _get_adapter(session)
        result = adapter.verify_otp_and_bind(
            code=code,
            external_user_id="U_new_slack_user",
            display_name="New Slack User",
        )

        assert result is not None
        assert result["success"] is True
        assert "已成功綁定" in result["message"]

    def test_verify_otp_invalid_code(self, session: Session):
        """Invalid OTP should fail with error message."""
        adapter = _get_adapter(session)
        result = adapter.verify_otp_and_bind(
            code="000000",
            external_user_id="U_new_user",
        )

        assert result is not None
        assert result["success"] is False
        assert "驗證碼無效" in result["message"] or "已過期" in result["message"]


class TestUnboundUserHandling:
    """Tests for handling messages from unbound users."""

    @patch("src.bots.slack_adapter.SlackAdapter.send_message")
    def test_unbound_user_receives_binding_instructions(
        self,
        mock_send,
        session: Session,
        mock_settings,
    ):
        """User without binding should receive binding instructions."""
        webhook_payload = {
            "type": "event_callback",
            "event": {
                "type": "message",
                "channel": "C123456",
                "user": "U_unbound_user",
                "text": "午餐 120 元",
                "ts": "1234567890.123456",
            },
        }

        body = json.dumps(webhook_payload)
        timestamp = str(int(time.time()))
        signature = _compute_slack_signature(body, timestamp, mock_settings.slack_signing_secret)

        with patch("src.bots.slack_adapter.get_settings", return_value=mock_settings):
            adapter = _get_adapter(session)
            adapter.process_webhook(body, signature, timestamp)

        # Should send binding instructions
        mock_send.assert_called_once()
        # Check both positional and keyword arguments
        if mock_send.call_args.kwargs:
            message_text = mock_send.call_args.kwargs.get("text", "")
        else:
            # Fallback to positional args
            message_text = mock_send.call_args[0][1] if len(mock_send.call_args[0]) > 1 else ""
        assert "綁定" in message_text or "驗證碼" in message_text


class TestSlackAPIErrorHandling:
    """Tests for handling Slack API errors."""

    @patch("src.bots.slack_adapter.requests.post")
    def test_message_send_failure_logs_error(self, mock_post, session: Session):
        """Failed message send should log error and not crash."""
        adapter = _get_adapter(session)
        mock_post.return_value.status_code = 429
        mock_post.return_value.text = "rate_limited"

        with patch("src.bots.slack_adapter.get_settings", return_value=mock_settings):
            # Should not raise exception
            result = adapter.send_message(
                channel="C123456",
                text="Test message",
            )

        # Should return False or handle gracefully
        assert result is False or result is None
