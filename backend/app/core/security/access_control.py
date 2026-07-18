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
import hmac
import logging
import secrets
from functools import lru_cache

from fastapi import Header, HTTPException, status

from app.core.config.settings import settings
from app.core.security.persisted_secret import load_or_create_secret_file

logger = logging.getLogger(__name__)

_TOKEN_FILE_NAME = ".access_token"


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


async def verify_access_token(authorization: str | None = Header(default=None)) -> None:
    """FastAPI dependency: require `Authorization: Bearer <token>` matching the configured token."""
    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[len("bearer "):]

    if not provided or not hmac.compare_digest(provided, get_access_token()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing access token")
