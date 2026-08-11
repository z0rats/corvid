"""Social-analyzer settings API routes - timeout, top-sites count"""

from app.core.settings.username_search.crud.social_analyzer_settings_crud import (
    get_social_analyzer_config as crud_get_config,
    update_social_analyzer_config as crud_update_config,
)
from app.core.settings.username_search.schemas.social_analyzer_settings_schemas import (
    SocialAnalyzerConfigSchema,
    SocialAnalyzerConfigUpdateSchema,
)
from app.core.settings.settings_router_factory import build_singleton_settings_router

router = build_singleton_settings_router(
    prefix="/api/settings/social-analyzer",
    tags=["Username Search Settings"],
    response_schema=SocialAnalyzerConfigSchema,
    update_schema=SocialAnalyzerConfigUpdateSchema,
    get_service=crud_get_config,
    update_service=crud_update_config,
    exclude_none=True,
)
