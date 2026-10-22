import asyncio
import logging

import httpx
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppHTTPException
from app.core.settings.api_keys.config.service_config import (
    get_all_service_definitions,
    get_service_definition,
)
from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey
from app.core.settings.api_keys.schemas.key_test_schemas import KeyTestResult, KeyTestStatus
from app.core.settings.api_keys.service.key_test_clients import KEY_TEST_EXEMPT, KEY_TESTS

logger = logging.getLogger(__name__)

_DETAILS: dict[KeyTestStatus, str] = {
    KeyTestStatus.OK: "The provider accepted the key.",
    KeyTestStatus.REJECTED: "The provider rejected the key. Check it was copied whole, hasn't "
    "been revoked or expired, and paste it again.",
    KeyTestStatus.RATE_LIMITED: "The key is rate limited or out of quota right now. Try again "
    "later.",
    KeyTestStatus.PLAN_REQUIRED: "The key works, but this API needs a paid plan.",
    KeyTestStatus.UNREACHABLE: "Couldn't reach the provider. Check the network and try again.",
    KeyTestStatus.ERROR: "The provider answered with an unexpected error.",
    KeyTestStatus.NOT_CONFIGURED: "No key is saved for this service.",
}


def key_test_exempt_reason(service_key: str) -> str | None:
    """Why `service_key` can't be tested, or None when it can (or needs no key)."""
    return KEY_TEST_EXEMPT.get(service_key)


async def _saved_keys(db: AsyncSession, key_names: list[str]) -> dict[str, str] | None:
    keys = {}
    for name in key_names:
        apikey = await get_apikey(db, name)
        if not apikey or not apikey.is_configured():
            return None
        keys[name] = apikey.key
    return keys


def _result(service_key: str, test_status: KeyTestStatus, **kwargs) -> KeyTestResult:
    return KeyTestResult(
        service=service_key, status=test_status, detail=_DETAILS[test_status], **kwargs
    )


def _require_keyed_service(service_key: str) -> list[str]:
    definition = get_service_definition(service_key)
    if definition is None or not definition.required_keys:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No keyed service with that name",
            error_code="SERVICE_NOT_FOUND",
        )
    return definition.required_keys


async def _run_check(service_key: str, keys: dict[str, str]) -> KeyTestResult:
    """Network part only, so several can run at once without sharing the DB session."""
    try:
        outcome = await KEY_TESTS[service_key](keys)
    # Exception type only, never its text or traceback: those can carry the request URL, some
    # keys travel in it, and the redaction filter only sees the message, not a traceback.
    except httpx.HTTPError as e:
        logger.warning(
            "Key test for %s could not reach the provider: %s", service_key, type(e).__name__
        )
        return _result(service_key, KeyTestStatus.UNREACHABLE)
    except Exception as e:
        logger.error("Unexpected error testing the key for %s: %s", service_key, type(e).__name__)
        return _result(service_key, KeyTestStatus.ERROR)
    return _result(
        service_key, outcome.status, http_status=outcome.http_status, quota=outcome.quota
    )


async def run_key_test(db: AsyncSession, service_key: str) -> KeyTestResult:
    """Live check of the saved key(s) of one service. Never raises for a provider failure."""
    key_names = _require_keyed_service(service_key)
    if service_key in KEY_TEST_EXEMPT:
        return KeyTestResult(
            service=service_key,
            status=KeyTestStatus.UNTESTABLE,
            detail=KEY_TEST_EXEMPT[service_key],
        )
    keys = await _saved_keys(db, key_names)
    if keys is None:
        return _result(service_key, KeyTestStatus.NOT_CONFIGURED)
    return await _run_check(service_key, keys)


async def run_all_key_tests(db: AsyncSession) -> list[KeyTestResult]:
    """Tests every testable service whose keys are all saved; skips the rest."""
    pending = []
    for service_key, definition in get_all_service_definitions().items():
        if service_key not in KEY_TESTS:
            continue
        keys = await _saved_keys(db, definition.required_keys)
        if keys is not None:
            pending.append(_run_check(service_key, keys))
    return list(await asyncio.gather(*pending))
