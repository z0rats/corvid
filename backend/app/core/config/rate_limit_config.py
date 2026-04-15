import ipaddress
import logging

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

from app.core.config.settings import settings

logger = logging.getLogger(__name__)


def _is_valid_ip(value: str) -> bool:
    """Check whether a string is a valid IPv4 or IPv6 address"""
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def _get_client_ip(request: Request) -> str:
    """Extract real client IP from X-Forwarded-For only in production behind a reverse proxy.

    In development the header is ignored because there is no trusted proxy in
    front of the application and any client could spoof the header to bypass
    rate limiting.
    """
    if settings.environment == "production":
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            candidate = forwarded_for.split(",")[0].strip()
            if _is_valid_ip(candidate):
                return candidate
            logger.warning("Ignoring malformed X-Forwarded-For value: %s", candidate)

    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_client_ip,
    default_limits=["120/minute", "5000/hour"],
)
