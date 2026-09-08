"""The three inbound Telegram bot commands (`/help`, `/digest`, `/lookup`). Each handler
returns the reply text; sending it back to the chat is the caller's (`command_dispatcher`)
job. See docs/adr/0012-telegram-bot-polling.md.
"""

import asyncio
from urllib.parse import quote

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.alerts.crud.alerts_crud import get_unread_alerts
from app.features.ioc_tools.ioc_lookup.bulk_lookup.service.bulk_ioc_lookup_service import (
    run_single_lookup_with_rate_limit,
)
from app.features.ioc_tools.ioc_lookup.config.rate_limiting_config import get_concurrency_limit
from app.features.ioc_tools.ioc_lookup.schemas.lookup_schemas import LookupStatus
from app.features.ioc_tools.ioc_lookup.single_lookup.service.ioc_lookup_engine import (
    get_all_service_configs,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import (
    IOC_TYPES,
    determine_ioc_type,
)

_DIGEST_LIMIT = 10

_STATUS_ICONS = {
    LookupStatus.SUCCESS.value: "✅",  # checkmark
    LookupStatus.RATE_LIMITED.value: "⚠️",  # warning
    LookupStatus.UNAUTHORIZED.value: "⚠️",
    LookupStatus.SERVICE_UNAVAILABLE.value: "⚠️",
}
_DEFAULT_STATUS_ICON = "❌"  # cross mark


def handle_help() -> str:
    """Static help text listing the supported commands."""
    return (
        "Corvid bot commands:\n"
        "/lookup <value> - quick IOC lookup across configured services\n"
        "/digest - recent unread alerts\n"
        "/help - show this message"
    )


async def handle_digest(db: AsyncSession) -> str:
    """Format the most recent unread alerts as one line each."""
    alerts = await get_unread_alerts(db, limit=_DIGEST_LIMIT)
    if not alerts:
        return "No unread alerts."

    lines = ["\U0001f514 Unread alerts:"]
    lines.extend(f"[{alert.module}] {alert.title}" for alert in alerts)
    return "\n".join(lines)


async def handle_lookup(db: AsyncSession, value: str, web_base_url: str) -> str:
    """Run `value` through every configured service supporting its detected IOC type and
    return a condensed pass/fail line per service - not a merged verdict, since
    `LookupResult.data` is an opaque, provider-specific dict with no common
    malicious/score field across providers (see lookup_schemas.py)."""
    ioc_type = determine_ioc_type(value)
    if ioc_type == IOC_TYPES["UNKNOWN"]:
        return f"Could not determine an IOC type for: {value}"

    all_services = await get_all_service_configs(db)
    matching = [s for s in all_services if s.is_configured and ioc_type in s.supported_ioc_types]
    if not matching:
        return f"No configured services support IOC type {ioc_type}."

    semaphore = asyncio.Semaphore(get_concurrency_limit("max_concurrent_requests"))
    results = await asyncio.gather(
        *[
            run_single_lookup_with_rate_limit(service.key, value, ioc_type, db, semaphore)
            for service in matching
        ]
    )

    lines = [f"\U0001f50d Lookup results for {value} ({ioc_type}):"]
    for service, result in zip(matching, results, strict=True):
        status = result.get("status", LookupStatus.ERROR.value)
        icon = _STATUS_ICONS.get(status, _DEFAULT_STATUS_ICON)
        if status == LookupStatus.SUCCESS.value:
            lines.append(f"{icon} {service.name}")
        else:
            lines.append(f"{icon} {service.name}: {result.get('error', status)}")

    if web_base_url:
        lines.append(f"\n{web_base_url}/ioc-tools/lookup?q={quote(value)}")

    return "\n".join(lines)
