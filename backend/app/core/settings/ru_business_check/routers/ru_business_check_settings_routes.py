"""RU Business Check settings routes - flag-engine thresholds, history retention"""

from app.core.settings.ru_business_check.crud.ru_business_check_settings_crud import (
    get_ru_business_check_settings as crud_get_settings,
)
from app.core.settings.ru_business_check.crud.ru_business_check_settings_crud import (
    update_ru_business_check_settings as crud_update_settings,
)
from app.core.settings.ru_business_check.schemas.ru_business_check_settings_schemas import (
    RuBusinessCheckSettingsSchema,
    RuBusinessCheckSettingsUpdateSchema,
)
from app.core.settings.settings_router_factory import build_singleton_settings_router

router = build_singleton_settings_router(
    prefix="/api/settings/ru-business-check",
    tags=["RU Business Check Settings"],
    response_schema=RuBusinessCheckSettingsSchema,
    update_schema=RuBusinessCheckSettingsUpdateSchema,
    get_service=crud_get_settings,
    update_service=crud_update_settings,
    exclude_none=True,
)
