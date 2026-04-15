import json
import logging
import threading
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0)


class ServiceError(Exception):
    """Base exception for external service errors"""

    def __init__(self, service_name: str, message: str, status_code: int = 500) -> None:
        self.service_name = service_name
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ServiceAuthError(ServiceError):
    """Raised when an API key is missing or authentication fails"""

    def __init__(self, service_name: str, message: str) -> None:
        super().__init__(service_name, message, status_code=401)


class ServiceRateLimitError(ServiceError):
    """Raised when an external service rate-limits the request"""

    def __init__(self, service_name: str, message: str, retry_after: str = "unknown") -> None:
        self.retry_after = retry_after
        super().__init__(service_name, message, status_code=429)


class ServiceUnavailableError(ServiceError):
    """Raised when an external service is unreachable"""

    def __init__(self, service_name: str, message: str) -> None:
        super().__init__(service_name, message, status_code=503)

_shared_client: httpx.AsyncClient | None = None
_client_lock = threading.Lock()


def get_client() -> httpx.AsyncClient:
    """Get or create the shared httpx.AsyncClient with connection pooling (thread-safe)"""
    global _shared_client
    if _shared_client is not None and not _shared_client.is_closed:
        return _shared_client

    with _client_lock:
        if _shared_client is None or _shared_client.is_closed:
            _shared_client = httpx.AsyncClient(
                timeout=DEFAULT_TIMEOUT,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return _shared_client


async def close_client() -> None:
    """Close the shared httpx client, releasing all connections"""
    global _shared_client
    if _shared_client and not _shared_client.is_closed:
        await _shared_client.aclose()
        _shared_client = None


def _extract_error_detail(response: httpx.Response, default: str) -> str:
    """Extract a human-readable error message from an HTTP error response"""
    try:
        content_type = response.headers.get('content-type', '')
        if response.content and content_type.startswith('application/json'):
            body = response.json()
            if 'errors' in body and body['errors']:
                return body['errors'][0].get('detail', str(body))
            if 'message' in body:
                return body['message']
            if 'error' in body and isinstance(body['error'], str):
                return body['error']
        else:
            text = response.text.strip()
            if text:
                return text
    except (json.JSONDecodeError, ValueError, AttributeError):
        text = response.text.strip()
        if text:
            return text
    return default


async def handle_response(service_name: str, response: httpx.Response) -> dict[str, Any]:
    """Centralized response handling for HTTP requests to external services.

    Raises ServiceError subclasses on failure instead of returning error dicts.
    """
    try:
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as http_err:
        status_code = http_err.response.status_code

        if status_code == 429:
            retry_after = http_err.response.headers.get('Retry-After', 'unknown')
            logger.warning("Rate limit hit for %s (retry_after=%s)", service_name, retry_after)
            raise ServiceRateLimitError(
                service_name,
                f"{service_name} rate limit exceeded. Please try again later.",
                retry_after=retry_after,
            )

        error_detail = _extract_error_detail(
            http_err.response, f"HTTP {status_code} Error"
        )
        logger.warning("HTTP error in %s: %s", service_name, error_detail)
        raise ServiceError(service_name, f"{service_name} error: {error_detail}", status_code)

    except httpx.RequestError as req_err:
        logger.error("Request error in %s: %s", service_name, req_err)
        raise ServiceUnavailableError(service_name, f"Could not connect to {service_name}: {req_err}")
    except json.JSONDecodeError as json_err:
        logger.error("JSON decode error in %s: %s", service_name, json_err)
        raise ServiceError(service_name, f"Failed to parse response from {service_name}.")


def _require_apikey(service_name: str, apikey: str) -> None:
    """Validate that an API key is present, raising ServiceAuthError if not"""
    if not apikey:
        raise ServiceAuthError(service_name, f"{service_name} API key is missing.")


def _require_credentials(service_name: str, **credentials: str) -> None:
    """Validate that all credentials are present, raising ServiceAuthError if not"""
    if not all(credentials.values()):
        raise ServiceAuthError(service_name, f"{service_name} credentials missing.")


async def _authenticate_oauth(
    service_name: str, token_url: str, **kwargs: Any
) -> str:
    """Perform OAuth token exchange, returning the access token"""
    client = get_client()
    token_res = await client.post(url=token_url, **kwargs)
    token_data = await handle_response(f"{service_name} Auth", token_res)

    access_token = token_data.get('access_token')
    if not access_token:
        raise ServiceError(service_name, f"Failed to retrieve {service_name} access token.")
    return access_token
