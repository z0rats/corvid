from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.singleton import get_or_create_singleton
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings


async def get_telegram_settings(db: AsyncSession) -> TelegramSettings:
    """Retrieve the Telegram settings record, creating defaults if not exists."""
    return await get_or_create_singleton(db, TelegramSettings)


async def update_telegram_settings(
    db: AsyncSession,
    settings: TelegramSettings,
    **fields: str | bool | None,
) -> TelegramSettings:
    """Update Telegram settings fields."""
    for key, value in fields.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
    await db.flush()
    return settings
