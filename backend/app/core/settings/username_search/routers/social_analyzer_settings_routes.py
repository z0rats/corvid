"""Social-analyzer settings API routes - timeout, top-sites count"""

import logging

from fastapi import APIRouter

from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.settings.username_search.crud.social_analyzer_settings_crud import (
    get_social_analyzer_config as crud_get_config,
    update_social_analyzer_config as crud_update_config,
)
from app.core.settings.username_search.schemas.social_analyzer_settings_schemas import (
    SocialAnalyzerConfigSchema,
    SocialAnalyzerConfigUpdateSchema,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/settings/social-analyzer", tags=["Username Search Settings"])


@router.get(
    "",
    response_model=SocialAnalyzerConfigSchema,
    response_model_exclude_none=True,
    summary="Get social-analyzer config",
    description="Get social-analyzer username search source configuration",
)
async def get_social_analyzer_config(db: ReadSessionDep) -> SocialAnalyzerConfigSchema:
    """Get current social-analyzer configuration"""
    return SocialAnalyzerConfigSchema.model_validate(await crud_get_config(db))


@router.put(
    "",
    response_model=SocialAnalyzerConfigSchema,
    response_model_exclude_none=True,
    summary="Update social-analyzer config",
    description="Update social-analyzer username search source configuration",
)
async def update_social_analyzer_config(
    config_data: SocialAnalyzerConfigUpdateSchema, db: SessionDep
) -> SocialAnalyzerConfigSchema:
    """Update social-analyzer configuration"""
    updated_config = await crud_update_config(db, config_data)
    logger.info("Updated social-analyzer configuration.")
    return SocialAnalyzerConfigSchema.model_validate(updated_config)
