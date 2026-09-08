"""Long-polling loop for inbound Telegram bot commands (`getUpdates`), started once at
app startup and run for the life of the process - see
docs/adr/0012-telegram-bot-polling.md for why polling rather than a webhook.

This is the first persistent, gracefully-stoppable background task in this codebase
(the two `asyncio.create_task(...)` calls in main.py's startup are fire-and-forget,
run-once), so it owns its own task handle and explicit cancellation in
`stop_bot_polling`.

The loop always starts and idles (rather than only starting once settings say it should
run) - each iteration re-reads `TelegramSettings` fresh, so a config change takes effect
on the next iteration (worst case one long-poll timeout's delay) without needing a
settings-changed hook to start/stop it.
"""

import asyncio
import logging

from app.core.database import managed_session
from app.core.settings.telegram.crud.telegram_settings_crud import get_telegram_settings
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from app.core.settings.telegram.service.telegram_client import delete_webhook, get_updates
from app.core.telegram_bot.service.command_dispatcher import _handle_update

logger = logging.getLogger(__name__)

_IDLE_SLEEP_SECONDS = 30
_ERROR_BACKOFF_SECONDS = 5
_POLL_TIMEOUT_SECONDS = 25

_poll_task: asyncio.Task[None] | None = None


async def _get_settings() -> TelegramSettings:
    async with managed_session() as db:
        return await get_telegram_settings(db)


async def _poll_once(offset: int, cleared_for_token: str | None) -> tuple[int, str | None]:
    """Run one iteration of the poll loop body. Split out from `_poll_loop` so it's
    unit-testable without driving an infinite loop.

    `cleared_for_token` tracks which bot token last had `deleteWebhook` called for it -
    `getUpdates` and a webhook are mutually exclusive in the Bot API, so a token that was
    ever webhook-configured elsewhere would otherwise make every poll fail. Re-clears
    whenever the token changes, not on every iteration.
    """
    settings = await _get_settings()
    if not (settings.is_usable() and settings.bot_commands_enabled):
        await asyncio.sleep(_IDLE_SLEEP_SECONDS)
        return offset, cleared_for_token

    if settings.bot_token != cleared_for_token:
        await delete_webhook(settings.bot_token)
        cleared_for_token = settings.bot_token

    updates = await get_updates(settings.bot_token, offset, timeout=_POLL_TIMEOUT_SECONDS)
    for update in updates:
        offset = update["update_id"] + 1
        await _handle_update(update, settings)

    return offset, cleared_for_token


async def _poll_loop() -> None:
    offset = 0
    cleared_for_token: str | None = None
    while True:
        try:
            offset, cleared_for_token = await _poll_once(offset, cleared_for_token)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.error("Error in Telegram bot poll loop", exc_info=True)
            cleared_for_token = None
            await asyncio.sleep(_ERROR_BACKOFF_SECONDS)


def start_bot_polling() -> None:
    """Start the long-poll loop as a background task. Idempotent - a second call while
    already running is a no-op."""
    global _poll_task
    if _poll_task is not None and not _poll_task.done():
        return
    _poll_task = asyncio.create_task(_poll_loop())
    logger.info("Telegram bot polling loop started")


async def stop_bot_polling() -> None:
    """Cancel the poll loop and wait for it to exit. Safe to call even if it was never
    started."""
    global _poll_task
    if _poll_task is None:
        return
    _poll_task.cancel()
    try:
        await _poll_task
    except asyncio.CancelledError:
        pass
    _poll_task = None
    logger.info("Telegram bot polling loop stopped")
