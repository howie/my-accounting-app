"""Voice chat WebSocket endpoint for Gemini Live API v2v interaction.

Supports:
- Bidirectional audio streaming (PCM 16-bit, 16kHz, mono)
- Text prompt interrupts during voice conversation
- Chinese language system prompt enforcement

WebSocket message protocol:
  Client -> Server:
    {"type": "audio", "data": "<base64-pcm>", "mime_type": "audio/pcm"}
    {"type": "text", "text": "文字訊息"}  # Text interrupt
    {"type": "end_turn"}                   # Signal end of speaking
    {"type": "disconnect"}                 # Close session

  Server -> Client:
    {"type": "audio", "data": "<base64-pcm>", "mime_type": "audio/pcm;rate=24000"}
    {"type": "text", "text": "transcript"}
    {"type": "interrupted"}                # Audio generation was interrupted
    {"type": "error", "message": "..."}
    {"type": "connected"}                  # Session ready
"""

import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from src.core.config import get_settings
from src.services.llm.gemini_live_provider import GeminiLiveSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["voice"])


@router.websocket("/ws")
async def voice_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for voice-to-voice conversation with Gemini Live API.

    The connection flow:
    1. Client connects via WebSocket
    2. Server establishes Gemini Live session with Chinese system prompt
    3. Client streams audio data, server relays to Gemini
    4. Server streams Gemini audio responses back to client
    5. Client can send text messages to interrupt voice at any time
    """
    await websocket.accept()
    settings = get_settings()

    if not settings.gemini_api_key:
        await websocket.send_json(
            {
                "type": "error",
                "message": "Gemini API key 未設定。請先設定 GEMINI_API_KEY。",
            }
        )
        await websocket.close(code=1008)
        return

    session = GeminiLiveSession(
        api_key=settings.gemini_api_key,
        model_name=settings.gemini_live_model,
        voice_name=settings.gemini_voice_name,
    )

    async def on_audio(audio_b64: str, mime_type: str) -> None:
        """Forward Gemini audio output to client."""
        try:
            await websocket.send_json(
                {
                    "type": "audio",
                    "data": audio_b64,
                    "mime_type": mime_type,
                }
            )
        except Exception:
            logger.exception("Error sending audio to client")

    async def on_text(text: str) -> None:
        """Forward Gemini text transcript to client."""
        try:
            await websocket.send_json(
                {
                    "type": "text",
                    "text": text,
                }
            )
        except Exception:
            logger.exception("Error sending text to client")

    async def on_interrupted() -> None:
        """Notify client that generation was interrupted."""
        try:
            await websocket.send_json({"type": "interrupted"})
        except Exception:
            logger.exception("Error sending interrupted signal")

    try:
        # Connect to Gemini Live API
        await session.connect(
            on_audio=on_audio,
            on_text=on_text,
            on_interrupted=on_interrupted,
        )
        await session.start_receiving()
        await websocket.send_json({"type": "connected"})

        # Main message loop
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            msg_type = msg.get("type", "")

            if msg_type == "audio":
                # Relay audio to Gemini
                audio_b64 = msg.get("data", "")
                mime_type = msg.get("mime_type", "audio/pcm")
                audio_bytes = base64.b64decode(audio_b64)
                await session.send_audio_stream(audio_bytes, mime_type)

            elif msg_type == "text":
                # Text interrupt: sends text to interrupt current voice generation
                text = msg.get("text", "")
                if text.strip():
                    await session.send_text(text)

            elif msg_type == "end_turn":
                await session.send_end_of_turn()

            elif msg_type == "disconnect":
                break

    except WebSocketDisconnect:
        logger.info("Voice WebSocket client disconnected")
    except json.JSONDecodeError:
        logger.warning("Invalid JSON received on voice WebSocket")
        await websocket.send_json(
            {
                "type": "error",
                "message": "無效的訊息格式",
            }
        )
    except Exception:
        logger.exception("Voice WebSocket error")
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "語音連線發生錯誤",
                }
            )
        except Exception:
            pass
    finally:
        await session.disconnect()
