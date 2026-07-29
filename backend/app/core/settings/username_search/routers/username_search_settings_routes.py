"""Username Search (Maigret) settings routes - timeout, concurrency, proxy"""

from app.features.username_search.service.db_refresh_scheduler_service import configure_maigret_db_scheduler
from app.core.settings.username_search.crud.username_search_settings_crud import (
    get_username_search_config as crud_get_config,
    update_username_search_config as crud_update_config,
)
from app.core.settings.username_search.schemas.username_search_settings_schemas import (
    UsernameSearchConfigSchema,
    UsernameSearchConfigUpdateSchema,
)
from app.core.settings.settings_router_factory import build_singleton_settings_router


def _maybe_reconfigure_scheduler(payload: UsernameSearchConfigUpdateSchema, updated) -> None:
    if payload.auto_update_db_enabled is not None or payload.auto_update_interval_hours is not None:
        configure_maigret_db_scheduler(updated.auto_update_db_enabled, updated.auto_update_interval_hours)


router = build_singleton_settings_router(
    prefix="/api/settings/username-search",
    tags=["Username Search Settings"],
    response_schema=UsernameSearchConfigSchema,
    update_schema=UsernameSearchConfigUpdateSchema,
    get_service=crud_get_config,
    update_service=crud_update_config,
    on_after_update=_maybe_reconfigure_scheduler,
    exclude_none=True,
)
