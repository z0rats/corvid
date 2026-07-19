"""
Certificate Transparency log lookup via crt.sh's JSON endpoint.

crt.sh (run by Sectigo) mirrors public CT logs and needs no API key. A
`%.<domain>` wildcard query returns every certificate issued for the domain
and its subdomains, which doubles as a subdomain-enumeration source: SAN
entries on those certs commonly include hosts an operator never intended to
advertise.
"""
import logging
from typing import Any

import httpx
from app.core.exceptions import AppHTTPException

logger = logging.getLogger(__name__)

CRTSH_URL = "https://crt.sh/"
CRTSH_TIMEOUT = 20.0
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Corvid-Domain-Lookup/1.0",
    "Accept": "application/json",
}


async def fetch_crtsh_certificates(domain: str) -> list[dict[str, Any]]:
    """
    Fetch raw Certificate Transparency log entries for a domain (and its
    subdomains) from crt.sh.

    Args:
        domain: Domain name to search for

    Returns:
        List of raw crt.sh certificate entry dicts

    Raises:
        AppHTTPException: For request failures or an unparseable response
    """
    params = {"q": f"%.{domain}", "output": "json"}
    logger.debug("Fetching crt.sh data for domain: %s", domain)

    try:
        async with httpx.AsyncClient(timeout=CRTSH_TIMEOUT, headers=DEFAULT_HEADERS) as client:
            response = await client.get(CRTSH_URL, params=params)
            response.raise_for_status()

            if not response.content:
                logger.info("crt.sh returned an empty response for domain: %s", domain)
                return []

            data = response.json()
            logger.info("Retrieved %s certificate entries from crt.sh for domain: %s", len(data), domain)
            return data

    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching crt.sh data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=504,
            detail="Request timeout while connecting to crt.sh",
            error_code="CRTSH_TIMEOUT",
        )
    except httpx.RequestError as e:
        logger.error("Request error while fetching crt.sh data for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=503,
            detail=f"Failed to connect to crt.sh: {str(e)}",
            error_code="CRTSH_CONNECTION_ERROR",
        )
    except httpx.HTTPStatusError as e:
        logger.error("HTTP status error from crt.sh for domain %s: Status %s", domain, e.response.status_code)
        raise AppHTTPException(
            status_code=e.response.status_code,
            detail=f"crt.sh returned error: {e.response.status_code}",
            error_code="CRTSH_API_ERROR",
        )
    except ValueError as e:
        # crt.sh serves an HTML error/status page (not JSON) when it's overloaded or the query is malformed
        logger.error("Could not parse crt.sh JSON response for domain %s: %s", domain, e)
        raise AppHTTPException(
            status_code=502,
            detail="crt.sh returned an unexpected (non-JSON) response",
            error_code="CRTSH_INVALID_RESPONSE",
        )
    except Exception as e:
        logger.error("Unexpected error while fetching crt.sh data for domain %s: %s", domain, e, exc_info=True)
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching crt.sh data",
            error_code="CRTSH_UNEXPECTED_ERROR",
        )
