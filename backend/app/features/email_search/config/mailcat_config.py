from functools import lru_cache
from importlib import metadata as importlib_metadata

from mailcat import CHECKERS, fastmail, gmail, intpl, mailDe, onet, yandex

PACKAGE_NAME = "mailcat-osint"

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
