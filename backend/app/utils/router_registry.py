from fastapi import APIRouter, FastAPI

from app.core import healthcheck
from app.core.alerts.routes import alerts_routes
from app.core.settings.api_keys.routers import api_keys_settings_routes, service_config_routes
from app.core.settings.cti_profile.routers import cti_profile_routes
from app.core.settings.ai_settings.routers import ai_settings_routes
from app.core.settings.general.routers import general_settings_routes
from app.core.settings.keywords.routers import keywords_settings_routes
from app.core.settings.modules.routers import modules_settings_routes
from app.features.cvss_calculator.routers import cvss_routes
from app.features.ioc_tools.domain_finder.routers import domain_routes
from app.features.email_analyzer.routers import email_routes
from app.features.ioc_tools.ioc_defanger.routers import internal_defang_routes
from app.features.ioc_tools.ioc_extractor.routers import internal_ioc_extractor_routes
from app.features.ioc_tools.ioc_lookup.bulk_lookup.routers import bulk_ioc_lookup_routes
from app.features.ioc_tools.ioc_lookup.single_lookup.routers import unified_routes
from app.features.llm_templates.routers import llm_template_routes, template_category_routes
from app.features.newsfeed.routers import (
    external_newsfeed_routes,
    newsfeed_settings_routes,
    article_routes,
    feed_management_routes,
    analysis_routes,
    analytics_routes,
    trends_blacklist_routes,
)


def get_core_routers() -> list[APIRouter]:
    """Get core application routers"""
    return [
        healthcheck.router,
        alerts_routes.router,
        alerts_routes.ws_router,
    ]


def get_settings_routers() -> list[APIRouter]:
    """Get settings-related routers"""
    return [
        ai_settings_routes.router,
        api_keys_settings_routes.router,
        service_config_routes.router,
        general_settings_routes.router,
        newsfeed_settings_routes.router,
        feed_management_routes.router,
        modules_settings_routes.router,
        keywords_settings_routes.router,
        cti_profile_routes.router,
        trends_blacklist_routes.router,
    ]


def get_feature_routers() -> list[APIRouter]:
    """Get feature-related routers"""
    return [
        template_category_routes.router,
        llm_template_routes.router,
        domain_routes.router,
        email_routes.router,
        internal_ioc_extractor_routes.router,
        internal_defang_routes.router,
        cvss_routes.router,
        article_routes.router,
        analysis_routes.router,
        analytics_routes.router,
        external_newsfeed_routes.router,
        bulk_ioc_lookup_routes.router,
        unified_routes.router,
    ]


def register_all_routers(app: FastAPI) -> None:
    """Register all routers with the FastAPI application"""
    for router in [*get_core_routers(), *get_settings_routers(), *get_feature_routers()]:
        app.include_router(router)
