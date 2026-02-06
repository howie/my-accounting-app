"""LINE Bot adapter for webhook handling."""

import hashlib
import hmac
import json
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


class LINEAdapter:
    """Adapter for LINE Messaging API webhooks."""

    def __init__(self, session: Session):
        self.session = session

    def verify_signature(self, body: str, signature: str | None) -> bool:
        """Verify X-Line-Signature HMAC-SHA256 header."""
        if not signature:
            return False

        channel_secret = get_settings().line_channel_secret
        if not channel_secret:
            logger.warning("LINE_CHANNEL_SECRET not configured")
            return False

        expected_signature = hmac.new(
            channel_secret.encode("utf-8"),
            body.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def parse_webhook(self, webhook_payload: dict) -> list[dict]:
        """Parse LINE webhook events."""
        events = webhook_payload.get("events", [])
        parsed_events = []

        for event in events:
            if event.get("type") != "message":
                continue

            message = event.get("message", {})
            if message.get("type") != "text":
                continue

            source = event.get("source", {})
            external_user_id = source.get("userId")
            if not external_user_id:
                continue

            text = message.get("text")
            reply_token = event.get("replyToken")

            if text and reply_token:
                parsed_events.append(
                    {
                        "text": text,
                        "external_user_id": external_user_id,
                        "reply_token": reply_token,
                        "message_type": "text",
                    }
                )

        return parsed_events

    def is_otp_code(self, text: str) -> bool:
        """Check if message text is a 6-digit OTP code."""
        return bool(re.fullmatch(r"\d{6}", text.strip()))

    def verify_otp_and_bind(
        self, code: str, external_user_id: str, display_name: str | None = None
    ) -> dict:
        """Verify OTP code and create channel binding."""
        service = ChannelBindingService(self.session)
        binding = service.verify_code(
            code=code, external_user_id=external_user_id, display_name=display_name
        )

        if binding:
            return {"success": True, "message": "已成功綁定！您現在可以使用 LINE Bot 進行記帳。"}
        else:
            return {"success": False, "message": "驗證碼無效或已過期，請重新產生驗證碼。"}

    def send_reply(self, reply_token: str, text: str) -> bool:
        """Send reply message via LINE Reply API."""
        try:
            access_token = get_settings().line_channel_access_token
            if not access_token:
                logger.error("LINE_CHANNEL_ACCESS_TOKEN not configured")
                return False

            url = "https://api.line.me/v2/bot/message/reply"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {access_token}",
            }
            payload = {"replyToken": reply_token, "messages": [{"type": "text", "text": text}]}

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("LINE API rate limit exceeded")
            else:
                logger.error(f"LINE reply API failed: {e}", exc_info=True)
            return False
        except Exception as e:
            logger.error(f"LINE reply failed: {e}", exc_info=True)
            return False

    def process_webhook(self, body: str, signature: str) -> list[dict]:
        """Process incoming LINE webhook."""
        webhook_payload = json.loads(body)
        events = self.parse_webhook(webhook_payload)
        responses = []

        for event in events:
            external_user_id = event["external_user_id"]
            text = event["text"]
            reply_token = event["reply_token"]

            if self.is_otp_code(text):
                result = self.verify_otp_and_bind(text, external_user_id)
                self.send_reply(reply_token, result["message"])
                responses.append({"status": "otp_handled"})
                continue

            binding = self.session.exec(
                select(ChannelBinding)
                .where(ChannelBinding.channel_type == ChannelType.LINE)
                .where(ChannelBinding.external_user_id == external_user_id)
                .where(ChannelBinding.is_active == True)  # noqa: E712
            ).first()

            if not binding:
                self.send_reply(
                    reply_token,
                    "您尚未綁定帳號。請先在網頁版設定頁面產生驗證碼，然後在此輸入 6 位數驗證碼完成綁定。",
                )
                responses.append({"status": "unbound"})
                continue

            handler = BotMessageHandler(self.session)
            result = handler.handle_message(
                binding=binding, text=text, message_type=MessageType.TEXT
            )

            self.send_reply(reply_token, result.reply_text)
            responses.append({"status": "processed"})

        return responses
