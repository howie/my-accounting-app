"""Gemini Live API provider for real-time voice-to-voice conversations.

Uses the google-genai SDK Live API for bidirectional audio streaming
with Chinese language system prompt and text interrupt support.
"""

import asyncio
import base64
import logging
from typing import Any

from google import genai
from google.genai.types import (
    Content,
    LiveClientContent,
    LiveConnectConfig,
    LiveServerContent,
    Part,
    PrebuiltVoiceConfig,
    SpeechConfig,
    VoiceConfig,
)

logger = logging.getLogger(__name__)

# Chinese system prompt for Gemini Live voice conversations
VOICE_SYSTEM_PROMPT = """你是 LedgerOne 記帳應用程式的語音 AI 助手。

重要語言規則：
- 你必須全程使用繁體中文進行對話
- 無論使用者用什麼語言提問，你都必須用繁體中文回覆
- 理解使用者的中文語音輸入，並用自然流暢的繁體中文語音回覆
- 使用口語化的繁體中文，讓對話自然親切

你可以幫助使用者：
- 記帳和建立交易記錄
- 查詢帳戶餘額
- 查看交易記錄
- 管理帳本

回覆原則：
- 語音回覆要簡潔，不要太長
- 確認金額和帳戶時要清楚複述
- 如果聽不清楚，請使用者重複一次
- 保持友善自然的語調
"""


class GeminiLiveSession:
    """Manages a single Gemini Live API session for voice-to-voice interaction."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.0-flash-live-001",
        voice_name: str = "Aoede",
        system_prompt: str | None = None,
    ):
        self.api_key = api_key
        self.model_name = model_name
        self.voice_name = voice_name
        self.system_prompt = system_prompt or VOICE_SYSTEM_PROMPT
        self._client: genai.Client | None = None
        self._session: Any = None
        self._is_connected = False
        self._receive_task: asyncio.Task[None] | None = None
        self._on_audio_callback: Any = None
        self._on_text_callback: Any = None
        self._on_interrupted_callback: Any = None

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=self.api_key)
        return self._client

    def _build_config(self) -> LiveConnectConfig:
        """Build the Live API connection config with Chinese system prompt."""
        return LiveConnectConfig(
            response_modalities=["AUDIO"],
            system_instruction=Content(parts=[Part(text=self.system_prompt)]),
            speech_config=SpeechConfig(
                voice_config=VoiceConfig(
                    prebuilt_voice_config=PrebuiltVoiceConfig(
                        voice_name=self.voice_name,
                    )
                )
            ),
        )

    async def connect(
        self,
        on_audio: Any = None,
        on_text: Any = None,
        on_interrupted: Any = None,
    ) -> None:
        """Establish a Live API connection.

        Args:
            on_audio: Callback for audio data (base64-encoded PCM)
            on_text: Callback for text transcription
            on_interrupted: Callback when audio generation is interrupted
        """
        self._on_audio_callback = on_audio
        self._on_text_callback = on_text
        self._on_interrupted_callback = on_interrupted

        client = self._get_client()
        config = self._build_config()

        self._session = await client.aio.live.connect(
            model=self.model_name,
            config=config,
        )
        self._is_connected = True
        logger.info("Gemini Live session connected (model=%s)", self.model_name)

    async def start_receiving(self) -> None:
        """Start the async loop that receives responses from Gemini."""
        if not self._session:
            return

        self._receive_task = asyncio.create_task(self._receive_loop())

    async def _receive_loop(self) -> None:
        """Internal loop to receive and dispatch Gemini Live responses."""
        try:
            async for response in self._session.receive():
                await self._handle_response(response)
        except asyncio.CancelledError:
            logger.info("Gemini Live receive loop cancelled")
        except Exception:
            logger.exception("Error in Gemini Live receive loop")
            self._is_connected = False

    async def _handle_response(self, response: Any) -> None:
        """Process a response from the Gemini Live API."""
        server_content: LiveServerContent | None = getattr(response, "server_content", None)
        if server_content is None:
            return

        # Check if this is an interruption (turn_complete or interrupted)
        if getattr(server_content, "interrupted", False):
            logger.info("Gemini Live: generation interrupted")
            if self._on_interrupted_callback:
                await self._on_interrupted_callback()
            return

        model_turn = getattr(server_content, "model_turn", None)
        if model_turn is None:
            return

        for part in model_turn.parts:
            # Handle audio output
            if hasattr(part, "inline_data") and part.inline_data:
                audio_bytes = part.inline_data.data
                if audio_bytes and self._on_audio_callback:
                    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
                    await self._on_audio_callback(audio_b64, part.inline_data.mime_type)

            # Handle text output (transcript)
            if hasattr(part, "text") and part.text:
                if self._on_text_callback:
                    await self._on_text_callback(part.text)

    async def send_audio(self, audio_data: bytes, mime_type: str = "audio/pcm") -> None:
        """Send audio data to the Gemini Live session.

        Args:
            audio_data: Raw audio bytes (PCM 16-bit, 16kHz, mono)
            mime_type: Audio MIME type
        """
        if not self._session or not self._is_connected:
            logger.warning("Cannot send audio: session not connected")
            return

        await self._session.send(
            input=LiveClientContent(
                turns=[
                    Content(
                        role="user",
                        parts=[Part(inline_data={"mime_type": mime_type, "data": audio_data})],
                    )
                ],
                turn_complete=True,
            )
        )

    async def send_audio_stream(self, audio_data: bytes, mime_type: str = "audio/pcm") -> None:
        """Send streaming audio data (partial turn, no end_of_turn).

        Used for continuous microphone input. Gemini will use voice
        activity detection (VAD) to determine when the user stops speaking.

        Args:
            audio_data: Raw audio chunk bytes
            mime_type: Audio MIME type
        """
        if not self._session or not self._is_connected:
            return

        await self._session.send(
            input=LiveClientContent(
                turns=[
                    Content(
                        role="user",
                        parts=[Part(inline_data={"mime_type": mime_type, "data": audio_data})],
                    )
                ],
                turn_complete=False,
            )
        )

    async def send_text(self, text: str) -> None:
        """Send a text message to interrupt or supplement the voice conversation.

        This is the key feature for text-prompt interruption during v2v mode.
        When text is sent during ongoing voice generation, it will interrupt
        the current audio output and Gemini will respond to the text instead.

        Args:
            text: Text message to send (acts as interrupt if voice is active)
        """
        if not self._session or not self._is_connected:
            logger.warning("Cannot send text: session not connected")
            return

        logger.info("Sending text interrupt: %s", text[:50])
        await self._session.send(
            input=LiveClientContent(
                turns=[
                    Content(
                        role="user",
                        parts=[Part(text=text)],
                    )
                ],
                turn_complete=True,
            )
        )

    async def send_end_of_turn(self) -> None:
        """Signal end of user's turn (for manual turn management)."""
        if not self._session or not self._is_connected:
            return

        await self._session.send(input=LiveClientContent(turn_complete=True))

    async def disconnect(self) -> None:
        """Close the Live API session."""
        if self._receive_task and not self._receive_task.done():
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass

        if self._session:
            try:
                await self._session.close()
            except Exception:
                logger.exception("Error closing Gemini Live session")

        self._session = None
        self._is_connected = False
        self._receive_task = None
        logger.info("Gemini Live session disconnected")
