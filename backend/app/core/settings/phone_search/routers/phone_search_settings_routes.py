"""Phone Search settings routes - timeout, optional proxy"""

from app.core.settings.phone_search.crud.phone_search_settings_crud import (
    get_phone_search_config as crud_get_config,
)
from app.core.settings.phone_search.crud.phone_search_settings_crud import (
    update_phone_search_config as crud_update_config,
)
from app.core.settings.phone_search.schemas.phone_search_settings_schemas import (
    PhoneSearchConfigSchema,
    PhoneSearchConfigUpdateSchema,
)
from app.core.settings.settings_router_factory import build_singleton_settings_router

router = build_singleton_settings_router(
    prefix="/api/settings/phone-search",
    tags=["Phone Search Settings"],
    response_schema=PhoneSearchConfigSchema,
    update_schema=PhoneSearchConfigUpdateSchema,
    get_service=crud_get_config,
    update_service=crud_update_config,
    exclude_none=True,
)
