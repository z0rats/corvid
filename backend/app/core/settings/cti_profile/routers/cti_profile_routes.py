"""
CTI Profile Settings Routes

FastAPI routes for CTI (Cyber Threat Intelligence) profile settings management.
"""

import logging

from fastapi import APIRouter, HTTPException, status

from app.core.dependencies import SessionDep
from app.core.settings.cti_profile.schemas.cti_profile_schemas import (
    CTISettingsResponse,
    CTISettingsUpdate,
    CTISettingsCreate
)
from app.core.settings.cti_profile.service.cti_profile_service import (
    get_cti_profile_settings,
    update_cti_profile_settings
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/settings/cti", tags=["CTI Profile Settings"])


@router.get(
    "",
    response_model=CTISettingsResponse,
    summary="Get CTI profile settings",
    description="Retrieve current CTI (Cyber Threat Intelligence) profile settings",
    responses={
        400: {"description": "Invalid settings data"},
        500: {"description": "Failed to retrieve settings"},
    },
)
async def get_cti_settings(db: SessionDep) -> CTISettingsResponse:
    """Retrieve CTI profile settings with automatic initialization if not found"""
    try:
        return await get_cti_profile_settings(db)
    except ValueError as e:
        logger.warning("Validation error retrieving CTI settings: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid settings data: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error retrieving CTI settings: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve CTI profile settings"
        )


@router.put(
    "",
    response_model=CTISettingsResponse,
    summary="Update CTI profile settings",
    description="Update CTI (Cyber Threat Intelligence) profile settings with validation",
    responses={
        400: {"description": "Invalid settings data"},
        500: {"description": "Failed to update settings"},
    },
)
async def update_cti_settings(
    settings_update: CTISettingsUpdate,
    db: SessionDep
) -> CTISettingsResponse:
    """Update CTI profile settings with comprehensive validation"""
    try:
        return await update_cti_profile_settings(db, settings_update)
    except ValueError as e:
        logger.warning("Validation error updating CTI settings: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid settings data: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error updating CTI settings: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update CTI profile settings"
        )


@router.post(
    "",
    response_model=CTISettingsResponse,
    summary="Create CTI profile settings",
    description="Create new CTI (Cyber Threat Intelligence) profile settings",
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"description": "Invalid settings data"},
        500: {"description": "Failed to create settings"},
    },
)
async def create_cti_settings(
    settings_create: CTISettingsCreate,
    db: SessionDep
) -> CTISettingsResponse:
    """Create new CTI profile settings"""
    try:
        settings_update = CTISettingsUpdate(settings=settings_create.settings)
        return await update_cti_profile_settings(db, settings_update)
    except ValueError as e:
        logger.warning("Validation error creating CTI settings: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid settings data: {str(e)}"
        )
    except Exception as e:
        logger.error("Unexpected error creating CTI settings: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create CTI profile settings"
        )
