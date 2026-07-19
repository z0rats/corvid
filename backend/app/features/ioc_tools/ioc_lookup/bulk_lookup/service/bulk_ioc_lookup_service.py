import asyncio
import logging
from typing import Any, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
import time
from app.features.ioc_tools.ioc_lookup.single_lookup.service.ioc_lookup_engine import (
    lookup_ioc, get_all_service_configs,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import get_service
from app.features.ioc_tools.ioc_lookup.schemas.lookup_schemas import LookupStatus
from app.features.ioc_tools.ioc_lookup.config.rate_limiting_config import (
    get_service_rate_limit,
    get_concurrency_limit,
    get_timeout_config
)

logger = logging.getLogger(__name__)


async def run_single_lookup_with_rate_limit(
    service_name: str,
    ioc: str,
    ioc_type: str,
    db: AsyncSession,
    semaphore: asyncio.Semaphore
) -> dict[str, Any]:
    """Execute a single IOC lookup with rate limiting and concurrency control.

    Always returns a dict with a "status" key set to a `LookupStatus` value, so
    callers can distinguish "no key" / "rate limited" / "real error" / "success"
    without parsing message text.
    """
    async with semaphore:
        try:
            service_config = get_service(service_name)
            if not service_config:
                logger.warning("Service not configured: %s", service_name)
                return {"status": LookupStatus.ERROR.value, "error": f"Service '{service_name}' not configured"}

            if ioc_type not in service_config.get('supported_ioc_types', []):
                logger.debug("Service %s doesn't support IOC type %s", service_name, ioc_type)
                return {"status": LookupStatus.ERROR.value, "error": f"Service '{service_name}' doesn't support {ioc_type}"}

            # lookup_ioc() applies per-service pacing/backoff itself (shared with single lookup).
            result = await lookup_ioc(service_name, ioc, ioc_type, db)

            logger.debug("Completed lookup for %s: %s", service_name, ioc)
            if result.status != LookupStatus.SUCCESS:
                return {"status": result.status.value, "error": result.error}
            return {"status": LookupStatus.SUCCESS.value, "data": result.data}

        except Exception as e:
            logger.error("Exception in %s lookup for %s: %s", service_name, ioc, str(e), exc_info=True)
            return {"status": LookupStatus.ERROR.value, "error": str(e)}


async def process_bulk_lookups_with_rate_limiting(
    iocs: list[str],
    services: list[str],
    db: AsyncSession,
    max_concurrent_requests: int | None = None
) -> AsyncGenerator[dict[str, Any], None]:
    """Process bulk IOC lookups with rate limiting and yield results as they complete"""
    if max_concurrent_requests is None:
        max_concurrent_requests = get_concurrency_limit('max_concurrent_requests')

    logger.info("Starting rate-limited bulk lookup for %s IOCs across %s services", len(iocs), len(services))
    logger.info("Max concurrent requests: %s", max_concurrent_requests)

    from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import determine_ioc_type

    all_service_configs = await get_all_service_configs(db)

    enabled_and_requested_services = {
        s.key for s in all_service_configs
        if s.key in services and s.is_configured and s.is_bulk_enabled
    }

    services_to_query = list(enabled_and_requested_services)

    if not services_to_query:
        logger.warning("No services available for bulk lookup")
        yield {
            "status": LookupStatus.ERROR.value,
            "error": "No selected services are available or enabled for bulk lookup.",
            "service": "system",
            "available_services": [s.key for s in all_service_configs if s.is_configured]
        }
        return

    logger.info("Using services: %s", services_to_query)
    logger.info("Rate limits: %s", [(s, get_service_rate_limit(s)) for s in services_to_query])

    semaphore = asyncio.Semaphore(max_concurrent_requests)

    tasks = []
    for ioc_value in iocs:
        ioc_type = determine_ioc_type(ioc_value)
        if ioc_type == "unknown":
            logger.warning("Unknown IOC type for: %s", ioc_value)
            yield {
                "ioc": ioc_value,
                "service": "system",
                "status": LookupStatus.ERROR.value,
                "error": "Unknown IOC type"
            }
            continue

        for service_name in services_to_query:
            service_config = get_service(service_name)
            if not service_config or ioc_type not in service_config.get('supported_ioc_types', []):
                logger.debug("Skipping %s for %s - doesn't support %s", service_name, ioc_value, ioc_type)
                continue

            coro = run_single_lookup_with_rate_limit(
                service_name, ioc_value, ioc_type, db, semaphore
            )
            task = asyncio.create_task(coro)
            tasks.append((ioc_value, service_name, task))

    logger.info("Created %s rate-limited lookup tasks", len(tasks))

    total_timeout = get_timeout_config()['total_timeout']
    start_time = time.monotonic()

    for index, (ioc_value, service_name, task) in enumerate(tasks):
        remaining = total_timeout - (time.monotonic() - start_time)
        if remaining <= 0:
            logger.warning(
                "Bulk lookup exceeded total timeout of %ss; cancelling %s remaining task(s)",
                total_timeout, len(tasks) - index
            )
            for _, _, pending_task in tasks[index:]:
                pending_task.cancel()
            for pending_ioc, pending_service, _ in tasks[index:]:
                yield {
                    "ioc": pending_ioc,
                    "service": pending_service,
                    "status": LookupStatus.ERROR.value,
                    "error": "Bulk lookup exceeded the total timeout"
                }
            break

        try:
            result = await asyncio.wait_for(task, timeout=remaining)
            status_value = result.get("status", LookupStatus.ERROR.value)
            if status_value == LookupStatus.SUCCESS.value:
                yield {
                    "ioc": ioc_value,
                    "service": service_name,
                    "status": status_value,
                    "data": result.get("data")
                }
            else:
                yield {
                    "ioc": ioc_value,
                    "service": service_name,
                    "status": status_value,
                    "error": result.get("error", "Service error")
                }
        except asyncio.TimeoutError:
            task.cancel()
            logger.warning("Bulk lookup total timeout reached while awaiting %s/%s", ioc_value, service_name)
            yield {
                "ioc": ioc_value,
                "service": service_name,
                "status": LookupStatus.ERROR.value,
                "error": "Bulk lookup exceeded the total timeout"
            }
        except Exception as e:
            logger.error("Error awaiting task for %s/%s: %s", ioc_value, service_name, str(e))
            yield {
                "ioc": ioc_value,
                "service": service_name,
                "status": LookupStatus.ERROR.value,
                "error": str(e)
            }

    logger.info("Completed rate-limited bulk lookup processing")
