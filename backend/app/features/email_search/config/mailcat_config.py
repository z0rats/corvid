import logging
from functools import lru_cache
from importlib import metadata as importlib_metadata

import httpx
from mailcat import CHECKERS, fastmail, gmail, intpl, mailDe, onet, yandex

logger = logging.getLogger(__name__)

PACKAGE_NAME = "mailcat-osint"
PYPI_JSON_URL = f"https://pypi.org/pypi/{PACKAGE_NAME}/json"

TIMEOUT_SECONDS_DEFAULT = 10
MAX_CONCURRENCY_DEFAULT = 10
USE_TOR_DEFAULT = False
ENABLE_SMTP_CHECKS_DEFAULT = False
ENABLE_HEADLESS_CHECKS_DEFAULT = False

# gmail/yandex/mailDe use SMTP RCPT probing on TCP/25, which most cloud/Docker
# egress blocks by default - only worth enabling with Tor or a proxy with open port 25.
SMTP_CHECKERS = [gmail, yandex, mailDe]

# fastmail/intpl/onet drive a headless Chromium via requests-html/pyppeteer, which
# lazily downloads a Chromium binary on first real use - opt-in to avoid that
# surprise download/footprint on a stock deployment.
HEADLESS_CHECKERS = [fastmail, intpl, onet]

_OPTIONAL = {id(f) for f in (*SMTP_CHECKERS, *HEADLESS_CHECKERS)}
DEFAULT_CHECKERS = [f for f in CHECKERS if id(f) not in _OPTIONAL]


def get_active_checkers(enable_smtp_checks: bool, enable_headless_checks: bool) -> list:
    """Build the list of mailcat checker coroutines to run for a scan"""
    checkers = list(DEFAULT_CHECKERS)
    if enable_smtp_checks:
        checkers += SMTP_CHECKERS
    if enable_headless_checks:
        checkers += HEADLESS_CHECKERS
    return checkers


@lru_cache
def get_installed_version() -> str:
    """Installed mailcat-osint package version, read from package metadata"""
    return importlib_metadata.version(PACKAGE_NAME)


async def fetch_latest_pypi_version(timeout_seconds: float = 5.0) -> str | None:
    """Check PyPI for the latest published mailcat-osint version.

    Returns None on any network/parsing error rather than raising - this is
    a best-effort "is an update available" check, not a required operation.
    """
    try:
        async with httpx.AsyncClient(timeout=timeout_seconds) as client:
            response = await client.get(PYPI_JSON_URL)
            response.raise_for_status()
            return response.json()["info"]["version"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Failed to check PyPI for latest mailcat-osint version: %s", exc)
        return None
