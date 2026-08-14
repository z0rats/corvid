import asyncio
import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config.body_limit_config import RequestBodyLimitMiddleware
from app.core.config.fastapi_config import get_cors_config, get_fastapi_config
from app.core.config.logging_config import setup_logging
from app.core.config.rate_limit_config import limiter
from app.core.config.request_id_config import RequestIdMiddleware
from app.core.config.security_config import SecurityHeadersMiddleware
from app.core.config.settings import settings
from app.core.config.validation import ensure_required_directories, log_validation_results
from app.core.database import Base, dispose_database_engine, engine, managed_session
from app.core.dependencies import get_disk_space_health
from app.core.exceptions import register_exception_handlers
from app.core.scheduler import stop_scheduler
from app.core.security.access_control import get_access_token, verify_access_token
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import close_client
from app.utils.router_registry import register_all_routers
from app.utils.scheduler_registry import initialize_all_schedulers
from app.utils.startup_service import initialize_application_defaults

logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure application logging with environment settings"""
    setup_logging(
        log_level=settings.logging.level,
        log_dir=settings.logging.dir,
        app_name=settings.logging.app_name,
        enable_console=settings.logging.enable_console,
        enable_file=settings.logging.enable_file,
    )


async def _run_application_defaults() -> None:
    """Initialize application defaults in a managed session"""
    async with managed_session() as db:
        await initialize_application_defaults(db)


async def _create_database_tables() -> None:
    """Create all database tables if they don't exist"""

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


async def _reconcile_stale_scans() -> None:
    """Mark username/email/git-recon/ru-business-check search runs still 'running' from a
    previous process as failed.

    All four scans are driven by a detached `asyncio.create_task()` (see their
    `routers/*_routes.py` `scan`/`start_scan` handlers) that outlives the SSE request but
    not the process itself, so a container stop/crash mid-scan leaves the row
    stuck at 'running' with nothing to ever move it out of that state.
    """
    from app.features.email_search.crud.email_search_crud import (
        interrupt_running_search_runs as interrupt_running_mail_runs,
    )
    from app.features.git_recon.crud.git_recon_crud import (
        interrupt_running_searches as interrupt_running_git_recon,
    )
    from app.features.ru_business_check.crud.ru_business_check_crud import (
        interrupt_running_searches as interrupt_running_ru_business_check,
    )
    from app.features.username_search.crud.username_search_crud import interrupt_running_search_runs

    async with managed_session() as db:
        maigret_count = await interrupt_running_search_runs(db)
        mail_count = await interrupt_running_mail_runs(db)
        git_recon_count = await interrupt_running_git_recon(db)
        ru_business_check_count = await interrupt_running_ru_business_check(db)
        if maigret_count or mail_count or git_recon_count or ru_business_check_count:
            logger.info(
                "Reconciled stale scan runs left 'running' by a previous process: "
                "%s username-search, %s email-search, %s git-recon, %s ru-business-check",
                maigret_count,
                mail_count,
                git_recon_count,
                ru_business_check_count,
            )


async def _populate_blacklist_if_stale_in_background() -> None:
    """On startup, catch up immediately if the address blacklist is empty or older than its
    configured refresh interval, rather than relying solely on the recurring scheduler job.

    That job's in-memory countdown resets on every process restart (no persistent job store),
    so on a host that restarts more often than the interval — common during active development,
    but also true of any production redeploy — it may never actually fire on its own and the
    data silently goes stale. This check re-derives staleness from the DB on every startup."""
    from datetime import timedelta

    from app.features.ioc_tools.ioc_lookup.single_lookup.service.blacklist_refresh_service import (
        is_blacklist_stale,
        refresh_blacklist,
    )

    try:
        max_age = timedelta(hours=settings.scheduler.blacklist_refresh_interval_hours)
        async with managed_session() as db:
            if await is_blacklist_stale(db, max_age):
                logger.info("Address blacklist is empty or stale; refreshing in the background")
                summary = await refresh_blacklist(db)
                logger.info("Blacklist catch-up refresh completed: %s", summary)
    except Exception as e:
        logger.error("Background blacklist refresh failed: %s", e)


def _check_disk_space() -> None:
    """Warn (don't block startup) if the data_dir mount is running low on free space"""
    health = get_disk_space_health(settings)
    if health.get("status") == "low":
        logger.warning(
            "Low disk space on data directory mount: %s GB free of %s GB total (%s)",
            health.get("free_gb"),
            health.get("total_gb"),
            settings.data_dir,
        )


def _register_keyless_providers() -> None:
    """Tell api_keys settings which ioc_lookup providers need no key, so its routes don't
    have to import from ioc_tools directly (settings is a lower-level module than features)."""
    from app.core.settings.api_keys.service.keyless_providers import set_keyless_provider_names
    from app.features.ioc_tools.ioc_lookup.single_lookup.service import external_api_clients
    from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import (
        get_all_services,
        register_services,
    )

    # The registry is normally populated lazily on first lookup; force it now so it's ready
    # this early in startup. register_services() is idempotent, so the later lazy call is harmless.
    register_services(external_api_clients)
    set_keyless_provider_names(
        {name for name, spec in get_all_services().items() if not spec.required_key_names}
    )


async def handle_application_startup() -> None:
    """Handle application startup tasks"""
    logger.info("Application starting up...")
    try:
        get_access_token()  # eager: prints/persists the token now, not on first request
        _check_disk_space()
        _register_keyless_providers()
        await _create_database_tables()
        await _reconcile_stale_scans()
        await _run_application_defaults()
        asyncio.create_task(_fetch_favicons_in_background())
        asyncio.create_task(_populate_blacklist_if_stale_in_background())
        await initialize_all_schedulers()
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
    add_protected_docs_routes(app)

    return app


def add_protected_docs_routes(app: FastAPI) -> None:
    """Re-add /docs, /redoc and /openapi.json behind the access-token dependency.

    fastapi_config.py disables FastAPI's own auto-registered docs routes
    unconditionally so they can't be reached without a token; these replacements
    stay off entirely in production, matching the previous behaviour.
    """
    if settings.environment == "production":
        return

    protected = [Depends(verify_access_token)]

    @app.get("/openapi.json", include_in_schema=False, dependencies=protected)
    async def get_openapi_json():
        return app.openapi()

    @app.get("/docs", include_in_schema=False, dependencies=protected)
    async def get_docs():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{app.title} - Swagger UI",
            swagger_ui_parameters=app.swagger_ui_parameters,
        )

    @app.get("/redoc", include_in_schema=False, dependencies=protected)
    async def get_redoc():
        return get_redoc_html(openapi_url="/openapi.json", title=f"{app.title} - ReDoc")


def initialize_application() -> FastAPI:
    """Initialize the complete application"""
    ensure_required_directories()
    configure_logging()
    log_validation_results()
    return create_fastapi_application()


app = initialize_application()
