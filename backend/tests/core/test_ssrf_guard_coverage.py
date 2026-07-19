"""Regression guard for SSRF-guard coverage (see roadmap: "Outbound SSRF guard
coverage audit"). `safe_get` in `app.core.security.ssrf_guard` is the required
entrypoint for any outbound request whose target host is (directly or
indirectly) user-supplied - see that module's docstring.

This walks every backend source file for raw HTTP-client construction
(`httpx.AsyncClient(`/`httpx.Client(`/`requests.get(` etc.) and fails if a
file doing so is neither on the reviewed allowlist below nor importing
`safe_get`. It exists so a new feature copy-pasting an existing HTTP-client
pattern - instead of reusing `safe_get` - fails a test instead of silently
reopening an SSRF hole.

If this test fails on a new file: either route it through `safe_get`, or, if
the target host is fixed/hardcoded (not user-supplied), add it to
`ALLOWLISTED_FIXED_HOST_FILES` below with a one-line reason.
"""
import re
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"

_RAW_CLIENT_RE = re.compile(
    r"httpx\.(?:Async)?Client\(|requests\.(?:get|post|put|delete|patch)\(|aiohttp\.ClientSession\("
)
_SAFE_GET_IMPORT_RE = re.compile(r"from app\.core\.security\.ssrf_guard import[^\n]*\bsafe_get\b")

# Files that construct a raw httpx/requests client against a fixed, hardcoded
# host (PyPI, a specific third-party API, etc.) rather than a user-supplied
# URL - so there's nothing for safe_get to validate. Reviewed manually; keep
# this list in sync when one of these starts accepting a user-controlled host.
ALLOWLISTED_FIXED_HOST_FILES = {
    # PyPI version-check calls (fixed pypi.org host)
    "features/email_search/config/mailcat_config.py",
    "features/username_search/config/maigret_config.py",
    "features/username_search/config/social_analyzer_config.py",
    # Fixed third-party API hosts; only path/query values (IOC, username) are
    # user-supplied, never the host itself
    "features/ioc_tools/domain_finder/service/urlscan_api_service.py",
    "features/ioc_tools/domain_finder/service/crtsh_api_service.py",
    "features/ioc_tools/ioc_lookup/single_lookup/service/client_base.py",
    "features/reddit_search/service/reddit_search_service.py",
    # Dork runner: fixed search-engine hosts (DuckDuckGo/Google/Bing); only the
    # dork query string is user-supplied, never the host
    "features/dork_runner/service/engines/base.py",
    # Quota dashboard: fixed provider hosts (VirusTotal/Shodan/Hunter.io); only
    # the API key is user-supplied, in query/header, never the host
    "core/settings/api_keys/service/quota_clients.py",
}

# Implementation module itself, and its own tests
_EXCLUDED_PATHS = {
    "core/security/ssrf_guard.py",
}


def _iter_source_files():
    for path in APP_ROOT.rglob("*.py"):
        rel = path.relative_to(APP_ROOT).as_posix()
        if rel in _EXCLUDED_PATHS:
            continue
        yield rel, path


def test_raw_http_clients_go_through_safe_get_or_are_allowlisted():
    offenders = []
    for rel, path in _iter_source_files():
        content = path.read_text(encoding="utf-8")
        if not _RAW_CLIENT_RE.search(content):
            continue
        if rel in ALLOWLISTED_FIXED_HOST_FILES:
            continue
        if _SAFE_GET_IMPORT_RE.search(content):
            continue
        offenders.append(rel)

    assert not offenders, (
        "File(s) construct a raw HTTP client without importing safe_get and are not "
        f"in ALLOWLISTED_FIXED_HOST_FILES: {offenders}. If the target host can be "
        "user-supplied, route the request through app.core.security.ssrf_guard.safe_get. "
        "If the host is fixed/hardcoded, add the file to ALLOWLISTED_FIXED_HOST_FILES "
        "in this test with a one-line reason."
    )


def test_allowlist_entries_still_exist_and_still_need_the_exemption():
    """Keeps the allowlist itself honest: an entry that no longer constructs a raw
    client (e.g. refactored to use safe_get) should be removed, not left stale."""
    stale = []
    for rel in ALLOWLISTED_FIXED_HOST_FILES:
        path = APP_ROOT / rel
        assert path.is_file(), f"Allowlisted file no longer exists: {rel}"
        if not _RAW_CLIENT_RE.search(path.read_text(encoding="utf-8")):
            stale.append(rel)

    assert not stale, f"Allowlist entries no longer construct a raw HTTP client, remove them: {stale}"
