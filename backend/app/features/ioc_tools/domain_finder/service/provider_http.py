"""One way for a domain_finder panel to call its third-party provider and fail consistently.

Every provider failure maps onto the same `AppHTTPException`s, `error_code`s prefixed with the
provider's `code`:

- `<CODE>_TIMEOUT` (504) / `<CODE>_CONNECTION_ERROR` (503) - the provider didn't answer
- `<CODE>_API_ERROR` (the provider's own status) - it answered with an HTTP error
- `<CODE>_INVALID_RESPONSE` (502) - its body didn't parse (`parse` raised `ValueError`,
  e.g. an HTML error page where JSON was expected)
- `<CODE>_UNEXPECTED_ERROR` (500) - anything else
- an `AppHTTPException` raised by `check`/`parse` itself (rate limit, bad key, not found)
  passes through unchanged

`provider_get` only ever requests `provider.base_url + path` - a fixed, hardcoded host - which
is why this module may construct a raw httpx client without `ssrf_guard.safe_get` (see
`tests/core/test_ssrf_guard_coverage.py`). A provider reached through a user-influenced
redirect (RDAP) builds its own `safe_get` request and wraps it in `provider_errors` instead.
"""

import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

import httpx

from app.core.exceptions import AppHTTPException

logger = logging.getLogger(__name__)

USER_AGENT = "Corvid-Domain-Lookup/1.0"


@dataclass(frozen=True)
class Provider:
    name: str
    code: str
    base_url: str
    timeout: float = 20.0
    accept: str | None = "application/json"

    def error(self, status_code: int, suffix: str, detail: str) -> AppHTTPException:
        return AppHTTPException(
            status_code=status_code, detail=detail, error_code=f"{self.code}_{suffix}"
        )


@asynccontextmanager
async def provider_errors(provider: Provider, subject: str) -> AsyncIterator[None]:
    """Map any failure inside the block onto `provider`'s error codes (see module docstring)."""
    try:
        yield
    except AppHTTPException:
        raise
    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching %s data for %s: %s", provider.name, subject, e)
        raise provider.error(
            504, "TIMEOUT", f"Request timeout while connecting to {provider.name}"
        ) from e
    except httpx.RequestError as e:
        logger.error("Request error while fetching %s data for %s: %s", provider.name, subject, e)
        raise provider.error(
            503, "CONNECTION_ERROR", f"Failed to connect to {provider.name}: {e}"
        ) from e
    except httpx.HTTPStatusError as e:
        status = e.response.status_code
        logger.error("HTTP status error from %s for %s: Status %s", provider.name, subject, status)
        raise provider.error(
            status, "API_ERROR", f"{provider.name} returned error: {status}"
        ) from e
    except ValueError as e:
        logger.error("Could not parse %s response for %s: %s", provider.name, subject, e)
        raise provider.error(
            502, "INVALID_RESPONSE", f"{provider.name} returned an unexpected response"
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error while fetching %s data for %s: %s",
            provider.name,
            subject,
            e,
            exc_info=True,
        )
        raise provider.error(
            500,
            "UNEXPECTED_ERROR",
            f"An unexpected error occurred while fetching {provider.name} data",
        ) from e


async def provider_get[T](
    provider: Provider,
    path: str = "",
    *,
    subject: str,
    parse: Callable[[httpx.Response], T],
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    check: Callable[[httpx.Response], None] | None = None,
) -> T:
    """GET `provider.base_url + path` and return `parse(response)`. `check(response)` runs
    before the generic status check, for provider-specific statuses worth their own error
    (a rejected key, a rate limit). `subject` (the domain) only appears in logs."""
    request_headers = {"User-Agent": USER_AGENT}
    if provider.accept:
        request_headers["Accept"] = provider.accept
    request_headers.update(headers or {})

    async with provider_errors(provider, subject):
        async with httpx.AsyncClient(timeout=provider.timeout, headers=request_headers) as client:
            response = await client.get(provider.base_url + path, params=params)
            if check is not None:
                check(response)
            response.raise_for_status()
            return parse(response)
