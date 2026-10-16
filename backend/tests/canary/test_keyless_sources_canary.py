"""Live canaries for the keyless, scraped/undocumented sources outside ru_business_check: "did the
source change its response shape", not "does our code work" (the mocked suite covers that).

Outcome policy: `policy.py` - network errors and "not answering us" statuses (403/429/451/5xx -
rate limits, anti-bot, geo blocks from a GitHub runner) SKIP; anything else - a 401 (the source
now demands a key), a JSON endpoint answering HTML, a missing field the parsers rely on - FAILS.

Deliberately absent: sources that act on a real account (phone_search's sign-in/recovery
flows, email_search's mailcat/user_scanner registration checks) - a weekly probe could trigger
notifications to the account owner - and Instagram, whose anonymous access is rate-limited
too aggressively for a weekly check to say anything about its schema.

Run: `cd backend && pytest -m canary -o addopts= -q` (see .github/workflows/canary.yml). A failing
weekly run opens (or comments on) a `canary-failure` GitHub issue; a new source needs an entry in
`coverage_map.py` (pinned by tests/core/test_canary_coverage.py).
"""

import pytest

from app.core.registry_dumps.common import check_list_floors, download_text, dump_client
from app.features.dork_runner.service.engines import duckduckgo_engine
from app.features.reddit_search.service.reddit_search_service import _build_urls
from app.features.sanctions_search.service import sanctions_search_service
from app.features.sanctions_search.service.opensanctions_csv_parser import parse_targets_csv
from app.features.username_search.service import hudson_rock_service
from app.features.username_search.service.threat_actor_usernames_service import (
    BASE_URL as THREAT_ACTOR_BASE_URL,
)
from app.features.username_search.service.threat_actor_usernames_service import (
    _extract_found_sites,
)
from app.features.youtube.service.youtube_oembed_service import fetch_oembed_data
from app.features.youtube.service.youtube_page_service import fetch_page_metadata
from tests.canary.policy import get, json_body, live

pytestmark = pytest.mark.canary

# Long-lived references: Reddit's CEO account, and the first video ever uploaded to YouTube.
REDDIT_USER = "spez"
YOUTUBE_VIDEO = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


@pytest.mark.parametrize("archive", ["arctic_shift", "pullpush"])
def test_reddit_archive_returns_the_item_fields_reddit_search_reads(archive):
    urls = _build_urls(
        REDDIT_USER,
        "posts",
        subreddit=None,
        date_from=None,
        date_to=None,
        include_nsfw=True,
        cursor_before=None,
        cursor_after=None,
    )
    url = urls[0] if archive == "arctic_shift" else urls[1]
    body = json_body(get(url, headers={"Accept": "application/json"}))

    items = body.get("data")
    assert isinstance(items, list) and items, f"{archive} returned no `data` for u/{REDDIT_USER}"
    for field in ("id", "created_utc", "author", "title"):
        assert items[0].get(field), f"{archive} items lost `{field}`"


def test_threat_actor_usernames_search_shape():
    body = json_body(get(f"{THREAT_ACTOR_BASE_URL}/api/search", params={"q": "admin"}))

    results = body.get("results")
    assert isinstance(results, list) and results, "a common handle should match some forum"
    sites = _extract_found_sites(results)
    assert all(site["site_name"] and site["extra"]["username"] for site in sites)


def test_hudson_rock_username_search_shape():
    body = json_body(get(hudson_rock_service.BASE_URL, params={"username": "test"}))

    assert isinstance(body.get("stealers"), list), "Hudson Rock response lost `stealers`"
    for stealer in body["stealers"]:
        assert "date_compromised" in stealer and "computer_name" in stealer


def test_youtube_oembed_metadata():
    data = live(fetch_oembed_data(YOUTUBE_VIDEO))

    assert data.get("title") == "Me at the zoo"
    assert data.get("author_name")


def test_youtube_page_metadata_scrape():
    meta = live(fetch_page_metadata(YOUTUBE_VIDEO))
    if not meta or not ({"name", "identifier"} & meta.keys()):
        # A consent/anti-bot page still carries a <meta name="keywords"> but no itemprop data.
        pytest.skip("YouTube served no itemprop metadata (consent/anti-bot page)")

    assert meta.get("name") == "Me at the zoo"
    assert meta.get("identifier") == "jNQXAC9IVRw"


def test_duckduckgo_html_results_are_organic_links():
    results = live(duckduckgo_engine.search("site:wikipedia.org osint"))
    if not results:
        pytest.skip("DuckDuckGo returned no results (likely an anti-bot page for this runner)")

    for result in results:
        assert result.title and result.url.startswith(("http://", "https://"))
        assert "duckduckgo.com" not in result.url, f"ad/redirect link leaked in: {result.url}"


def test_opensanctions_sdn_dump_parses_above_the_floors():
    async def fetch() -> str:
        async with dump_client() as client:
            return await download_text(
                client, sanctions_search_service.LIST_URL, sanctions_search_service.SOURCE
            )

    text = live(fetch())

    records, total = parse_targets_csv(text)
    check_list_floors(total, len(records), sanctions_search_service.SOURCE)
    for field in ("opensanctions_id", "name", "schema"):
        assert records[0].get(field), f"OpenSanctions CSV lost `{field}`"
