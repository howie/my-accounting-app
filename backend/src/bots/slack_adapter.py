"""Slack Bot adapter for webhook handling."""

import hashlib
import hmac
import json
import logging
import re
import time

import requests
from sqlmodel import Session, select

from src.core.config import get_settings
from src.models.channel_binding import ChannelBinding, ChannelType
from src.models.channel_message_log import MessageType
from src.services.bot_message_handler import BotMessageHandler
from src.services.channel_binding_service import ChannelBindingService

logger = logging.getLogger(__name__)


class SlackAdapter:
    """Adapter for Slack Events API webhooks."""

    def __init__(self, session: Session):
        self.session = session

    def verify_signature(self, body: str, signature: str | None, timestamp: str | None) -> bool:
        """Verify X-Slack-Signature HMAC-SHA256 header with timestamp."""
        if not signature or not timestamp:
            return False

        signing_secret = get_settings().slack_signing_secret
        if not signing_secret:
            logger.warning("SLACK_SIGNING_SECRET not configured")
            return False

        try:
            ts = int(timestamp)
            current_time = int(time.time())
            if abs(current_time - ts) > 300:
                logger.warning("Slack timestamp too old (replay attack protection)")
                return False
        except ValueError:
            return False

        base_string = f"v0:{timestamp}:{body}"
        expected_signature = (
            "v0="
            + hmac.new(
                signing_secret.encode("utf-8"),
                base_string.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()
        )

        return hmac.compare_digest(signature, expected_signature)

    def handle_url_verification(self, payload: dict) -> dict:
        """Handle Slack url_verification challenge."""
        return {"challenge": payload.get("challenge")}

    def parse_event(self, webhook_payload: dict) -> dict | None:
        """Parse Slack event callback."""
        if webhook_payload.get("type") != "event_callback":
            return None

        event = webhook_payload.get("event", {})
        if event.get("type") != "message":
            return None

        if event.get("subtype"):
            return None

        external_user_id = event.get("user")
        text = event.get("text")

        if not external_user_id or not text:
            return None

        return {
            "text": text,
            "external_user_id": external_user_id,
            "channel": event.get("channel"),
            "event_type": "message",
        }

    def parse_slash_command(self, command_payload: dict) -> dict | None:
        """Parse Slack slash command."""
        return {
            "text": command_payload.get("text", ""),
            "external_user_id": command_payload.get("user_id"),
            "command": command_payload.get("command"),
            "response_url": command_payload.get("response_url"),
        }

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
            return {"success": True, "message": "已成功綁定！您現在可以使用 Slack Bot 進行記帳。"}
        else:
            return {"success": False, "message": "驗證碼無效或已過期，請重新產生驗證碼。"}

    def send_message(self, channel: str, text: str) -> bool:
        """Send message to Slack channel."""
        try:
            bot_token = get_settings().slack_bot_token
            if not bot_token:
                logger.error("SLACK_BOT_TOKEN not configured")
                return False

            url = "https://slack.com/api/chat.postMessage"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {bot_token}"}
            payload = {"channel": channel, "text": text}

            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            return True

        except Exception as e:
            logger.error(f"Slack message send failed: {e}", exc_info=True)
            return False

    def handle_slash_command(self, command_payload: dict) -> dict:
        """Handle Slack slash command."""
        parsed = self.parse_slash_command(command_payload)
        if not parsed:
            return {"response_type": "ephemeral", "text": "Invalid command"}

        external_user_id = parsed["external_user_id"]
        text = parsed["text"]

        if self.is_otp_code(text):
            result = self.verify_otp_and_bind(text, external_user_id)
            return {"response_type": "ephemeral", "text": result["message"]}

        binding = self.session.exec(
            select(ChannelBinding)
            .where(ChannelBinding.channel_type == ChannelType.SLACK)
            .where(ChannelBinding.external_user_id == external_user_id)
            .where(ChannelBinding.is_active == True)  # noqa: E712
        ).first()

        if not binding:
            return {
                "response_type": "ephemeral",
                "text": "您尚未綁定帳號。請先在網頁版設定頁面產生驗證碼，然後在此輸入 6 位數驗證碼完成綁定。",
            }

        handler = BotMessageHandler(self.session)
        result = handler.handle_message(binding=binding, text=text, message_type=MessageType.TEXT)

        return {"response_type": "ephemeral", "text": result.reply_text}

    def process_webhook(self, body: str, signature: str, timestamp: str) -> dict | None:
        """Process incoming Slack webhook."""
        webhook_payload = json.loads(body)

        if webhook_payload.get("type") == "url_verification":
            return self.handle_url_verification(webhook_payload)

        event = self.parse_event(webhook_payload)
        if not event:
            return None

        external_user_id = event["external_user_id"]
        text = event["text"]
        channel = event["channel"]

        if self.is_otp_code(text):
            result = self.verify_otp_and_bind(text, external_user_id)
            self.send_message(channel, result["message"])
            return {"status": "otp_handled"}

        binding = self.session.exec(
            select(ChannelBinding)
            .where(ChannelBinding.channel_type == ChannelType.SLACK)
            .where(ChannelBinding.external_user_id == external_user_id)
            .where(ChannelBinding.is_active == True)  # noqa: E712
        ).first()

        if not binding:
            self.send_message(
                channel,
                "您尚未綁定帳號。請先在網頁版設定頁面產生驗證碼，然後在此輸入 6 位數驗證碼完成綁定。",
            )
            return {"status": "unbound"}

        handler = BotMessageHandler(self.session)
        result = handler.handle_message(binding=binding, text=text, message_type=MessageType.TEXT)

        self.send_message(channel, result.reply_text)
        return {"status": "processed"}
