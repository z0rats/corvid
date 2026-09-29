"""Runs GHunt (in its own isolated venv, see ghunt_config.py) as a subprocess to look up a
Google account's public profile by email.

GHunt's session-file path is hardcoded to `~/.malfrats/ghunt/creds.m` (no CLI option to
override it - see ghunt/objects/base.py::GHuntCreds upstream), so per-request isolation is done
by giving the child process its own private `HOME` pointing at a throwaway temp directory, torn
down in a `finally` regardless of outcome. Only one GHunt run is allowed at a time
(`_SEMAPHORE`) - there is exactly one stored session, and GHunt's own account is Google-rate-
limited, so concurrent runs would just race each other against the same account.

GHunt has no per-failure exit code (see module docstring in ghunt_session_service.py for the
session-format background); the exit-code/stderr heuristic below is documented, not guaranteed,
and calls out where it's unverified - see docs/architecture/ghunt.md.
"""

import asyncio
import datetime
import json
import logging
import os
import re
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppHTTPException
from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey
from app.core.utils.cli_tool_version import get_cli_tool_version
from app.core.utils.pypi_version_check import fetch_latest_pypi_version
from app.features.email_search.config.ghunt_config import (
    ERROR_EXECUTION_ERROR,
    ERROR_NOT_FOUND,
    ERROR_SESSION_EXPIRED,
    ERROR_SESSION_INVALID,
    ERROR_SESSION_MISSING,
    ERROR_TIMEOUT,
    GHUNT_BIN,
    PACKAGE_NAME,
    SESSION_KEY_NAME,
    TIMEOUT_SECONDS,
)
from app.features.email_search.schemas.ghunt_schemas import (
    GhuntHealthResponse,
    GhuntPhoto,
    GhuntProfileResponse,
)
from app.features.email_search.service.ghunt_session_service import parse_ghunt_session

logger = logging.getLogger(__name__)

_SEMAPHORE = asyncio.Semaphore(1)
_STDERR_TRUNCATE_CHARS = 500
_VERSION_RE = re.compile(r"GHunt (\d+\.\d+\.\d+)")
_GHUNT_DATETIME_RE = re.compile(r"(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})")

# Substrings from GHunt's own uncaught-exception tracebacks (ghunt/errors.py, ghunt/helpers/
# auth.py) that indicate the stored session itself is the problem, rather than a generic
# execution failure - matched case-insensitively against stderr. Best-effort: GHunt has no
# dedicated exit code for this, see this module's docstring.
_SESSION_ERROR_MARKERS = (
    "ghuntinvalidsession",
    "authurl",
    "authorization",
    "masterautherror",
    "osidautherror",
)


@lru_cache(maxsize=1)
def get_ghunt_version() -> str | None:
    """Installed GHunt version, read from its own startup banner.

    Every GHunt invocation prints "> GHunt X.Y.Z (...) <" before doing anything else (even
    `--help`), so a cheap `--help` call is enough - it never touches a session, so no isolated
    HOME is needed here. Cached because this call also triggers GHunt's own outbound
    update-check request (no CLI flag disables it - see docs/architecture/ghunt.md).
    """
    return get_cli_tool_version(GHUNT_BIN, version_args=("--help",), version_regex=_VERSION_RE)


async def get_ghunt_health(db: AsyncSession) -> GhuntHealthResponse:
    installed = get_ghunt_version() is not None
    latest_version = await fetch_latest_pypi_version(PACKAGE_NAME)
    apikey = await get_apikey(db, SESSION_KEY_NAME)
    session_configured = bool(
        apikey and apikey.is_usable() and parse_ghunt_session(apikey.key) is not None
    )
    return GhuntHealthResponse(
        installed=installed,
        version=get_ghunt_version(),
        latest_version=latest_version,
        session_configured=session_configured,
    )


def _parse_ghunt_datetime(value: Any) -> datetime.datetime | None:
    if not isinstance(value, str):
        return None
    match = _GHUNT_DATETIME_RE.match(value)
    if not match:
        return None
    try:
        return datetime.datetime.strptime(match.group(1), "%Y/%m/%d %H:%M:%S").replace(
            tzinfo=datetime.UTC
        )
    except ValueError:
        return None


def _parse_photo(raw: dict[str, Any] | None) -> GhuntPhoto | None:
    if not raw:
        return None
    return GhuntPhoto(url=raw.get("url"), is_default=bool(raw.get("isDefault")))


def parse_ghunt_profile_json(raw: Any, email: str) -> GhuntProfileResponse:
    """Parse GHunt's `--json` output into a `GhuntProfileResponse`.

    Tolerant of the top-level container key's exact name (GHunt names it `f"{container}_
    CONTAINER"`, and only ever populates the "PROFILE" container for a plain email lookup, but
    the literal key isn't relied on) - see docs/architecture/ghunt.md for the full shape,
    derived from the pinned 2.3.4 source rather than a live capture.
    """
    if not isinstance(raw, dict) or not raw:
        raise ValueError("Empty or unexpected GHunt output")

    container_data = next(iter(raw.values()))
    if not isinstance(container_data, dict):
        raise ValueError("Unexpected GHunt output shape")

    profile = container_data.get("profile") or {}
    source_ids = (profile.get("sourceIds") or {}).get("PROFILE") or {}
    emails = (profile.get("emails") or {}).get("PROFILE") or {}
    profile_info = (profile.get("profileInfos") or {}).get("PROFILE") or {}
    in_app = (profile.get("inAppReachability") or {}).get("PROFILE") or {}
    extended = profile.get("extendedData") or {}
    dynamite = extended.get("dynamiteData") or {}
    gplus = extended.get("gplusData") or {}

    return GhuntProfileResponse(
        gaia_id=profile.get("personId") or "",
        email=emails.get("value") or email,
        profile_photo=_parse_photo((profile.get("profilePhotos") or {}).get("PROFILE")),
        cover_photo=_parse_photo((profile.get("coverPhotos") or {}).get("PROFILE")),
        last_profile_edit=_parse_ghunt_datetime(source_ids.get("lastUpdated")),
        user_types=list(profile_info.get("userTypes") or []),
        activated_services=list(in_app.get("apps") or []),
        entity_type=dynamite.get("entityType") or None,
        is_enterprise_user=bool(gplus.get("isEntrepriseUser")),
        play_games=container_data.get("play_games"),
        maps=container_data.get("maps"),
        calendar=container_data.get("calendar"),
    )


def _looks_like_session_error(stderr_text: str) -> bool:
    lowered = stderr_text.lower()
    return any(marker in lowered for marker in _SESSION_ERROR_MARKERS)


async def run_ghunt_profile(db: AsyncSession, email: str) -> GhuntProfileResponse:
    apikey = await get_apikey(db, SESSION_KEY_NAME)
    if not apikey or not apikey.is_usable():
        raise AppHTTPException(
            status_code=409,
            detail="No GHunt session configured - add one under Settings > API Keys",
            error_code=ERROR_SESSION_MISSING,
        )

    if parse_ghunt_session(apikey.key) is None:
        raise AppHTTPException(
            status_code=409,
            detail="Stored GHunt session is structurally invalid",
            error_code=ERROR_SESSION_INVALID,
        )

    async with _SEMAPHORE:
        tmp_home = tempfile.mkdtemp(prefix="ghunt-")
        try:
            os.chmod(tmp_home, 0o700)
            creds_dir = Path(tmp_home) / ".malfrats" / "ghunt"
            creds_dir.mkdir(parents=True, exist_ok=True)
            creds_path = creds_dir / "creds.m"
            creds_path.write_text(apikey.key, encoding="utf-8")
            os.chmod(creds_path, 0o600)

            out_path = Path(tmp_home) / "out.json"
            env = {"HOME": tmp_home, "PATH": "/usr/bin:/bin"}

            process = await asyncio.create_subprocess_exec(
                GHUNT_BIN,
                "email",
                email,
                "--json",
                str(out_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            try:
                _, stderr = await asyncio.wait_for(process.communicate(), timeout=TIMEOUT_SECONDS)
            except TimeoutError as e:
                process.kill()
                await process.wait()
                raise AppHTTPException(
                    status_code=504,
                    detail="GHunt timed out",
                    error_code=ERROR_TIMEOUT,
                ) from e

            if process.returncode == 0 and not out_path.exists():
                raise AppHTTPException(
                    status_code=404,
                    detail="No public Google account found for this email",
                    error_code=ERROR_NOT_FOUND,
                )

            if process.returncode != 0:
                stderr_text = stderr.decode(errors="replace").strip()
                if _looks_like_session_error(stderr_text):
                    raise AppHTTPException(
                        status_code=409,
                        detail="Stored GHunt session appears to be expired or rejected by "
                        "Google - generate a new one with `ghunt login`",
                        error_code=ERROR_SESSION_EXPIRED,
                    )
                logger.warning(
                    "GHunt exited with code %s: %s",
                    process.returncode,
                    stderr_text[:_STDERR_TRUNCATE_CHARS],
                )
                raise AppHTTPException(
                    status_code=502,
                    detail=(stderr_text[:_STDERR_TRUNCATE_CHARS] or "GHunt exited with an error"),
                    error_code=ERROR_EXECUTION_ERROR,
                )

            try:
                raw = json.loads(out_path.read_text(encoding="utf-8"))
                return parse_ghunt_profile_json(raw, email)
            except (json.JSONDecodeError, ValueError, OSError) as e:
                logger.error("Failed to parse GHunt output: %s", e)
                raise AppHTTPException(
                    status_code=502,
                    detail="GHunt's output didn't match what this tool expects - it may have "
                    "changed its output format",
                    error_code=ERROR_EXECUTION_ERROR,
                ) from e
        finally:
            shutil.rmtree(tmp_home, ignore_errors=True)
