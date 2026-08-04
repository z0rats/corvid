"""
DNSDumpster API client for domain reconnaissance.

DNSDumpster's official API (https://dnsdumpster.com/developer/) needs an API key
(X-API-Key header) - unlike its sibling crt.sh/RDAP panels, there's no keyless
fallback. Free tier caps a domain lookup at 50 records and rate-limits to
1 request/2s.
"""
import logging
from typing import Any

import httpx
from app.core.exceptions import AppHTTPException

logger = logging.getLogger(__name__)

DNSDUMPSTER_BASE_URL = "https://api.dnsdumpster.com"
DNSDUMPSTER_TIMEOUT = 20.0
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Corvid-Domain-Lookup/1.0",
    "Accept": "application/json",
}


async def fetch_dnsdumpster_data(domain: str, api_key: str) -> dict[str, Any]:
    """
    Fetch domain reconnaissance data from the DNSDumpster API.

    Args:
        domain: Domain name to search for
        api_key: DNSDumpster API key (X-API-Key header)

    Returns:
        Raw DNSDumpster domain-lookup response as a dict

    Raises:
        AppHTTPException: For request failures, an invalid key, or a rate-limit hit
    """
    url = f"{DNSDUMPSTER_BASE_URL}/domain/{domain}"
    headers = {**DEFAULT_HEADERS, "X-API-Key": api_key}
    logger.debug("Fetching DNSDumpster data for domain: %s", domain)

    try:
        async with httpx.AsyncClient(timeout=DNSDUMPSTER_TIMEOUT, headers=headers) as client:
            response = await client.get(url)

            if response.status_code in (401, 403):
                logger.warning("DNSDumpster rejected the configured API key (status %s)", response.status_code)
                raise AppHTTPException(
                    status_code=401,
                    detail="DNSDumpster rejected the configured API key",
                    error_code="DNSDUMPSTER_INVALID_KEY",
                )
            if response.status_code == 429:
                logger.warning("DNSDumpster rate limit exceeded for domain: %s", domain)
                raise AppHTTPException(
                    status_code=429,
                    detail="DNSDumpster API rate limit exceeded, try again shortly",
                    error_code="DNSDUMPSTER_RATE_LIMITED",
                )

            response.raise_for_status()
            data = response.json()
            logger.info("Retrieved DNSDumpster data for domain: %s", domain)
            return data

    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching DNSDumpster data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=504,
            detail="Request timeout while connecting to DNSDumpster",
            error_code="DNSDUMPSTER_TIMEOUT",
        )
    except httpx.RequestError as e:
        logger.error("Request error while fetching DNSDumpster data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=503,
            detail=f"Failed to connect to DNSDumpster: {str(e)}",
            error_code="DNSDUMPSTER_CONNECTION_ERROR",
        )
    except httpx.HTTPStatusError as e:
        logger.error("HTTP status error from DNSDumpster for domain %s: Status %s", domain, e.response.status_code)
        raise AppHTTPException(
            status_code=e.response.status_code,
            detail=f"DNSDumpster API returned error: {e.response.status_code}",
            error_code="DNSDUMPSTER_API_ERROR",
        )
    except ValueError as e:
        logger.error("Could not parse DNSDumpster JSON response for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=502,
            detail="DNSDumpster returned an unexpected (non-JSON) response",
            error_code="DNSDUMPSTER_INVALID_RESPONSE",
        )
    except AppHTTPException:
        raise
    except Exception as e:
        logger.error("Unexpected error while fetching DNSDumpster data for domain %s: %s", domain, e, exc_info=True)
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching DNSDumpster data",
            error_code="DNSDUMPSTER_UNEXPECTED_ERROR",
        )
