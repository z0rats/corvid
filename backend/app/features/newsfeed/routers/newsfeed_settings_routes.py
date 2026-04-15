"""Newsfeed settings routes - feed configuration, retention, enable/disable"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.scheduler import update_scheduler_configuration
from app.features.newsfeed.crud.newsfeed_settings_crud import (
    get_all_newsfeed_settings,
    update_newsfeed_setting,
    toggle_feed_status,
)
from app.features.newsfeed.service.icon_management_service import icon_exists
from app.features.newsfeed.crud.newsfeed_config_crud import (
    get_newsfeed_config as crud_get_config,
    update_newsfeed_config as crud_update_config,
    get_retention_days as crud_get_retention,
    set_retention_days as crud_set_retention,
)
from app.features.newsfeed.schemas.newsfeed_schemas import (
    NewsfeedSettingsSchema,
    NewsfeedConfigSchema,
    NewsfeedConfigUpdateSchema,
    FeedStatusUpdate,
    RetentionDaysUpdate,
    RetentionDaysResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings", tags=["Newsfeed Settings"])


@router.get(
    "/modules/newsfeed",
    response_model=list[NewsfeedSettingsSchema],
    response_model_exclude_none=True,
    summary="List newsfeeds",
    description="Retrieve all configured newsfeed settings",
    responses={404: {"description": "No settings found"}},
)
async def read_newsfeed_settings(db: ReadSessionDep) -> list[NewsfeedSettingsSchema]:
    """Get all newsfeed settings"""
    settings = await get_all_newsfeed_settings(db)
    if not settings:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No settings found")

    response = []
    for s in settings:
        schema = NewsfeedSettingsSchema.model_validate(s)
        if schema.icon != "default.png" and not icon_exists(schema.icon):
            schema.icon = "default.png"
        response.append(schema)
    return response


@router.put(
    "/modules/newsfeed",
    response_model=NewsfeedSettingsSchema,
    response_model_exclude_none=True,
    summary="Update newsfeed",
    description="Update settings for a specific newsfeed",
)
async def update_settings(settings: NewsfeedSettingsSchema, db: SessionDep) -> NewsfeedSettingsSchema:
    """Update newsfeed settings by name"""
    updated = await update_newsfeed_setting(db, settings.name, settings)
    logger.info("Updated newsfeed settings for %s.", settings.name)
    return NewsfeedSettingsSchema.model_validate(updated)


@router.patch(
    "/modules/newsfeed/{feed_name}/status",
    response_model=NewsfeedSettingsSchema,
    response_model_exclude_none=True,
    summary="Toggle newsfeed status",
    description="Enable or disable a newsfeed by name",
    responses={404: {"description": "Newsfeed not found"}},
)
async def update_feed_status(
    feed_name: str,
    update: FeedStatusUpdate,
    db: SessionDep,
) -> NewsfeedSettingsSchema:
    """Enable or disable a newsfeed"""
    feed = await toggle_feed_status(db, feed_name, update.enabled)
    if not feed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Newsfeed not found")
    action = "Enabled" if update.enabled else "Disabled"
    logger.info("%s newsfeed %s.", action, feed_name)
    return NewsfeedSettingsSchema.model_validate(feed)


@router.get(
    "/newsfeed/retention",
    response_model=int,
    summary="Get retention period",
    description="Get the number of days articles are retained before deletion",
)
async def get_retention_days(db: ReadSessionDep) -> int:
    """Get the current article retention period in days"""
    return await crud_get_retention(db)


@router.put(
    "/newsfeed/retention",
    response_model=RetentionDaysResponse,
    summary="Update retention period",
    description="Update the number of days articles are retained before deletion",
)
async def update_retention_days(update: RetentionDaysUpdate, db: SessionDep) -> RetentionDaysResponse:
    """Update the article retention period"""
    await crud_set_retention(db, update.retention_days)
    return RetentionDaysResponse(message="Retention days updated successfully", retention_days=update.retention_days)


@router.get(
    "/newsfeed/config",
    response_model=NewsfeedConfigSchema,
    response_model_exclude_none=True,
    summary="Get newsfeed config",
    description="Get newsfeed configuration including background fetch settings",
)
async def get_newsfeed_config(db: ReadSessionDep) -> NewsfeedConfigSchema:
    """Get current newsfeed configuration"""
    return NewsfeedConfigSchema.model_validate(await crud_get_config(db))


@router.put(
    "/newsfeed/config",
    response_model=NewsfeedConfigSchema,
    response_model_exclude_none=True,
    summary="Update newsfeed config",
    description="Update newsfeed configuration and reconfigure the background fetch scheduler",
)
async def update_newsfeed_config(config_data: NewsfeedConfigUpdateSchema, db: SessionDep) -> NewsfeedConfigSchema:
    """Update newsfeed configuration and restart scheduler with new settings"""
    updated_config = await crud_update_config(db, config_data)
    await update_scheduler_configuration()
    logger.info("Updated newsfeed configuration and triggered scheduler update.")
    return NewsfeedConfigSchema.model_validate(updated_config)
