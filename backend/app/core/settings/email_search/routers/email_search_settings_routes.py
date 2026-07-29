"""Email Search (mailcat) settings routes - timeout, concurrency, proxy/Tor, optional checkers"""

from app.core.settings.email_search.crud.email_search_settings_crud import (
    get_email_search_config as crud_get_config,
    update_email_search_config as crud_update_config,
)
from app.core.settings.email_search.schemas.email_search_settings_schemas import (
    EmailSearchConfigSchema,
    EmailSearchConfigUpdateSchema,
)
from app.core.settings.settings_router_factory import build_singleton_settings_router

router = build_singleton_settings_router(
    prefix="/api/settings/email-search",
    tags=["Email Search Settings"],
    response_schema=EmailSearchConfigSchema,
    update_schema=EmailSearchConfigUpdateSchema,
    get_service=crud_get_config,
    update_service=crud_update_config,
    exclude_none=True,
)
