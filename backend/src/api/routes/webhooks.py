"""Webhook routes for bot channels.

Handles incoming webhooks from Telegram, LINE, and Slack.
Rate limited to 30 req/min per user (FR-012).
"""

import json
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlmodel import Session

from src.api.deps import get_session
from src.api.rate_limit import limiter
from src.bots.line_adapter import LINEAdapter
from src.bots.slack_adapter import SlackAdapter
from src.bots.telegram_adapter import TelegramAdapter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/webhooks/telegram")
@limiter.limit("30/minute")
async def telegram_webhook(
    request: Request,
    session: Session = Depends(get_session),
    x_telegram_bot_api_secret_token: str | None = Header(None),
):
    """Handle Telegram Bot webhook."""
    try:
        adapter = TelegramAdapter(session)

        if not adapter.verify_signature(x_telegram_bot_api_secret_token):
            raise HTTPException(status_code=401, detail="Invalid signature")

        update = await request.json()
        adapter.process_webhook(update)

        return {"ok": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        return {"ok": True}


@router.post("/webhooks/line")
@limiter.limit("30/minute")
async def line_webhook(
    request: Request,
    session: Session = Depends(get_session),
    x_line_signature: str | None = Header(None),
):
    """Handle LINE Bot webhook."""
    try:
        body = await request.body()
        body_str = body.decode("utf-8")

        adapter = LINEAdapter(session)

        if not adapter.verify_signature(body_str, x_line_signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

        adapter.process_webhook(body_str, x_line_signature)

        return {"ok": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LINE webhook error: {e}", exc_info=True)
        return {"ok": True}


@router.post("/webhooks/slack")
@limiter.limit("30/minute")
async def slack_webhook(
    request: Request,
    session: Session = Depends(get_session),
    x_slack_signature: str | None = Header(None),
    x_slack_request_timestamp: str | None = Header(None),
):
    """Handle Slack Bot webhook and url_verification."""
    try:
        body = await request.body()
        body_str = body.decode("utf-8")

        adapter = SlackAdapter(session)

        payload = json.loads(body_str)

        if payload.get("type") == "url_verification":
            return adapter.handle_url_verification(payload)

        if not adapter.verify_signature(body_str, x_slack_signature, x_slack_request_timestamp):
            raise HTTPException(status_code=401, detail="Invalid signature")

        adapter.process_webhook(body_str, x_slack_signature, x_slack_request_timestamp)

        return {"ok": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Slack webhook error: {e}", exc_info=True)
        return {"ok": True}
