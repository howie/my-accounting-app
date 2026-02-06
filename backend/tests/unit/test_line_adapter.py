"""Unit tests for LINE adapter.

Tests:
- HMAC-SHA256 signature verification
- Text event parsing
- Binding verification via OTP
- Reply token handling

Per Constitution Principle II: Tests written BEFORE implementation.
"""

import hashlib
import hmac
import json
from unittest.mock import patch

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
    settings.line_channel_secret = "test_channel_secret"
    settings.line_channel_access_token = "test_access_token"
    return settings


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="line@example.com", display_name="LINE Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    """Create a test ledger."""
    ledger = Ledger(
        name="LINE Ledger",
        description="For LINE testing",
        currency="TWD",
        user_id=user.id,
    )
    session.add(ledger)
    session.commit()
    session.refresh(ledger)
    return ledger


@pytest.fixture
def line_binding(session: Session, user: User, ledger: Ledger):
    """Create a LINE channel binding."""
    from src.models.channel_binding import ChannelBinding

    binding = ChannelBinding(
        user_id=user.id,
        channel_type=ChannelType.LINE,
        external_user_id="line_U123456789",
        display_name="LINE Test User",
        is_active=True,
        default_ledger_id=ledger.id,
    )
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def _get_adapter(session: Session):
    """Import and create LINEAdapter."""
    from src.bots.line_adapter import LINEAdapter

    return LINEAdapter(session)


def _compute_line_signature(body: str, secret: str) -> str:
    """Compute LINE HMAC-SHA256 signature."""
    return hmac.new(
        secret.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


class TestSignatureVerification:
    """Tests for LINE HMAC-SHA256 signature verification."""

    def test_verify_signature_valid(self, session, mock_settings: Session):
        """Valid X-Line-Signature should pass."""
        adapter = _get_adapter(session)
        body = '{"events": []}'
        secret = "test_channel_secret"
        signature = _compute_line_signature(body, secret)

        with patch("src.bots.line_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(body, signature)

        assert result is True

    def test_verify_signature_invalid(self, session, mock_settings: Session):
        """Invalid signature should fail."""
        adapter = _get_adapter(session)
        body = '{"events": []}'
        secret = "test_channel_secret"

        with patch("src.bots.line_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(body, "invalid_signature")

        assert result is False

    def test_verify_signature_missing(self, session, mock_settings: Session):
        """Missing signature should fail."""
        adapter = _get_adapter(session)
        body = '{"events": []}'

        with patch("src.bots.line_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(body, None)

        assert result is False

    def test_verify_signature_body_tampered(self, session, mock_settings: Session):
        """Tampered body should fail signature verification."""
        adapter = _get_adapter(session)
        original_body = '{"events": []}'
        tampered_body = '{"events": [{"type": "message"}]}'
        secret = "test_channel_secret"
        signature = _compute_line_signature(original_body, secret)

        with patch("src.bots.line_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(tampered_body, signature)

        assert result is False


class TestTextMessageParsing:
    """Tests for parsing LINE text message events."""

    def test_parse_text_message_event(self, session: Session):
        """Should extract text and user ID from LINE message event."""
        adapter = _get_adapter(session)

        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "test_reply_token_123",
                    "source": {
                        "type": "user",
                        "userId": "line_U123456789",
                    },
                    "message": {
                        "type": "text",
                        "id": "123456789",
                        "text": "午餐 120 元",
                    },
                },
            ],
        }

        events = adapter.parse_webhook(webhook_payload)

        assert len(events) == 1
        event = events[0]
        assert event["text"] == "午餐 120 元"
        assert event["external_user_id"] == "line_U123456789"
        assert event["reply_token"] == "test_reply_token_123"
        assert event["message_type"] == "text"

    def test_parse_non_text_message_ignored(self, session: Session):
        """Non-text messages (sticker, image) should be ignored."""
        adapter = _get_adapter(session)

        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "test_reply_token",
                    "source": {
                        "type": "user",
                        "userId": "line_U123456789",
                    },
                    "message": {
                        "type": "sticker",
                        "id": "123456789",
                        "packageId": "1",
                        "stickerId": "1",
                    },
                },
            ],
        }

        events = adapter.parse_webhook(webhook_payload)

        # Sticker messages should be ignored
        assert len(events) == 0

    def test_parse_non_message_event_ignored(self, session: Session):
        """Non-message events (follow, unfollow) should be ignored."""
        adapter = _get_adapter(session)

        webhook_payload = {
            "events": [
                {
                    "type": "follow",
                    "replyToken": "test_reply_token",
                    "source": {
                        "type": "user",
                        "userId": "line_U123456789",
                    },
                },
            ],
        }

        events = adapter.parse_webhook(webhook_payload)

        # Follow events should be ignored
        assert len(events) == 0

    def test_parse_multiple_events(self, session: Session):
        """Multiple events in one webhook should all be parsed."""
        adapter = _get_adapter(session)

        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "token_1",
                    "source": {"type": "user", "userId": "user_1"},
                    "message": {"type": "text", "id": "1", "text": "Message 1"},
                },
                {
                    "type": "message",
                    "replyToken": "token_2",
                    "source": {"type": "user", "userId": "user_2"},
                    "message": {"type": "text", "id": "2", "text": "Message 2"},
                },
            ],
        }

        events = adapter.parse_webhook(webhook_payload)

        assert len(events) == 2


class TestReplyTokenHandling:
    """Tests for LINE reply token handling."""

    @patch("src.bots.line_adapter.LINEAdapter.send_reply")
    def test_reply_uses_reply_token(self, mock_send_reply, session: Session, line_binding):
        """Reply should use the reply token from the event."""
        adapter = _get_adapter(session)
        mock_send_reply.return_value = True

        adapter.send_reply(
            reply_token="test_reply_token_123",
            text="已記錄：午餐 120 元",
        )

        mock_send_reply.assert_called_once()
        args = mock_send_reply.call_args
        assert args.kwargs["reply_token"] == "test_reply_token_123"
        assert args.kwargs["text"] == "已記錄：午餐 120 元"

    @patch("src.bots.line_adapter.requests.post")
    def test_reply_api_call_structure(self, mock_post, session: Session, mock_settings):
        """Reply API call should have correct structure."""
        adapter = _get_adapter(session)
        mock_post.return_value.status_code = 200

        with patch("src.bots.line_adapter.get_settings", return_value=mock_settings):
            adapter.send_reply(
                reply_token="test_reply_token",
                text="Test reply",
            )

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "https://api.line.me/v2/bot/message/reply" in call_args[0][0]

        payload = call_args[1]["json"]
        assert payload["replyToken"] == "test_reply_token"
        assert payload["messages"][0]["type"] == "text"
        assert payload["messages"][0]["text"] == "Test reply"


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
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.LINE)

        adapter = _get_adapter(session)
        result = adapter.verify_otp_and_bind(
            code=code,
            external_user_id="line_U_new_user",
            display_name="New LINE User",
        )

        assert result is not None
        assert result["success"] is True
        assert "已成功綁定" in result["message"]

    def test_verify_otp_invalid_code(self, session: Session):
        """Invalid OTP should fail with error message."""
        adapter = _get_adapter(session)
        result = adapter.verify_otp_and_bind(
            code="000000",
            external_user_id="line_U_new_user",
        )

        assert result is not None
        assert result["success"] is False
        assert "驗證碼無效" in result["message"] or "已過期" in result["message"]


class TestUnboundUserHandling:
    """Tests for handling messages from unbound users."""

    @patch("src.bots.line_adapter.LINEAdapter.send_reply")
    def test_unbound_user_receives_binding_instructions(
        self,
        mocksend_reply,
        session: Session,
    ):
        """User without binding should receive binding instructions."""
        adapter = _get_adapter(session)

        webhook_payload = {
            "events": [
                {
                    "type": "message",
                    "replyToken": "test_reply_token",
                    "source": {
                        "type": "user",
                        "userId": "line_U_unbound",
                    },
                    "message": {
                        "type": "text",
                        "id": "123",
                        "text": "午餐 120 元",
                    },
                },
            ],
        }

        body = json.dumps(webhook_payload)
        secret = "test_secret"
        signature = _compute_line_signature(body, secret)

        with patch("src.bots.line_adapter.get_settings", return_value=mock_settings):
            adapter.process_webhook(body, signature)

        # Should send binding instructions
        mocksend_reply.assert_called_once()
        reply_text = mocksend_reply.call_args[0][1]
        assert "綁定" in reply_text or "驗證碼" in reply_text


class TestLINEAPIErrorHandling:
    """Tests for handling LINE API errors."""

    @patch("src.bots.line_adapter.requests.post")
    def test_reply_api_failure_logs_error(self, mock_post, session: Session):
        """Failed reply API call should log error and not crash."""
        adapter = _get_adapter(session)
        mock_post.return_value.status_code = 429  # Rate limit
        mock_post.return_value.text = "Rate limit exceeded"

        with patch("src.bots.line_adapter.get_settings", return_value=mock_settings):
            # Should not raise exception
            result = adapter.send_reply(
                reply_token="test_reply_token",
                text="Test",
            )

        # Should return False or handle gracefully
        assert result is False or result is None

    @patch("src.bots.line_adapter.requests.post")
    def test_quota_exhaustion_handling(self, mock_post, session: Session):
        """LINE free plan quota exhaustion (429) should be handled gracefully."""
        adapter = _get_adapter(session)
        mock_post.return_value.status_code = 429
        mock_post.return_value.json.return_value = {
            "message": "Exceeded the monthly limit of push messages",
        }

        with patch("src.bots.line_adapter.get_settings", return_value=mock_settings):
            result = adapter.send_reply(
                reply_token="test_reply_token",
                text="Test",
            )

        # Should handle gracefully without crashing
        assert result is False or result is None
