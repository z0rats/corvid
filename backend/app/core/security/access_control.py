"""Access-token gate for the whole API.

The app has no user accounts (single-user tool), so this is the substitute for
a login: one shared secret, required on every `/api/*` request (and on `/docs`
/`/openapi.json` - see main.py). Comes from API_ACCESS_TOKEN if set, otherwise
one is generated once and persisted to `<data_dir>/.access_token` - the same
pattern as the encryption key in secrets_crypto.py.

The WebSocket route (`alerts_routes.py`) checks this same token itself via a
query param instead of this dependency, since browsers can't attach a custom
Authorization header to a WebSocket handshake.
"""

import asyncio
import hmac
import logging
import secrets
import time
from functools import lru_cache

from fastapi import Header, HTTPException, status

from app.core.alerts.service.alerts_service import raise_alert
from app.core.config.settings import settings
from app.core.database import managed_session
from app.core.security.persisted_secret import load_or_create_secret_file, overwrite_secret_file

logger = logging.getLogger(__name__)

_TOKEN_FILE_NAME = ".access_token"

# Rate-limits the "failed auth attempts" alert so a bot/stale-client hammering
# this endpoint (a hot, potentially adversarial path) triggers at most one
# notification per window instead of one per rejected request. Fire-and-forget
# (asyncio.create_task, not an inline await) for the same reason: never add
# Telegram's own latency (up to its 10s timeout) to a 401 response, which would
# otherwise let an attacker turn this into a self-inflicted slow-response DoS.
_FAILED_AUTH_ALERT_COOLDOWN_SECONDS = 900
_failed_auth_count = 0
_last_failed_auth_alert_at: float | None = None
_background_tasks: set[asyncio.Task] = set()


def _fire_and_forget(coro) -> None:
    task = asyncio.create_task(coro)
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)


async def _raise_failed_auth_alert(count: int) -> None:
    async with managed_session() as db:
        await raise_alert(
            db,
            module="security",
            title="Failed access-token attempts",
            message=(
                f"{count} request(s) were rejected for an invalid or missing access "
                f"token in the last {_FAILED_AUTH_ALERT_COOLDOWN_SECONDS // 60} minutes."
            ),
            telegram_category="security",
        )


def _record_failed_auth() -> None:
    """Bump the failed-attempt counter; fire an alert at most once per cooldown
    window, resetting the counter each time so the next window's count starts fresh."""
    global _failed_auth_count, _last_failed_auth_alert_at

    _failed_auth_count += 1
    now = time.monotonic()
    if (
        _last_failed_auth_alert_at is not None
        and now - _last_failed_auth_alert_at < _FAILED_AUTH_ALERT_COOLDOWN_SECONDS
    ):
        return

    count, _failed_auth_count = _failed_auth_count, 0
    _last_failed_auth_alert_at = now
    _fire_and_forget(_raise_failed_auth_alert(count))


class AccessTokenFixedError(Exception):
    """Raised by `regenerate_access_token` when API_ACCESS_TOKEN pins a fixed
    value - the env var always wins in `get_access_token`, so overwriting the
    file would silently have no effect."""


def _load_or_create_token_file() -> str:
    value, created = load_or_create_secret_file(_TOKEN_FILE_NAME, lambda: secrets.token_urlsafe(32))
    if created:
        path = f"{settings.data_dir}/{_TOKEN_FILE_NAME}"
        logger.warning(
            "Generated a new API access token, required to use the app. "
            "Retrieve it with: cat %s (or set API_ACCESS_TOKEN to a fixed value).",
            path,
        )
        print(
            f"\n{'=' * 64}\n"
            f"Corvid access token (enter this in the browser):\n\n"
            f"  {value}\n\n"
            f"Also saved to: {path}\n"
            f"{'=' * 64}\n",
            flush=True,
        )
    return value


@lru_cache
def get_access_token() -> str:
    return settings.api.access_token or _load_or_create_token_file()


def regenerate_access_token() -> str:
    """Generate a new access token, persist it, and invalidate the cached value
    so the new token is effective immediately (no restart needed).

    Every other holder of the old token (other browser tabs/devices, the
    browser extension) is signed out on their next request, since this app
    has one shared token rather than per-session credentials.
    """
    if settings.api.access_token:
        raise AccessTokenFixedError(
            "Access token is fixed via the API_ACCESS_TOKEN environment variable; "
            "unset it to allow regeneration."
        )

    new_token = secrets.token_urlsafe(32)
    overwrite_secret_file(_TOKEN_FILE_NAME, new_token)
    get_access_token.cache_clear()
    logger.warning(
        "Access token was regenerated via the API; all other sessions are now signed out."
    )
    return new_token


async def verify_access_token(authorization: str | None = Header(default=None)) -> None:
    """FastAPI dependency: require `Authorization: Bearer <token>` matching the configured token."""
    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[len("bearer ") :]

    if not provided or not hmac.compare_digest(provided, get_access_token()):
        _record_failed_auth()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing access token"
        )
