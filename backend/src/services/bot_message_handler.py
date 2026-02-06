"""BotMessageHandler: shared message processing for all bot channels.

Wraps ChatService to provide a unified interface for bot adapters.
Handles message logging to ChannelMessageLog for audit trail.
"""

import logging
import time
import uuid

from sqlmodel import Session

from src.models.channel_binding import ChannelBinding
from src.models.channel_message_log import (
    ChannelMessageLog,
    MessageType,
    ProcessingStatus,
)
from src.models.user import User
from src.services.chat_service import ChatService

logger = logging.getLogger(__name__)

BOT_SYSTEM_PROMPT_SUFFIX = """
你現在是透過通訊軟體 Bot 與使用者對話。
回覆請保持簡短（適合手機閱讀），使用純文字格式（不支援 Markdown）。
如果使用者傳送的訊息看起來像記帳指令，直接處理不需額外確認。
如果訊息意圖不明確，請友善地詢問使用者想做什麼。
"""


class BotMessageResult:
    """Result of processing a bot message."""

    def __init__(
        self,
        reply_text: str,
        message_log_id: uuid.UUID | None = None,
        transaction_id: uuid.UUID | None = None,
        success: bool = True,
    ):
        self.reply_text = reply_text
        self.message_log_id = message_log_id
        self.transaction_id = transaction_id
        self.success = success


class BotMessageHandler:
    """Shared message handler for all bot channels.

    Accepts messages from bot adapters, delegates to ChatService for
    NLP processing and tool execution, and logs everything to ChannelMessageLog.
    """

    def __init__(self, session: Session):
        self.session = session

    def handle_message(
        self,
        *,
        binding: ChannelBinding,
        text: str,
        message_type: MessageType = MessageType.TEXT,
    ) -> BotMessageResult:
        """Process a message from a bot channel.

        Args:
            binding: The channel binding for this user+channel
            text: The message text (or transcribed voice text)
            message_type: Type of message (TEXT, VOICE, COMMAND)

        Returns:
            BotMessageResult with reply text and metadata
        """
        start_time = time.monotonic()

        # Create message log entry
        log_entry = ChannelMessageLog(
            channel_binding_id=binding.id,
            channel_type=binding.channel_type.value,
            message_type=message_type,
            raw_content=text,
            processing_status=ProcessingStatus.PROCESSING,
        )
        self.session.add(log_entry)
        self.session.flush()

        # Update binding last_used_at
        from datetime import UTC, datetime

        binding.last_used_at = datetime.now(UTC)

        try:
            # Get user for ChatService
            user = self.session.get(User, binding.user_id)
            if not user:
                return self._fail(log_entry, start_time, "使用者帳號不存在，請重新綁定。")

            # Determine ledger_id
            ledger_id = str(binding.default_ledger_id) if binding.default_ledger_id else None

            # Delegate to ChatService
            chat_service = ChatService(self.session, user)
            response = chat_service.chat(message=text, ledger_id=ledger_id)

            # Extract transaction_id from tool calls if a transaction was created
            transaction_id = self._extract_transaction_id(response.tool_calls)

            # Update message log
            processing_time = int((time.monotonic() - start_time) * 1000)
            log_entry.processing_status = ProcessingStatus.COMPLETED
            log_entry.response_text = response.message
            log_entry.transaction_id = transaction_id
            log_entry.processing_time_ms = processing_time
            log_entry.parsed_intent = self._infer_intent(response.tool_calls)

            self.session.commit()

            return BotMessageResult(
                reply_text=response.message,
                message_log_id=log_entry.id,
                transaction_id=transaction_id,
                success=True,
            )

        except Exception as e:
            logger.error("BotMessageHandler error: %s", e, exc_info=True)
            return self._fail(log_entry, start_time, "處理訊息時發生錯誤，請稍後再試。")

    def _fail(
        self,
        log_entry: ChannelMessageLog,
        start_time: float,
        error_message: str,
    ) -> BotMessageResult:
        """Mark a message log as failed and return error result."""
        processing_time = int((time.monotonic() - start_time) * 1000)
        log_entry.processing_status = ProcessingStatus.FAILED
        log_entry.error_message = error_message
        log_entry.processing_time_ms = processing_time
        self.session.commit()

        return BotMessageResult(
            reply_text=error_message,
            message_log_id=log_entry.id,
            success=False,
        )

    @staticmethod
    def _extract_transaction_id(tool_calls: list) -> uuid.UUID | None:
        """Extract transaction ID from tool call results if a transaction was created."""
        for tc in tool_calls:
            if (
                tc.tool_name == "create_transaction"
                and isinstance(tc.result, dict)
                and tc.result.get("success")
            ):
                tx_data = tc.result.get("transaction", {})
                tx_id = tx_data.get("id")
                if tx_id:
                    try:
                        return uuid.UUID(tx_id)
                    except (ValueError, TypeError):
                        pass
        return None

    @staticmethod
    def _infer_intent(tool_calls: list) -> str | None:
        """Infer the user's intent from tool calls executed."""
        if not tool_calls:
            return "UNKNOWN"

        tool_names = {tc.tool_name for tc in tool_calls}

        if "create_transaction" in tool_names:
            return "CREATE_TRANSACTION"
        if "list_accounts" in tool_names or "get_account" in tool_names:
            return "QUERY_BALANCE"
        if "list_transactions" in tool_names:
            return "QUERY_TRANSACTIONS"
        if "list_ledgers" in tool_names:
            return "LIST_ACCOUNTS"

        return "UNKNOWN"
