import asyncio
import logging
from typing import Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey
from app.core.settings.api_keys.schemas.quota_schemas import QuotaStatus
from app.core.settings.api_keys.service.quota_clients import (
    QuotaCheckError,
    fetch_hunterio_quota,
    fetch_shodan_quota,
    fetch_virustotal_quota,
)

logger = logging.getLogger(__name__)

# (api key name in the apikeys table, quota-fetch function)
_QUOTA_PROVIDERS: list[tuple[str, Callable[[str], Awaitable[dict]]]] = [
    ("virustotal", fetch_virustotal_quota),
    ("shodan", fetch_shodan_quota),
    ("hunterio_api_key", fetch_hunterio_quota),
]


async def _check_provider_quota(db: AsyncSession, provider: str, fetch_fn: Callable[[str], Awaitable[dict]]) -> QuotaStatus:
    apikey = await get_apikey(db, provider)
    if not apikey or not apikey.is_configured():
        return QuotaStatus(provider=provider, configured=False)

    try:
        quota_data = await fetch_fn(apikey.key)
        return QuotaStatus(provider=provider, configured=True, **quota_data)
    except QuotaCheckError as e:
        logger.warning("Quota check failed for %s: %s", provider, e)
        return QuotaStatus(provider=provider, configured=True, error=str(e))
    except Exception as e:
        logger.error("Unexpected error checking quota for %s: %s", provider, e, exc_info=True)
        return QuotaStatus(provider=provider, configured=True, error="Unexpected error checking quota")


async def get_quota_status(db: AsyncSession) -> list[QuotaStatus]:
    """Check remaining quota for every provider with a supported quota endpoint.

    Each provider is checked independently so one provider's failure/rate-limit
    doesn't blank out the results for the others.
    """
    results = await asyncio.gather(*[
        _check_provider_quota(db, provider, fetch_fn) for provider, fetch_fn in _QUOTA_PROVIDERS
    ])
    return list(results)
