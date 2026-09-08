from app.core.dependencies import SessionDep
from app.core.settings.settings_router_factory import build_singleton_settings_router
from app.core.settings.telegram.schemas.telegram_settings_schemas import (
    TelegramSettingsResponse,
    TelegramSettingsUpdate,
    TelegramTestMessageResponse,
)
from app.core.settings.telegram.service.telegram_settings_service import (
    get_or_create_telegram_settings,
    send_test_message,
    update_telegram_settings_values,
)

router = build_singleton_settings_router(
    prefix="/api/settings/telegram",
    tags=["Telegram Settings"],
    response_schema=TelegramSettingsResponse,
    update_schema=TelegramSettingsUpdate,
    get_service=get_or_create_telegram_settings,
    update_service=update_telegram_settings_values,
)


@router.post(
    "/test",
    response_model=TelegramTestMessageResponse,
    summary="Send a Telegram test message",
    description="Sends a fixed test message using the currently saved bot token/chat ID",
)
async def send_test_message_endpoint(db: SessionDep) -> TelegramTestMessageResponse:
    return await send_test_message(db)
