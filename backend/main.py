import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.body_limit_config import RequestBodyLimitMiddleware
from app.core.config.fastapi_config import get_fastapi_config, get_cors_config
from app.core.config.logging_config import setup_logging
from app.core.config.rate_limit_config import limiter
from app.core.config.request_id_config import RequestIdMiddleware
from app.core.config.security_config import SecurityHeadersMiddleware
from app.core.config.settings import settings
from app.core.config.validation import ensure_required_directories, log_validation_results
from app.core.database import Base, engine, managed_session, dispose_database_engine
from app.core.exceptions import register_exception_handlers
from app.core.scheduler import initialize_scheduler, stop_scheduler
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import close_client
from app.utils.startup_service import initialize_application_defaults
from app.utils.router_registry import register_all_routers

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure application logging with environment settings"""
    setup_logging(
        log_level=settings.logging.level,
        log_dir=settings.logging.dir,
        app_name=settings.logging.app_name,
        enable_console=settings.logging.enable_console,
        enable_file=settings.logging.enable_file
    )


async def _run_application_defaults() -> None:
    """Initialize application defaults in a managed session"""
    async with managed_session() as db:
        await initialize_application_defaults(db)


async def _create_database_tables() -> None:
    """Create all database tables if they don't exist"""
    import app.core.settings.general.models.general_settings_models
    import app.core.settings.modules.models.modules_settings_models 
    import app.core.settings.api_keys.models.api_keys_settings_models   
    import app.core.settings.keywords.models.keywords_settings_models   
    import app.core.settings.ai_settings.models.ai_settings_models
    import app.core.settings.cti_profile.models.cti_profile_models
    import app.core.alerts.models.alerts_models   
    import app.features.newsfeed.models.newsfeed_models   
    import app.features.llm_templates.models.llm_template_models   
    import app.features.llm_templates.models.template_category_models   

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def _fetch_favicons_in_background() -> None:
    """Fetch missing feed favicons in the background after startup"""
    from app.features.newsfeed.service.icon_management_service import bulk_fetch_favicons_parallel

    try:
        async with managed_session() as db:
            await bulk_fetch_favicons_parallel(db)
    except Exception as e:
        logger.error("Background favicon fetch failed: %s", e)


async def handle_application_startup() -> None:
    """Handle application startup tasks"""
    logger.info("Application starting up...")
    try:
        await _create_database_tables()
        await _run_application_defaults()
        asyncio.create_task(_fetch_favicons_in_background())
        await initialize_scheduler()
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error("Startup failed: %s", e)
        raise


async def handle_application_shutdown() -> None:
    """Handle application shutdown tasks"""
    logger.info("Application shutting down...")
    try:
        stop_scheduler()
        await close_client()
        await dispose_database_engine()
        logger.info("Application shutdown completed successfully")
    except Exception as e:
        logger.error("Shutdown error: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events"""
    app.state.startup_time = time.time()
    await handle_application_startup()
    yield
    await handle_application_shutdown()


def create_fastapi_application() -> FastAPI:
    """Create and configure FastAPI application instance"""
    config = get_fastapi_config()
    app = FastAPI(lifespan=lifespan, **config)

    cors_config = get_cors_config()
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.api.trusted_hosts)
    app.add_middleware(CORSMiddleware, **cors_config)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RequestBodyLimitMiddleware)
    app.add_middleware(RequestIdMiddleware)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    register_exception_handlers(app)
    register_all_routers(app)

    return app


def initialize_application() -> FastAPI:
    """Initialize the complete application"""
    ensure_required_directories()
    configure_logging()
    log_validation_results()
    return create_fastapi_application()


app = initialize_application()
