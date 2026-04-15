import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.config.service_config import get_all_service_definitions
from app.core.settings.api_keys.models.api_keys_settings_models import Apikey


async def add_default_api_keys(db: AsyncSession) -> None:
    """Add default API key entries for all services if they don't exist."""
    services = get_all_service_definitions()
    created_count = 0

    try:
        existing_names = await _get_existing_key_names(db)
        keys_to_create = _collect_missing_keys(services, existing_names)

        for name, is_active in keys_to_create:
            _create_api_key_entry(db, name, "", is_active, False)
            created_count += 1

        if created_count > 0:
            await db.flush()
        logging.info("Default API keys checked/created: %d new entries", created_count)

    except SQLAlchemyError as e:
        logging.error("Failed to add default API keys: %s", e)
        await db.rollback()
        raise


async def get_service_status_summary(db: AsyncSession) -> dict[str, Any]:
    """Get a comprehensive summary of service configuration status."""
    try:
        services = get_all_service_definitions()
        result = await db.execute(select(Apikey))
        existing_keys = result.scalars().all()
        key_status = _build_key_status_map(existing_keys)

        summary = _initialize_summary(services)

        for service_key, service_config in services.items():
            service_status = _calculate_service_status(service_config, key_status)
            _update_summary_counters(summary, service_status)
            summary["services"][service_key] = service_status

        logging.debug("Generated service status summary for %d services", len(services))
        return summary

    except SQLAlchemyError as e:
        logging.error("Failed to get service status summary: %s", str(e))
        raise
    except Exception as e:
        logging.error("Unexpected error getting service status summary: %s", str(e))
        raise


async def get_api_key_statistics(db: AsyncSession) -> dict[str, int]:
    """Get basic statistics about API key configuration."""
    try:
        result = await db.execute(select(Apikey))
        all_keys = result.scalars().all()

        stats = {
            "total_keys": len(all_keys),
            "configured_keys": sum(1 for key in all_keys if key.is_configured()),
            "active_keys": sum(1 for key in all_keys if key.is_active),
            "bulk_enabled_keys": sum(1 for key in all_keys if key.bulk_ioc_lookup),
            "usable_keys": sum(1 for key in all_keys if key.is_usable()),
        }

        logging.debug("Generated API key statistics: %s", stats)
        return stats

    except SQLAlchemyError as e:
        logging.error("Failed to get API key statistics: %s", str(e))
        raise


def _collect_missing_keys(
    services: dict[str, Any],
    existing_names: set[str],
) -> list[tuple[str, bool]]:
    """Determine which API key entries need to be created.

    Returns a list of (name, is_active) tuples for keys not yet in the DB.
    Tracks seen names to avoid duplicates within the same batch.
    """
    seen: set[str] = set(existing_names)
    missing: list[tuple[str, bool]] = []

    for service_key, service_config in services.items():
        if service_config.required_keys:
            for required_key in service_config.required_keys:
                normalized = required_key.strip().lower()
                if normalized not in seen:
                    missing.append((required_key, False))
                    seen.add(normalized)
        else:
            normalized = service_key.strip().lower()
            if normalized not in seen:
                missing.append((service_key, True))
                seen.add(normalized)

    return missing


async def _get_existing_key_names(db: AsyncSession) -> set[str]:
    """Get all existing API key names from the database (already lowercased by the model)."""
    result = await db.execute(select(Apikey.name))
    return {row[0] for row in result.all()}


def _create_api_key_entry(
    db: AsyncSession,
    name: str,
    key: str,
    is_active: bool,
    bulk_ioc_lookup: bool,
) -> None:
    """Add a new API key entry to the session."""
    db.add(Apikey(
        name=name,
        key=key,
        is_active=is_active,
        bulk_ioc_lookup=bulk_ioc_lookup,
    ))


def _build_key_status_map(existing_keys: list[Apikey]) -> dict[str, dict[str, bool]]:
    """Build a mapping of key names to their status."""
    return {
        key.name: {
            "configured": key.is_configured(),
            "active": key.is_active,
        }
        for key in existing_keys
    }


def _initialize_summary(services: dict[str, Any]) -> dict[str, Any]:
    """Initialize the service status summary structure."""
    return {
        "total_services": len(services),
        "services_with_keys": 0,
        "fully_configured_services": 0,
        "active_services": 0,
        "services": {},
    }


def _calculate_service_status(service_config: Any, key_status: dict[str, dict[str, bool]]) -> dict[str, Any]:
    """Calculate status for a single service."""
    service_status = {
        "name": service_config.name,
        "required_keys": service_config.required_keys,
        "keys_configured": 0,
        "keys_active": 0,
        "fully_configured": False,
        "fully_active": False,
    }

    if not service_config.required_keys:
        service_status["fully_configured"] = True
        service_status["fully_active"] = True
        return service_status

    for required_key in service_config.required_keys:
        if required_key in key_status:
            if key_status[required_key]["configured"]:
                service_status["keys_configured"] += 1
            if key_status[required_key]["active"]:
                service_status["keys_active"] += 1

    total_required = len(service_config.required_keys)
    service_status["fully_configured"] = service_status["keys_configured"] == total_required
    service_status["fully_active"] = service_status["keys_active"] == total_required
    return service_status


def _update_summary_counters(summary: dict[str, Any], service_status: dict[str, Any]) -> None:
    """Update the summary counters based on service status."""
    if service_status["keys_configured"] > 0 or not service_status["required_keys"]:
        summary["services_with_keys"] += 1

    if service_status["fully_configured"]:
        summary["fully_configured_services"] += 1

    if service_status["fully_active"]:
        summary["active_services"] += 1
