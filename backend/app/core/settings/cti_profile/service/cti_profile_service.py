"""
CTI Profile Settings Service

Handles business logic for CTI (Cyber Threat Intelligence) profile settings management.
"""

from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.settings.cti_profile.crud.cti_profile_crud import (
    get_cti_settings,
    create_cti_settings,
    update_cti_settings
)
from app.core.settings.cti_profile.schemas.cti_profile_schemas import CTISettingsResponse, CTISettingsUpdate
from app.core.settings.cti_profile.config.default_settings import (
    get_default_cti_profile_settings,
    get_severity_levels,
    get_supported_ioc_types
)
import logging

logger = logging.getLogger(__name__)


async def get_cti_profile_settings(db: AsyncSession) -> CTISettingsResponse:
    """Retrieve CTI profile settings with default initialization if not found"""
    settings = await get_cti_settings(db)

    if not settings:
        logger.info("No CTI settings found, creating default settings")
        default_settings = get_default_cti_profile_settings()
        settings = await create_cti_settings(db, default_settings)
        await db.flush()
        await db.refresh(settings)

    return CTISettingsResponse(
        id=settings.id,
        settings=settings.get_settings_dict()
    )


async def update_cti_profile_settings(
    db: AsyncSession,
    settings_update: CTISettingsUpdate
) -> CTISettingsResponse:
    """Update CTI profile settings with validation"""
    validated_settings = _validate_cti_settings(settings_update.settings)

    settings = await update_cti_settings(db, validated_settings)
    await db.flush()
    await db.refresh(settings)

    logger.info("CTI settings updated successfully for ID: %s", settings.id)

    return CTISettingsResponse(
        id=settings.id,
        settings=settings.get_settings_dict()
    )


def _validate_cti_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Validate CTI settings structure and values"""
    required_fields = ["profile_name"]

    for field in required_fields:
        if field not in settings:
            raise ValueError(f"Missing required field: {field}")

    if not isinstance(settings.get("profile_name"), str) or len(settings["profile_name"].strip()) == 0:
        raise ValueError("Profile name must be a non-empty string")

    if "severity_threshold" in settings:
        valid_severities = get_severity_levels()
        if settings["severity_threshold"] not in valid_severities:
            raise ValueError(f"Invalid severity threshold. Must be one of: {valid_severities}")

    if "indicators_of_interest" in settings:
        if not isinstance(settings["indicators_of_interest"], list):
            raise ValueError("Indicators of interest must be a list")

        supported_types = get_supported_ioc_types()
        for indicator in settings["indicators_of_interest"]:
            if indicator not in supported_types:
                logger.warning("Unsupported IOC type: %s", indicator)

    if "notification_preferences" in settings:
        _validate_notification_preferences(settings["notification_preferences"])

    return settings


def _validate_notification_preferences(preferences: dict[str, Any]) -> None:
    """Validate notification preferences structure"""
    if not isinstance(preferences, dict):
        raise ValueError("Notification preferences must be a dictionary")

    if "email" in preferences:
        email_prefs = preferences["email"]
        if not isinstance(email_prefs, dict):
            raise ValueError("Email preferences must be a dictionary")

        if "enabled" in email_prefs and not isinstance(email_prefs["enabled"], bool):
            raise ValueError("Email enabled flag must be a boolean")

    if "webhook" in preferences:
        webhook_prefs = preferences["webhook"]
        if not isinstance(webhook_prefs, dict):
            raise ValueError("Webhook preferences must be a dictionary")

        if "enabled" in webhook_prefs and not isinstance(webhook_prefs["enabled"], bool):
            raise ValueError("Webhook enabled flag must be a boolean")
