"""Raises an alert: persists it, broadcasts it over WebSocket, and (best-effort)
delivers it to Telegram if configured. The single entrypoint every notification-
worthy event should call - see docs/adr/0011-telegram-notifications.md.
"""

import logging
from typing import Literal

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.alerts.crud import alerts_crud
from app.core.alerts.models.alerts_models import Alert
from app.core.alerts.schemas.alerts_schemas import AlertSchema
from app.core.alerts.utils.alerts_websocket import manager
from app.core.settings.telegram.crud.telegram_settings_crud import get_telegram_settings
from app.core.settings.telegram.service.telegram_client import (
    TelegramDeliveryError,
    send_telegram_message,
)

logger = logging.getLogger(__name__)

MESSAGE_MAX_LENGTH = 1000

# "scan_failed"/"job_transition"/"security" are inherently rare and actionable (a
# failure, an edge-triggered health transition, or a security-relevant instance
# event - token regeneration, an API key add/update/delete, a backup export/
# restore, repeated failed-auth attempts) - they always create an alert and push
# to Telegram whenever the master switch is on, no dedicated toggle.
# "scan_finished" (routine completions/cancellations) and "newsfeed_match" (a
# newsfeed article matched a watchlist keyword) are the categories that can fire
# often and have no other consumer besides the Telegram settings toggle - so
# their toggle (`_EXISTENCE_TOGGLES` below) governs whether the alert is created
# at all, not just whether Telegram fires, to avoid flooding the in-app alerts
# inbox for anyone who hasn't opted in.
TelegramCategory = Literal[
    "scan_failed", "scan_finished", "job_transition", "security", "newsfeed_match"
]

# category -> TelegramSettings field gating the alert's existence (not just Telegram).
_EXISTENCE_TOGGLES = {
    "scan_finished": "notify_scan_events",
    "newsfeed_match": "notify_newsfeed_matches",
}
# category -> TelegramSettings field gating only the Telegram push (the alert
# itself is always created).
_TELEGRAM_ONLY_TOGGLES = {
    "job_transition": "notify_job_failures",
}


async def raise_alert(
    db: AsyncSession,
    module: str,
    title: str,
    message: str,
    *,
    telegram_category: TelegramCategory | None = None,
) -> Alert | None:
    """Create an alert, broadcast it to connected WS clients, and (best-effort)
    push it to Telegram. Returns `None` without creating anything if the
    category is in `_EXISTENCE_TOGGLES` and the user has muted it - see the
    module-level comment on `TelegramCategory`.
    """
    settings = None
    if telegram_category is not None:
        settings = await get_telegram_settings(db)
        existence_toggle = _EXISTENCE_TOGGLES.get(telegram_category)
        if existence_toggle is not None and not getattr(settings, existence_toggle):
            return None

    alert = await alerts_crud.create_alert(
        db, module=module, title=title, message=message[:MESSAGE_MAX_LENGTH]
    )
    await manager.broadcast(AlertSchema.model_validate(alert).model_dump(mode="json"))

    if settings is not None and settings.is_usable():
        assert telegram_category is not None  # settings is only set when it was
        telegram_toggle = _TELEGRAM_ONLY_TOGGLES.get(telegram_category)
        if telegram_toggle is not None and not getattr(settings, telegram_toggle):
            return alert
        try:
            await send_telegram_message(
                settings.bot_token, settings.chat_id, f"{title}\n\n{message}"
            )
        except TelegramDeliveryError as exc:
            logger.warning("Telegram delivery failed: %s", exc)

    return alert
