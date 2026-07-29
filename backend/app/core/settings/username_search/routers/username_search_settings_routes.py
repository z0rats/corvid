"""Username Search (Maigret) settings routes - timeout, concurrency, proxy"""

import logging

from fastapi import APIRouter

from app.core.dependencies import ReadSessionDep, SessionDep
from app.features.username_search.service.db_refresh_scheduler_service import configure_maigret_db_scheduler
from app.core.settings.username_search.crud.username_search_settings_crud import (
    get_username_search_config as crud_get_config,
    update_username_search_config as crud_update_config,
)
from app.core.settings.username_search.schemas.username_search_settings_schemas import (
    UsernameSearchConfigSchema,
    UsernameSearchConfigUpdateSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings/username-search", tags=["Username Search Settings"])


@router.get(
    "",
    response_model=UsernameSearchConfigSchema,
    response_model_exclude_none=True,
    summary="Get username search config",
    description="Get username search (Maigret) configuration",
)
async def get_username_search_config(db: ReadSessionDep) -> UsernameSearchConfigSchema:
    """Get current username search configuration"""
    return UsernameSearchConfigSchema.model_validate(await crud_get_config(db))


@router.put(
    "",
    response_model=UsernameSearchConfigSchema,
    response_model_exclude_none=True,
    summary="Update username search config",
    description="Update username search (Maigret) configuration",
)
async def update_username_search_config(
    config_data: UsernameSearchConfigUpdateSchema, db: SessionDep
) -> UsernameSearchConfigSchema:
    """Update username search configuration"""
    updated_config = await crud_update_config(db, config_data)
    if config_data.auto_update_db_enabled is not None or config_data.auto_update_interval_hours is not None:
        configure_maigret_db_scheduler(updated_config.auto_update_db_enabled, updated_config.auto_update_interval_hours)
    logger.info("Updated username search configuration.")
    return UsernameSearchConfigSchema.model_validate(updated_config)
