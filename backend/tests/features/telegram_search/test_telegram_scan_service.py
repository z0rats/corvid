"""run_scan's orchestration (profile card -> preview paging -> metrics/result) - `ScanRun.execute`
itself is mocked out, same split as steam_recon's scan service test; the lifecycle is covered by
tests/core/scans/test_run.py."""

import asyncio
from pathlib import Path

import pytest

from app.core.external_sources.contract import SourceDriftError
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanCancelled, ScanRun
from app.features.telegram_search.models.telegram_search_models import TelegramChannelSearch
from app.features.telegram_search.schemas.telegram_search_schemas import ScanRequest
from app.features.telegram_search.service import telegram_scan_service as svc
from app.features.telegram_search.service.telegram_scan_service import (
    TelegramSearchError,
    run_scan,
)
from app.features.telegram_search.service.tme_client import (
    TelegramRateLimitedError,
    TelegramSourceError,
)

FIXTURES = Path(__file__).parent / "fixtures"
PROFILE = (FIXTURES / "profile_channel.html").read_text(encoding="utf-8")
PREVIEW = (FIXTURES / "preview_page.html").read_text(encoding="utf-8")
FIRST_PAGE = (FIXTURES / "preview_first_page.html").read_text(encoding="utf-8")


class FakeClient:
    """Serves the fixtures: page 1 is preview_page.html (cursor 101), `before=101` is the oldest
    page (post #1 only), `before=2` is the created-date lookup."""

    def __init__(self, profile=PROFILE, pages=None, preview=True):
        self.profile = profile
        self.pages = pages if pages is not None else {None: PREVIEW, 101: FIRST_PAGE}
        self.preview = preview
        self.requests: list[int | None] = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def fetch_profile_page(self, channel):
        if isinstance(self.profile, Exception):
            raise self.profile
        return self.profile

    async def fetch_preview_page(self, channel, before=None):
        self.requests.append(before)
        if not self.preview:
            return None
        if before == 2:
            return FIRST_PAGE
        page = self.pages[before]
        if isinstance(page, BaseException):
            raise page
        return page


@pytest.fixture
def fake_client(monkeypatch):
    client = FakeClient()
    monkeypatch.setattr(svc, "TmeClient", lambda: client)
    monkeypatch.setattr(svc, "PAGE_DELAY_SECONDS", 0)
    return client


@pytest.fixture
def captured(monkeypatch):
    captured = {}

    async def fake_execute(feature_name, model, run_work, on_event, **kwargs):
        captured.update(feature_name=feature_name, model=model, run_work=run_work, **kwargs)

    monkeypatch.setattr(ScanRun, "execute", fake_execute)
    return captured


def _start(target="@TgInfo", max_posts=100):
    queue: asyncio.Queue = asyncio.Queue()
    asyncio.run(run_scan(ScanRequest(target=target, max_posts=max_posts), queue))
    return queue


def _work(captured):
    return asyncio.run(captured["run_work"](1))


def _stages(queue):
    stages = []
    while not queue.empty():
        event = queue.get_nowait()
        if event is not None:
            stages.append(event["data"]["stage"])
    return stages


def test_hands_scan_run_the_feature_model_and_normalized_channel(captured, fake_client):
    _start(target="https://t.me/s/TgInfo", max_posts=40)

    assert captured["feature_name"] == "telegram_search"
    assert captured["model"] is TelegramChannelSearch
    assert captured["create_fields"] == {
        "target": "https://t.me/s/TgInfo",
        "channel": "tginfo",
        "max_posts": 40,
    }
    assert isinstance(captured["cancellable"], TaskCancellable)
    assert {TelegramSearchError, TelegramSourceError, SourceDriftError} <= set(
        captured["expected_exceptions"]
    )


def test_full_run_pages_back_to_the_first_post_and_builds_the_result(captured, fake_client):
    queue = _start()

    outcome = _work(captured)

    # Two preview pages; post #1 came with the oldest page, so no separate created-date lookup.
    assert fake_client.requests == [None, 101]
    assert outcome.fields == {
        "title": "Telegram Info",
        "kind": "channel",
        "member_count": 83253,
        "posts_sampled": 8,
    }
    result = outcome.db_only_fields["result"]
    assert result["profile"]["username"] == "tginfo"
    assert result["profile"]["url"] == "https://t.me/tginfo"
    assert result["profile"]["preview_available"] is True
    assert result["profile"]["created_at"].startswith("2015-10-28")
    assert "subscribers" not in result["profile"]["media_counters"]
    assert [p["id"] for p in result["posts"]] == list(range(108, 100, -1))  # newest first
    assert result["metrics"]["posts_sampled"] == 8
    assert result["metrics"]["forwarded_count"] == 4
    assert result["top_posts"][0]["id"] == 107  # 1.31M views
    assert result["indicators"]
    assert _stages(queue) == [
        "profile",
        "profile_done",
        "posts",
        "posts",
        "analyzing",
    ]


def test_sample_stops_at_max_posts_and_looks_up_the_creation_date_separately(captured, fake_client):
    _start(max_posts=3)

    outcome = _work(captured)

    assert fake_client.requests == [None, 2]
    result = outcome.db_only_fields["result"]
    assert [p["id"] for p in result["posts"]] == [108, 107, 106]
    assert result["profile"]["created_at"].startswith("2015-10-28")


def test_a_cursor_that_does_not_move_back_stops_paging(captured, fake_client):
    fake_client.pages = {None: PREVIEW, 101: PREVIEW}

    _start(max_posts=500)
    outcome = _work(captured)

    assert fake_client.requests == [None, 101, 2]
    assert outcome.fields["posts_sampled"] == 8  # the repeated page added no duplicates


def test_preview_disabled_gives_a_profile_only_result(captured, fake_client):
    fake_client.preview = False
    _start()

    outcome = _work(captured)

    result = outcome.db_only_fields["result"]
    assert result["profile"]["preview_available"] is False
    assert result["metrics"] is None
    assert result["posts"] == []
    assert fake_client.requests == [None]


def test_missing_channel_fails_with_a_clear_message(captured, fake_client):
    fake_client.profile = (FIXTURES / "profile_not_found.html").read_text(encoding="utf-8")
    _start(target="nosuchchannel")

    with pytest.raises(TelegramSearchError, match="No public Telegram channel or group named"):
        _work(captured)


def test_user_account_is_rejected(captured, fake_client):
    fake_client.profile = (
        '<div class="tgme_page_title"><span>Someone</span></div>'
        '<div class="tgme_page_extra">@someone</div>'
    )
    _start(target="someone")

    with pytest.raises(TelegramSearchError, match="user or bot account"):
        _work(captured)


def test_rate_limit_propagates_as_the_retry_message(captured, fake_client):
    fake_client.profile = TelegramRateLimitedError(30)
    _start()

    with pytest.raises(TelegramRateLimitedError, match="retry in 30 s"):
        _work(captured)


def test_cancel_mid_sampling_keeps_the_posts_read_so_far(captured, fake_client):
    fake_client.pages = {None: PREVIEW, 101: asyncio.CancelledError()}
    _start()

    with pytest.raises(ScanCancelled) as exc_info:
        _work(captured)

    outcome = exc_info.value.outcome
    assert outcome.fields["posts_sampled"] == 8
    assert outcome.db_only_fields["result"]["metrics"]["posts_sampled"] == 8


def test_creation_date_requires_the_channel_created_service_post(captured, fake_client):
    ordinary_first = FIRST_PAGE.replace("service_message", "")

    async def fetch(channel, before=None):
        fake_client.requests.append(before)
        return ordinary_first if before == 2 else PREVIEW

    fake_client.fetch_preview_page = fetch
    _start(max_posts=3)

    result = _work(captured).db_only_fields["result"]

    assert result["profile"]["created_at"] is None
