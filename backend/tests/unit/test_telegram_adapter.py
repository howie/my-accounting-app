"""Unit tests for Telegram adapter.

Tests:
- Signature verification
- Text message parsing
- Voice message handling
- Binding verification via OTP
- Ambiguous input triggering clarification prompt (FR-009)

Per Constitution Principle II: Tests written BEFORE implementation.
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlmodel import Session

from src.core.config import Settings
from src.models.channel_binding import ChannelType
from src.models.ledger import Ledger
from src.models.user import User


@pytest.fixture
def mock_settings():
    """Create a mock Settings object for testing."""
    settings = MagicMock(spec=Settings)
    settings.telegram_webhook_secret = "test_secret_token"
    settings.telegram_bot_token = "test_bot_token"
    return settings


@pytest.fixture
def user(session: Session) -> User:
    """Create a test user."""
    user = User(email="telegram@example.com", display_name="Telegram Test User")
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def ledger(session: Session, user: User) -> Ledger:
    """Create a test ledger."""
    ledger = Ledger(
        name="Telegram Ledger",
        description="For telegram testing",
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
        display_name="Test Bot User",
        is_active=True,
        default_ledger_id=ledger.id,
    )
    session.add(binding)
    session.commit()
    session.refresh(binding)
    return binding


def _get_adapter(session: Session):
    """Import and create TelegramAdapter."""
    from src.bots.telegram_adapter import TelegramAdapter

    return TelegramAdapter(session)


class TestSignatureVerification:
    """Tests for Telegram webhook signature verification."""

    def test_verify_signature_valid(self, session: Session, mock_settings):
        """Valid X-Telegram-Bot-Api-Secret-Token should pass."""
        adapter = _get_adapter(session)
        secret = "test_secret_token"

        with patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(secret)

        assert result is True

    def test_verify_signature_invalid(self, session: Session, mock_settings):
        """Invalid secret token should fail."""
        adapter = _get_adapter(session)

        with patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature("wrong_secret")

        assert result is False

    def test_verify_signature_missing(self, session: Session, mock_settings):
        """Missing secret token should fail."""
        adapter = _get_adapter(session)

        with patch("src.bots.telegram_adapter.get_settings", return_value=mock_settings):
            result = adapter.verify_signature(None)

        assert result is False


class TestTextMessageParsing:
    """Tests for parsing Telegram text messages."""

    def test_parse_text_message_success(self, session: Session):
        """Should extract text and user ID from Telegram Update."""
        adapter = _get_adapter(session)

        update_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {
                    "id": 123,
                    "first_name": "Test",
                    "username": "testuser",
                },
                "chat": {"id": 123, "type": "private"},
                "date": 1234567890,
                "text": "午餐 120 元",
            },
        }

        result = adapter.parse_update(update_payload)

        assert result is not None
        assert result["text"] == "午餐 120 元"
        assert result["external_user_id"] == "123"
        assert result["message_type"] == "text"

    def test_parse_message_with_no_text_returns_none(self, session: Session):
        """Update without text message should return None."""
        adapter = _get_adapter(session)

        update_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123, "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "date": 1234567890,
                # No text field
            },
        }

        result = adapter.parse_update(update_payload)

        assert result is None

    def test_parse_edited_message_ignored(self, session: Session):
        """Edited messages should be ignored."""
        adapter = _get_adapter(session)

        update_payload = {
            "update_id": 123456789,
            "edited_message": {
                "message_id": 1,
                "from": {"id": 123, "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "date": 1234567890,
                "text": "Edited text",
            },
        }

        result = adapter.parse_update(update_payload)

        # Edited messages should be ignored
        assert result is None


class TestVoiceMessageHandling:
    """Tests for Telegram voice message handling."""

    def test_parse_voice_message_returns_voice_type(self, session: Session):
        """Voice message should be detected."""
        adapter = _get_adapter(session)

        update_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 123, "first_name": "Test"},
                "chat": {"id": 123, "type": "private"},
                "date": 1234567890,
                "voice": {
                    "file_id": "voice_file_id_123",
                    "duration": 5,
                },
            },
        }

        result = adapter.parse_update(update_payload)

        assert result is not None
        assert result["message_type"] == "voice"
        assert result["file_id"] == "voice_file_id_123"

    @patch("src.bots.telegram_adapter.TelegramAdapter._download_voice_file")
    @patch("src.bots.telegram_adapter.TelegramAdapter._transcribe_voice")
    def test_handle_voice_message_transcription(
        self,
        mock_transcribe,
        mock_download,
        session: Session,
    ):
        """Voice message should be downloaded and transcribed."""
        adapter = _get_adapter(session)
        mock_download.return_value = b"fake_audio_data"
        mock_transcribe.return_value = "午餐花了一百二十元"

        transcribed_text = adapter.transcribe_voice_message("voice_file_id_123")

        assert transcribed_text == "午餐花了一百二十元"
        mock_download.assert_called_once_with("voice_file_id_123")
        mock_transcribe.assert_called_once()

    @patch("src.bots.telegram_adapter.TelegramAdapter._download_voice_file")
    def test_voice_download_failure_returns_error_message(
        self,
        mock_download,
        session: Session,
    ):
        """Failed voice download should return error message."""
        adapter = _get_adapter(session)
        mock_download.side_effect = Exception("Download failed")

        result = adapter.transcribe_voice_message("voice_file_id_123")

        assert result is None


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
        assert adapter.is_otp_code("12345") is False  # Only 5 digits
        assert adapter.is_otp_code("1234567") is False  # 7 digits
        assert adapter.is_otp_code("abc123") is False

    def test_verify_otp_success(self, session: Session, user: User):
        """Valid OTP should create binding."""
        from src.services.channel_binding_service import ChannelBindingService

        service = ChannelBindingService(session)
        code = service.generate_code(user_id=user.id, channel_type=ChannelType.TELEGRAM)

        adapter = _get_adapter(session)
        result = adapter.verify_otp_and_bind(
            code=code,
            external_user_id="telegram_new_user",
            display_name="New User",
        )

        assert result is not None
        assert result["success"] is True
        assert "已成功綁定" in result["message"]

    def test_verify_otp_invalid_code(self, session: Session):
        """Invalid OTP should fail with error message."""
        adapter = _get_adapter(session)
        result = adapter.verify_otp_and_bind(
            code="000000",
            external_user_id="telegram_new_user",
        )

        assert result is not None
        assert result["success"] is False
        assert "驗證碼無效" in result["message"] or "已過期" in result["message"]


class TestAmbiguousInputHandling:
    """Tests for FR-009: ambiguous input triggering clarification prompt."""

    @patch("src.services.bot_message_handler.BotMessageHandler.handle_message")
    def test_ambiguous_input_triggers_clarification(
        self,
        mock_handle_message,
        session: Session,
        telegram_binding,
    ):
        """Ambiguous transaction input should trigger clarification."""
        adapter = _get_adapter(session)

        # Mock BotMessageHandler to return ambiguous result
        mock_result = MagicMock()
        mock_result.reply_text = "請問這筆支出是屬於哪個分類?\n1. 餐飲\n2. 交通\n3. 購物"
        mock_result.success = True
        mock_handle_message.return_value = mock_result

        update_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": int(telegram_binding.external_user_id)},
                "chat": {"id": int(telegram_binding.external_user_id), "type": "private"},
                "date": 1234567890,
                "text": "買東西 500",  # Ambiguous: what category?
            },
        }

        response = adapter.process_webhook(update_payload)

        assert response is not None
        # Should ask for clarification
        assert "分類" in response["reply_text"] or "確認" in response["reply_text"]

    @patch("src.services.bot_message_handler.BotMessageHandler.handle_message")
    def test_clear_input_no_clarification(
        self,
        mock_handle_message,
        session: Session,
        telegram_binding,
    ):
        """Clear transaction input should not trigger clarification."""
        adapter = _get_adapter(session)

        mock_result = MagicMock()
        mock_result.reply_text = "已記錄:午餐 120 元(餐飲)"
        mock_result.success = True
        mock_handle_message.return_value = mock_result

        update_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": int(telegram_binding.external_user_id)},
                "chat": {"id": int(telegram_binding.external_user_id), "type": "private"},
                "date": 1234567890,
                "text": "午餐 120 元",  # Clear category
            },
        }

        response = adapter.process_webhook(update_payload)

        assert response is not None
        assert "已記錄" in response["reply_text"]


class TestUnboundUserHandling:
    """Tests for handling messages from unbound users."""

    def test_unbound_user_receives_binding_instructions(self, session: Session):
        """User without binding should receive binding instructions."""
        adapter = _get_adapter(session)

        update_payload = {
            "update_id": 123456789,
            "message": {
                "message_id": 1,
                "from": {"id": 999999, "first_name": "Unbound"},
                "chat": {"id": 999999, "type": "private"},
                "date": 1234567890,
                "text": "午餐 120 元",
            },
        }

        response = adapter.process_webhook(update_payload)

        assert response is not None
        # Should instruct user to bind account
        assert "綁定" in response["reply_text"] or "驗證碼" in response["reply_text"]
