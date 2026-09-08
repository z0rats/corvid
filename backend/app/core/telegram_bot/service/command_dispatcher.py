"""Parses and dispatches one inbound Telegram update, then replies.

The chat_id check below is the security boundary for this whole feature: without it,
anyone who finds the bot on Telegram could run lookups (and read alert titles) through
this Corvid instance. See docs/adr/0012-telegram-bot-polling.md.
"""

import logging
from typing import Any

from app.core.database import managed_session
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from app.core.settings.telegram.service.telegram_client import (
    TelegramDeliveryError,
    send_telegram_message,
)
from app.core.telegram_bot.service.commands import handle_digest, handle_help, handle_lookup

logger = logging.getLogger(__name__)

_LOOKUP_ACK = "\U0001f50d Looking up..."
_UNRECOGNIZED_REPLY = "Unrecognized command. Try /help."


async def _handle_update(update: dict[str, Any], settings: TelegramSettings) -> None:
    """Process one Telegram update. Never raises - a malformed update or a downstream
    failure is logged and swallowed so one bad update can't kill the poll loop."""
    message = update.get("message")
    if not isinstance(message, dict):
        return

    chat_id = message.get("chat", {}).get("id")
    if chat_id is None or str(chat_id) != str(settings.chat_id):
        # Not our configured chat - silently ignored, not replied to.
        return

    text = (message.get("text") or "").strip()
    if not text:
        return

    command, _, rest = text.partition(" ")
    command = command.split("@", 1)[0].lower()
    rest = rest.strip()

    try:
        reply = await _dispatch(command, rest, settings)
        await send_telegram_message(settings.bot_token, settings.chat_id, reply)
    except TelegramDeliveryError as exc:
        logger.warning("Telegram delivery failed while replying to a command: %s", exc)
    except Exception:
        logger.error("Error handling Telegram command %r", command, exc_info=True)


async def _dispatch(command: str, rest: str, settings: TelegramSettings) -> str:
    if command == "/help":
        return handle_help()

    if command == "/digest":
        async with managed_session() as db:
            return await handle_digest(db)

    if command == "/lookup":
        if not rest:
            return "Usage: /lookup <value>"
        # Ack immediately - the gather below can take tens of seconds per the
        # retry/backoff config in rate_limiting_config.py.
        await send_telegram_message(settings.bot_token, settings.chat_id, _LOOKUP_ACK)
        async with managed_session() as db:
            return await handle_lookup(db, rest, settings.web_base_url)

    return _UNRECOGNIZED_REPLY
