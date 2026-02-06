"""Telegram Bot adapter for webhook handling.

Handles webhook signature verification, Update parsing, voice transcription, OTP binding, and
message delegation to BotMessageHandler.
"""

import logging
import re

import requests
from sqlmodel import Session, select

from src.core.config import get_settings
from src.models.channel_binding import ChannelBinding, ChannelType
from src.models.channel_message_log import MessageType
from src.services.bot_message_handler import BotMessageHandler
from src.services.channel_binding_service import ChannelBindingService

logger = logging.getLogger(__name__)


class TelegramAdapter:
    """Adapter for Telegram Bot API webhooks."""

    def __init__(self, session: Session):
        self.session = session

    def verify_signature(self, secret_token: str | None) -> bool:
        """Verify X-Telegram-Bot-Api-Secret-Token header."""
        if not secret_token:
            return False

        settings = get_settings()
        expected_secret = settings.telegram_webhook_secret
        if not expected_secret:
            logger.warning("TELEGRAM_WEBHOOK_SECRET not configured")
            return False

        return secret_token == expected_secret

    def parse_update(self, update: dict) -> dict | None:
        """Parse Telegram Update object."""
        message = update.get("message")
        if not message:
            return None

        from_user = message.get("from", {})
        external_user_id = str(from_user.get("id"))
        if not external_user_id:
            return None

        # Check for text message
        text = message.get("text")
        if text:
            return {
                "text": text,
                "external_user_id": external_user_id,
                "message_type": "text",
                "display_name": from_user.get("first_name"),
            }

        # Check for voice message
        voice = message.get("voice")
        if voice:
            return {
                "text": None,
                "external_user_id": external_user_id,
                "message_type": "voice",
                "file_id": voice.get("file_id"),
                "display_name": from_user.get("first_name"),
            }

        return None

    def is_otp_code(self, text: str) -> bool:
        """Check if message text is a 6-digit OTP code."""
        return bool(re.fullmatch(r"\d{6}", text.strip()))

    def verify_otp_and_bind(
        self,
        code: str,
        external_user_id: str,
        display_name: str | None = None,
    ) -> dict:
        """Verify OTP code and create channel binding."""
        service = ChannelBindingService(self.session)
        binding = service.verify_code(
            code=code,
            external_user_id=external_user_id,
            display_name=display_name,
        )

        if binding:
            return {
                "success": True,
                "message": "已成功綁定！您現在可以使用 Telegram Bot 進行記帳。",
            }
        else:
            return {
                "success": False,
                "message": "驗證碼無效或已過期，請重新產生驗證碼。",
            }

    def transcribe_voice_message(self, file_id: str) -> str | None:
        """Download and transcribe voice message."""
        try:
            audio_data = self._download_voice_file(file_id)
            if not audio_data:
                return None

            transcribed_text = self._transcribe_voice(audio_data)
            return transcribed_text

        except Exception as e:
            logger.error(f"Voice transcription failed: {e}", exc_info=True)
            return None

    def _download_voice_file(self, file_id: str) -> bytes | None:
        """Download voice file from Telegram."""
        try:
            settings = get_settings()
            bot_token = settings.telegram_bot_token
            if not bot_token:
                logger.error("TELEGRAM_BOT_TOKEN not configured")
                return None

            get_file_url = f"https://api.telegram.org/bot{bot_token}/getFile"
            response = requests.get(get_file_url, params={"file_id": file_id}, timeout=10)
            response.raise_for_status()
            file_path = response.json()["result"]["file_path"]

            download_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()

            return response.content

        except Exception as e:
            logger.error(f"Voice file download failed: {e}", exc_info=True)
            return None

    def _transcribe_voice(self, audio_data: bytes) -> str | None:
        """Transcribe voice audio using LLM provider."""
        try:
            logger.info("Voice transcription requested (placeholder)")
            # TODO: Implement actual transcription (Gemini audio input, etc.)
            return None

        except Exception as e:
            logger.error(f"Voice transcription failed: {e}", exc_info=True)
            return None

    def process_webhook(self, update: dict) -> dict | None:
        """Process incoming Telegram webhook."""
        parsed = self.parse_update(update)
        if not parsed:
            return None

        external_user_id = parsed["external_user_id"]
        display_name = parsed.get("display_name")

        # Handle voice message
        if parsed["message_type"] == "voice":
            file_id = parsed.get("file_id")
            if not file_id:
                return {"reply_text": "無法處理語音訊息"}

            transcribed_text = self.transcribe_voice_message(file_id)
            if not transcribed_text:
                return {"reply_text": "語音辨識失敗，請使用文字訊息"}

            parsed["text"] = transcribed_text

        text = parsed["text"]
        if not text:
            return None

        # Check if this is an OTP code for binding
        if self.is_otp_code(text):
            result = self.verify_otp_and_bind(text, external_user_id, display_name)
            return {"reply_text": result["message"]}

        # Lookup channel binding
        binding = self.session.exec(
            select(ChannelBinding)
            .where(ChannelBinding.channel_type == ChannelType.TELEGRAM)
            .where(ChannelBinding.external_user_id == external_user_id)
            .where(ChannelBinding.is_active == True)  # noqa: E712
        ).first()

        if not binding:
            return {
                "reply_text": (
                    "您尚未綁定帳號。請先在網頁版設定頁面產生驗證碼，"
                    "然後在此輸入 6 位數驗證碼完成綁定。"
                )
            }

        # Delegate to BotMessageHandler
        handler = BotMessageHandler(self.session)
        message_type = MessageType.VOICE if parsed["message_type"] == "voice" else MessageType.TEXT

        result = handler.handle_message(
            binding=binding,
            text=text,
            message_type=message_type,
        )

        return {"reply_text": result.reply_text}
