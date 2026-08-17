import asyncio
import logging
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey, get_apikeys
from app.features.ioc_tools.ioc_lookup.config.rate_limiting_config import (
    get_retry_config,
    get_service_rate_limit,
)
from app.features.ioc_tools.ioc_lookup.schemas.lookup_schemas import (
    LookupResult,
    LookupStatus,
    ServiceInfo,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service import (
    external_api_clients as service_functions,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError,
    ServiceError,
    ServiceRateLimitError,
    ServiceUnavailableError,
)

from .provider_spec import ProviderSpec, build_call_args
from .service_registry import get_all_services, get_service, register_services

logger = logging.getLogger(__name__)

_registry_lock: asyncio.Lock | None = None
_registry_initialized = False

# Per-service request pacing, shared by every caller (single lookup, bulk lookup) since this
# is module-level state keyed by service name rather than per-request.
_rate_limiters: dict[str, dict[str, Any]] = defaultdict(
    lambda: {"last_request": 0.0, "request_count": 0}
)


async def apply_rate_limit(service_name: str) -> None:
    """Sleep as needed so calls to a given service stay within its configured requests/sec."""
    rate_limit = get_service_rate_limit(service_name)
    min_interval = 1.0 / rate_limit

    limiter = _rate_limiters[service_name]
    time_since_last = time.time() - limiter["last_request"]

    if time_since_last < min_interval:
        sleep_time = min_interval - time_since_last
        logger.debug("Rate limiting %s: sleeping for %ss", service_name, sleep_time)
        await asyncio.sleep(sleep_time)

    limiter["last_request"] = time.time()
    limiter["request_count"] += 1


async def _sleep_before_retry(delay: float) -> None:
    await asyncio.sleep(delay)


async def _call_service_with_retry(
    service_config: ProviderSpec,
    func_args: dict[str, Any],
    service_name: str,
) -> Any:
    """Call a service's lookup function, retrying on rate-limit responses with exponential
    backoff instead of surfacing RATE_LIMITED to the caller on the first 429."""
    retry_config = get_retry_config()
    max_retries = retry_config["max_retries"]
    delay = retry_config["base_delay"]

    attempt = 0
    while True:
        await apply_rate_limit(service_name)
        try:
            return await service_config.func(**func_args)
        except ServiceRateLimitError:
            if attempt >= max_retries:
                raise
            logger.warning(
                "Rate limited by %s, retrying in %.1fs (attempt %s/%s)",
                service_name,
                delay,
                attempt + 1,
                max_retries,
            )
            await _sleep_before_retry(delay)
            delay = min(delay * retry_config["backoff_factor"], retry_config["max_delay"])
            attempt += 1


def get_rate_limiter_stats() -> dict[str, dict[str, Any]]:
    """Get statistics about rate limiter usage"""
    return {
        name: {
            "request_count": limiter["request_count"],
            "last_request": limiter["last_request"],
            "rate_limit": get_service_rate_limit(name),
        }
        for name, limiter in _rate_limiters.items()
    }


def reset_rate_limiters() -> None:
    """Reset all rate limiters (useful for testing)"""
    _rate_limiters.clear()
    logger.info("Rate limiters reset")


def _get_registry_lock() -> asyncio.Lock:
    """Return the registry lock, creating it on first call within the running event loop."""
    global _registry_lock
    if _registry_lock is None:
        _registry_lock = asyncio.Lock()
    return _registry_lock


async def _ensure_registry_initialized() -> None:
    """Populate the service registry on first use (async-safe, idempotent)."""
    global _registry_initialized
    if _registry_initialized:
        return

    async with _get_registry_lock():
        if _registry_initialized:
            return
        logger.info("Initializing service registry")
        register_services(service_functions)
        _registry_initialized = True
        logger.info("Registered %s services", len(get_all_services()))


async def _get_api_keys(service_config: ProviderSpec, db: AsyncSession) -> dict[str, str] | None:
    """Retrieve required API keys for a service."""
    key_names = service_config.required_key_names
    if not key_names:
        return {}

    key_results = await asyncio.gather(*[get_apikey(name=name, db=db) for name in key_names])

    keys = {}
    for key_name, key_data in zip(key_names, key_results, strict=False):
        if not key_data or not key_data.is_active:
            logger.warning("Missing or inactive API key: %s", key_name)
            return None
        keys[key_name] = key_data.key
    return keys


def _make_error_result(
    ioc: str, service_name: str, lookup_status: LookupStatus, message: str
) -> LookupResult:
    """Build a failed LookupResult for a given error status and message."""
    return LookupResult(
        ioc=ioc,
        service=service_name,
        status=lookup_status,
        error=message,
        timestamp=datetime.now(UTC),
    )


async def lookup_ioc(
    service_name: str, ioc: str, ioc_type: str, db: AsyncSession
) -> LookupResult | None:
    """Perform a unified IOC lookup by dispatching to the appropriate async service function."""
    await _ensure_registry_initialized()
    logger.info("Starting IOC lookup for service=%s, ioc_type=%s", service_name, ioc_type)

    service_config = get_service(service_name)
    if not service_config:
        logger.warning("Service not found: %s", service_name)
        return None

    if ioc_type not in service_config.supported_ioc_types:
        logger.warning("Unsupported IOC type %s for service %s", ioc_type, service_name)
        return _make_error_result(
            ioc,
            service_name,
            LookupStatus.ERROR,
            f"Service '{service_name}' does not support IOC type '{ioc_type}'.",
        )

    api_keys = await _get_api_keys(service_config, db)
    if api_keys is None and service_config.required_key_names:
        logger.error("Missing API keys for service: %s", service_name)
        return _make_error_result(
            ioc,
            service_name,
            LookupStatus.UNAUTHORIZED,
            f"Required API key(s) for '{service_name}' are missing or inactive.",
        )

    extra_args = {"db": db} if service_config.requires_db else None
    func_args = build_call_args(service_config, ioc, ioc_type, api_keys or {}, extra_args)

    logger.debug("Calling %s lookup function with args: %s", service_name, list(func_args.keys()))
    try:
        raw_result = await _call_service_with_retry(service_config, func_args, service_name)
    except ServiceRateLimitError as e:
        logger.warning("Rate limit for %s: %s", service_name, e.message)
        return _make_error_result(ioc, service_name, LookupStatus.RATE_LIMITED, e.message)
    except ServiceAuthError as e:
        logger.warning("Auth error for %s: %s", service_name, e.message)
        return _make_error_result(ioc, service_name, LookupStatus.UNAUTHORIZED, e.message)
    except ServiceUnavailableError as e:
        logger.error("Service unavailable for %s: %s", service_name, e.message)
        return _make_error_result(ioc, service_name, LookupStatus.SERVICE_UNAVAILABLE, e.message)
    except ServiceError as e:
        logger.error("Service error for %s: %s", service_name, e.message)
        return _make_error_result(ioc, service_name, LookupStatus.ERROR, e.message)
    except httpx.TimeoutException:
        logger.warning("Timeout connecting to %s", service_name)
        return _make_error_result(
            ioc, service_name, LookupStatus.SERVICE_UNAVAILABLE, f"{service_name} request timed out"
        )
    except httpx.RequestError as e:
        logger.error("Connection error for %s: %s", service_name, str(e))
        return _make_error_result(
            ioc,
            service_name,
            LookupStatus.SERVICE_UNAVAILABLE,
            f"Could not connect to {service_name}",
        )

    logger.info("Successfully completed lookup for %s", service_name)
    return LookupResult(
        ioc=ioc,
        service=service_name,
        status=LookupStatus.SUCCESS,
        data=raw_result,
        timestamp=datetime.now(UTC),
    )


async def get_all_service_configs(db: AsyncSession) -> list[ServiceInfo]:
    """Get configuration for all services with their availability and bulk-lookup status."""
    await _ensure_registry_initialized()
    logger.debug("Retrieving all service configurations")

    all_apikeys = await get_apikeys(db)
    active_key_map = {key.name: key for key in all_apikeys if key.name and key.is_active}

    services_with_status = []
    for service_key, config in get_all_services().items():
        required_keys = config.required_key_names

        if not required_keys:
            is_configured = True
            is_bulk_enabled = config.bulk_enabled
        else:
            active_for_service = [active_key_map[k] for k in required_keys if k in active_key_map]
            is_configured = len(active_for_service) == len(required_keys)
            is_bulk_enabled = (
                config.bulk_enabled
                and bool(active_for_service)
                and all(k.bulk_ioc_lookup for k in active_for_service)
            )

        services_with_status.append(
            ServiceInfo(
                key=service_key,
                name=config.name,
                supported_ioc_types=config.supported_ioc_types,
                is_configured=is_configured,
                is_bulk_enabled=is_bulk_enabled,
            )
        )

    logger.debug("Retrieved %s service configurations", len(services_with_status))
    return services_with_status


async def build_service_definitions(db: AsyncSession) -> dict[str, dict[str, Any]]:
    """Build service definitions map with availability status from configured API keys."""
    await _ensure_registry_initialized()

    all_apikeys = await get_apikeys(db)
    api_key_map = {key.name: key.key for key in all_apikeys if key.name and key.key}

    return {
        service_name: {
            "name": config.name,
            "requiredKeys": config.required_key_names,
            "supportedIocTypes": config.supported_ioc_types,
            "isAvailable": all(
                key in api_key_map and api_key_map[key].strip() for key in config.required_key_names
            )
            if config.required_key_names
            else True,
            "icon": f"{service_name}_logo_small",
        }
        for service_name, config in get_all_services().items()
    }
