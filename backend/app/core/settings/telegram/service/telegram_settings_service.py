import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationError
from app.core.settings.telegram.crud.telegram_settings_crud import (
    get_telegram_settings as _get_telegram_settings,
)
from app.core.settings.telegram.crud.telegram_settings_crud import (
    update_telegram_settings as _update_telegram_settings,
)
from app.core.settings.telegram.schemas.telegram_settings_schemas import (
    TelegramSettingsResponse,
    TelegramSettingsUpdate,
    TelegramTestMessageResponse,
)
from app.core.settings.telegram.service.telegram_client import (
    TelegramDeliveryError,
    send_telegram_message,
)

logger = logging.getLogger(__name__)

_UPDATE_FIELDS = (
    "bot_token",
    "chat_id",
    "enabled",
    "notify_scan_events",
    "notify_job_failures",
    "notify_newsfeed_matches",
    "bot_commands_enabled",
    "web_base_url",
)

TEST_MESSAGE = "✅ Corvid Telegram notifications are connected."


async def get_or_create_telegram_settings(db: AsyncSession) -> TelegramSettingsResponse:
    """Retrieve current Telegram settings, creating defaults if none exist."""
    settings = await _get_telegram_settings(db)
    return TelegramSettingsResponse.model_validate(settings)


async def update_telegram_settings_values(
    db: AsyncSession, settings_update: TelegramSettingsUpdate
) -> TelegramSettingsResponse:
    """Update Telegram settings with the provided values."""
    settings = await _get_telegram_settings(db)

    fields = {
        name: value
        for name in _UPDATE_FIELDS
        if (value := getattr(settings_update, name)) is not None
    }
    if fields:
        if "bot_token" in fields:
            fields["bot_token"] = fields["bot_token"].strip()
        if "chat_id" in fields:
            fields["chat_id"] = fields["chat_id"].strip()
        if "web_base_url" in fields:
            fields["web_base_url"] = fields["web_base_url"].strip().rstrip("/")
        settings = await _update_telegram_settings(db, settings, **fields)

    await db.flush()
    await db.refresh(settings)

    logger.info("Updated Telegram settings: enabled=%s", settings.enabled)
    return TelegramSettingsResponse.model_validate(settings)


async def send_test_message(db: AsyncSession) -> TelegramTestMessageResponse:
    """Send a fixed test message through the currently saved settings, surfacing
    any delivery failure to the caller (unlike alerts_service's best-effort
    notify path, this endpoint exists specifically to validate configuration)."""
    settings = await _get_telegram_settings(db)
    if not settings.is_configured():
        raise ApplicationError(
            "Set a bot token and chat ID before sending a test message.",
            status_code=400,
            error_code="TELEGRAM_NOT_CONFIGURED",
        )

    try:
        await send_telegram_message(settings.bot_token, settings.chat_id, TEST_MESSAGE)
    except TelegramDeliveryError as exc:
        raise ApplicationError(
            f"Could not deliver the test message: {exc}",
            status_code=502,
            error_code="TELEGRAM_TEST_FAILED",
        ) from None

    return TelegramTestMessageResponse(sent=True, message="Test message delivered.")
