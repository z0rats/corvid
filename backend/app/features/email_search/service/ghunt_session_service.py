"""Validates the structure of a GHunt session blob (the content of `creds.m`) without ever
invoking the GHunt CLI.

Format, read from the pinned upstream version's own save/load code
(`ghunt/objects/base.py::GHuntCreds`, GHunt 2.3.4): `creds.m` is
`base64(json.dumps({"cookies": {...}, "osids": {...}, "android": {"master_token": "...",
"authorization_tokens": {...}}}))`. `GHuntCreds.are_creds_loaded()` requires `cookies`, `osids`
and `android.master_token` to all be truthy - this module replicates that same check so a
malformed paste is rejected at save time instead of surfacing as a confusing subprocess failure
later.
"""

import base64
import binascii
import json
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppHTTPException
from app.core.settings.api_keys.schemas.api_keys_settings_schemas import (
    ApikeyCreateRequest,
    ApikeyStateResponse,
    ApikeyUpdateRequest,
)
from app.core.settings.api_keys.service.api_keys_service import (
    create_apikey_service,
    update_apikey_service,
)
from app.features.email_search.config.ghunt_config import ERROR_SESSION_INVALID, SESSION_KEY_NAME


def parse_ghunt_session(raw: str) -> dict[str, Any] | None:
    """Return the decoded session dict if `raw` is a structurally valid GHunt session blob,
    else None. Never raises."""
    if not raw or not raw.strip():
        return None

    try:
        decoded = base64.b64decode(raw.strip(), validate=True)
        data = json.loads(decoded)
    except binascii.Error, ValueError, UnicodeDecodeError:
        return None

    if not isinstance(data, dict):
        return None

    if not data.get("cookies") or not data.get("osids"):
        return None

    android = data.get("android")
    if not isinstance(android, dict) or not android.get("master_token"):
        return None

    return data


async def save_ghunt_session(db: AsyncSession, value: str) -> ApikeyStateResponse:
    """Validate a pasted GHunt session blob and persist it, without ever running GHunt.

    Reuses the generic Apikey create/update services underneath (same storage as every other
    provider key) - this is a feature-owned entry point only for the structural validation step,
    not a parallel storage mechanism. Returns only name/is_active, never the stored value: unlike
    the generic apikey routes (which echo `ApikeySchema.key` back, harmless for a short API
    token), this is the single most sensitive secret this app stores and must never round-trip
    through a response body - see docs/architecture/ghunt.md.
    """
    if parse_ghunt_session(value) is None:
        raise AppHTTPException(
            status_code=400,
            detail="Not a valid GHunt session - expected the base64 content of creds.m",
            error_code=ERROR_SESSION_INVALID,
        )

    updated = await update_apikey_service(
        db, SESSION_KEY_NAME, ApikeyUpdateRequest(key=value, is_active=True)
    )
    if updated is not None:
        return ApikeyStateResponse(name=updated.name, is_active=updated.is_active)

    created = await create_apikey_service(
        db, ApikeyCreateRequest(name=SESSION_KEY_NAME, key=value, is_active=True)
    )
    if created is None:
        # TOCTOU: another request created the row between our update attempt above (which found
        # nothing) and this create attempt (which found it already exists) - resolve by updating
        # the row that now exists rather than surfacing a confusing 409 for a single-user app.
        retried = await update_apikey_service(
            db, SESSION_KEY_NAME, ApikeyUpdateRequest(key=value, is_active=True)
        )
        if retried is None:
            raise AppHTTPException(
                status_code=500,
                detail="Failed to save GHunt session",
                error_code=ERROR_SESSION_INVALID,
            )
        return ApikeyStateResponse(name=retried.name, is_active=retried.is_active)

    return ApikeyStateResponse(name=created.name, is_active=created.is_active)
