"""CTI Profile Settings CRUD"""

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings.cti_profile.models.cti_profile_models import CTIProfileSettings

logger = logging.getLogger(__name__)


async def get_cti_settings(db: AsyncSession) -> CTIProfileSettings | None:
    """Retrieve the first CTI profile settings record"""
    try:
        stmt = select(CTIProfileSettings).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error("Database error retrieving CTI settings: %s", str(e))
        raise


async def get_cti_settings_by_id(db: AsyncSession, settings_id: int) -> CTIProfileSettings | None:
    """Retrieve CTI profile settings by ID"""
    try:
        stmt = select(CTIProfileSettings).where(CTIProfileSettings.id == settings_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    except SQLAlchemyError as e:
        logger.error("Database error retrieving CTI settings by ID %s: %s", settings_id, str(e))
        raise


async def create_cti_settings(db: AsyncSession, settings_data: dict[str, Any]) -> CTIProfileSettings:
    """Create new CTI profile settings"""
    try:
        cti_settings = CTIProfileSettings()
        cti_settings.set_settings_dict(settings_data)

        db.add(cti_settings)
        await db.flush()

        logger.info("Created CTI settings with ID: %s", cti_settings.id)
        return cti_settings
    except SQLAlchemyError as e:
        logger.error("Database error creating CTI settings: %s", str(e))
        raise


async def update_cti_settings(db: AsyncSession, settings_data: dict[str, Any]) -> CTIProfileSettings:
    """Update existing CTI profile settings or create if not exists"""
    try:
        cti_settings = await get_cti_settings(db)

        if cti_settings:
            cti_settings.set_settings_dict(settings_data)
            logger.info("Updated existing CTI settings with ID: %s", cti_settings.id)
        else:
            cti_settings = CTIProfileSettings()
            cti_settings.set_settings_dict(settings_data)
            db.add(cti_settings)
            logger.info("Created new CTI settings")

        await db.flush()
        return cti_settings
    except SQLAlchemyError as e:
        logger.error("Database error updating CTI settings: %s", str(e))
        raise


async def delete_cti_settings(db: AsyncSession, settings_id: int) -> bool:
    """Delete CTI profile settings by ID"""
    try:
        cti_settings = await get_cti_settings_by_id(db, settings_id)
        if not cti_settings:
            return False

        await db.delete(cti_settings)
        await db.flush()

        logger.info("Deleted CTI settings with ID: %s", settings_id)
        return True
    except SQLAlchemyError as e:
        logger.error("Database error deleting CTI settings: %s", str(e))
        raise
