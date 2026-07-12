from fastapi import APIRouter, Depends, FastAPI

from app.core import healthcheck
from app.core.security.access_control import verify_access_token
from app.core.alerts.routes import alerts_routes
from app.core.settings.api_keys.routers import api_keys_settings_routes, service_config_routes
from app.core.settings.cti_profile.routers import cti_profile_routes
from app.core.settings.ai_settings.routers import ai_settings_routes
from app.core.settings.email_search.routers import email_search_settings_routes
from app.core.settings.general.routers import general_settings_routes
from app.core.settings.keywords.routers import keywords_settings_routes
from app.core.settings.modules.routers import modules_settings_routes
from app.core.settings.username_search.routers import social_analyzer_settings_routes, username_search_settings_routes
from app.features.cvss_calculator.routers import cvss_routes
from app.features.email_search.routers import email_search_routes
from app.features.ioc_tools.domain_finder.routers import domain_routes
from app.features.email_analyzer.routers import email_routes
from app.features.image_tools.routers import image_routes
from app.features.ioc_tools.ioc_defanger.routers import internal_defang_routes
from app.features.ioc_tools.ioc_extractor.routers import internal_ioc_extractor_routes
from app.features.ioc_tools.ioc_lookup.bulk_lookup.routers import bulk_ioc_lookup_routes
from app.features.ioc_tools.ioc_lookup.single_lookup.routers import lookup_history_routes, unified_routes
from app.features.llm_templates.routers import llm_template_routes, template_category_routes
from app.features.reddit_search.routers import reddit_search_routes
from app.features.username_search.routers import username_search_routes
from app.features.newsfeed.routers import (
    external_newsfeed_routes,
    newsfeed_settings_routes,
    article_routes,
    feed_management_routes,
    analysis_routes,
    analytics_routes,
    trends_blacklist_routes,
)


def get_public_routers() -> list[APIRouter]:
    """Routers that stay reachable without the access token.

    - healthcheck: no sensitive data, useful for uptime monitors/orchestrators.
    - alerts_routes.ws_router: browsers can't attach a custom Authorization
      header to a WebSocket handshake, so it checks the same access token
      itself via a query param instead (see access_control.py, alerts_routes.py).
    """
    return [
        healthcheck.router,
        alerts_routes.ws_router,
    ]


def get_core_routers() -> list[APIRouter]:
    """Get core application routers"""
    return [
        alerts_routes.router,
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
        username_search_settings_routes.router,
        social_analyzer_settings_routes.router,
        email_search_settings_routes.router,
    ]


def get_feature_routers() -> list[APIRouter]:
    """Get feature-related routers"""
    return [
        template_category_routes.router,
        llm_template_routes.router,
        domain_routes.router,
        email_routes.router,
        image_routes.router,
        internal_ioc_extractor_routes.router,
        internal_defang_routes.router,
        cvss_routes.router,
        article_routes.router,
        analysis_routes.router,
        analytics_routes.router,
        external_newsfeed_routes.router,
        bulk_ioc_lookup_routes.router,
        unified_routes.router,
        lookup_history_routes.router,
        username_search_routes.router,
        email_search_routes.router,
        reddit_search_routes.router,
    ]


def register_all_routers(app: FastAPI) -> None:
    """Register all routers with the FastAPI application"""
    for router in get_public_routers():
        app.include_router(router)

    for router in [*get_core_routers(), *get_settings_routers(), *get_feature_routers()]:
        app.include_router(router, dependencies=[Depends(verify_access_token)])
