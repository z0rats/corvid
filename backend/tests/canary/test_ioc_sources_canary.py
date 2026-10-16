"""Live canaries for the keyless ioc_lookup providers, the address-blacklist feeds and the
default newsfeed RSS feeds: "did the source change its response shape or move", not "does our
code work" (the mocked suite covers that).

Outcome policy: `policy.py` (network/403/429/451/5xx skip; everything else fails - notably a
401 from a provider we treat as keyless, as when MalwareBazaar started requiring a key). Feed
redirects are followed, as the app's own SSRF-guarded fetch does.

Run: `cd backend && pytest -m canary -o addopts= -q` (see .github/workflows/canary.yml). A failing
weekly run opens (or comments on) a `canary-failure` GitHub issue; a new source needs an entry in
`coverage_map.py` (pinned by tests/core/test_canary_coverage.py).
"""

import httpx
import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.service import (
    blacklist_refresh_service,
    external_api_clients,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import close_client
from app.features.newsfeed.utils.default_rss_feeds import DEFAULT_NEWSFEEDS
from app.features.newsfeed.utils.fetching import _parse_feed_bytes
from tests.canary.policy import get, live

pytestmark = pytest.mark.canary


async def _with_fresh_client(coro):
    # The providers share one pooled httpx client bound to the event loop it was created on;
    # each asyncio.run() is a new loop, so close it before that loop ends.
    try:
        return await coro
    finally:
        await close_client()


def _live(coro):
    return live(_with_fresh_client(coro))


# --- keyless ioc_lookup providers ------------------------------------------------------------

LOG4SHELL = "CVE-2021-44228"


def test_cisa_kev_lists_a_known_exploited_cve():
    result = _live(external_api_clients.check_cisa_kev(LOG4SHELL))
    assert result.get("listed") is True
    assert result.get("vendorProject") and result.get("dateAdded")


def test_first_epss_scores_a_cve():
    result = _live(external_api_clients.search_first_epss(LOG4SHELL))
    entry = (result.get("data") or [{}])[0]
    assert entry.get("cve") == LOG4SHELL
    assert entry.get("epss") is not None and entry.get("percentile") is not None


def test_openphish_feed_loads_and_matches_its_own_entries():
    external_api_clients._openphish_cache["urls"] = None  # force a real download
    urls, _domains = _live(external_api_clients._get_openphish_feed())
    assert len(urls) >= 20, f"OpenPhish feed suspiciously small: {len(urls)} URLs"

    result = _live(external_api_clients.check_openphish(next(iter(urls))))
    assert result.get("listed") is True


def test_urlscan_search_returns_scans():
    result = _live(external_api_clients.check_urlscan("example.com"))
    results = result.get("results")
    assert isinstance(results, list) and results
    assert results[0].get("task") and results[0].get("page")


def test_library_of_leaks_returns_hit_counts():
    result = _live(external_api_clients.check_libraryofleaks("example.com"))
    assert isinstance(result.get("total_hits"), int)
    assert isinstance(result.get("collections"), list)


def test_ffraud_ip_lookup():
    result = _live(external_api_clients.check_ffraud("8.8.8.8"))
    assert result.get("success") is True
    assert isinstance(result.get("fraud_score"), int)


def test_ffraud_email_flags_a_disposable_domain():
    result = _live(external_api_clients.check_ffraud_email("test@mailinator.com"))
    assert result.get("is_disposable") is True


# --- address blacklist feeds -------------------------------------------------------------------


@pytest.mark.parametrize(
    "fetch",
    [
        blacklist_refresh_service.fetch_ofac_addresses,
        blacklist_refresh_service.fetch_scamsniffer_addresses,
        blacklist_refresh_service.fetch_opensanctions_addresses,
    ],
    ids=["ofac", "scamsniffer", "opensanctions"],
)
def test_blacklist_feed_yields_addresses(fetch):
    entries = _live(fetch())
    assert entries, f"{fetch.__name__} returned no addresses"
    assert all(entry.get("address") for entry in entries)


# --- default newsfeed RSS feeds ----------------------------------------------------------------


@pytest.mark.parametrize("feed", DEFAULT_NEWSFEEDS, ids=[f["name"] for f in DEFAULT_NEWSFEEDS])
def test_default_feed_serves_entries(feed):
    try:
        response = get(feed["url"], follow_redirects=True)
    except httpx.HTTPStatusError as exc:
        pytest.fail(f"unexpected {exc} - feed moved? see MOVED_DEFAULT_FEED_URLS")

    parsed = _parse_feed_bytes(feed["url"], response.content)
    assert parsed.entries, "feed parsed but has no entries"
    assert parsed.entries[0].get("title") and parsed.entries[0].get("link")
