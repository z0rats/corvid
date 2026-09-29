import asyncio
from pathlib import Path

import httpx
import pytest

import app.features.steam_recon.service.steam_comments_service as comments_mod
from app.features.steam_recon.service.steam_comments_service import (
    ProfileComment,
    classify_accusatory_ratio,
    fetch_profile_comments,
)
from app.features.steam_recon.utils.steam_id_utils import account_id_to_steamid64

FIXTURE_HTML = (Path(__file__).parent / "fixtures" / "comments_sample.html").read_text()
TARGET_STEAMID64 = account_id_to_steamid64(169802)  # the fixture's own-profile commenter


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def fake_transport(monkeypatch):
    """Route `fetch_profile_comments`'s internal httpx client through `handler`."""
    real_client = httpx.AsyncClient

    def apply(handler):
        monkeypatch.setattr(
            comments_mod.httpx,
            "AsyncClient",
            lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw),
        )

    return apply


class TestFetchProfileComments:
    def test_parses_author_text_and_timestamp_from_the_comment_html(self, fake_transport):
        def handler(request: httpx.Request) -> httpx.Response:
            assert request.url.path == f"/comment/Profile/render/{TARGET_STEAMID64}/-1/"
            return httpx.Response(
                200, json={"success": True, "comments_html": FIXTURE_HTML, "total_count": 3}
            )

        fake_transport(handler)
        comments = _run(fetch_profile_comments(TARGET_STEAMID64))

        assert len(comments) == 3
        first = comments[0]
        assert first.author_steamid64 == account_id_to_steamid64(34093805)
        assert first.text == "this guy is such a cheater, reported for aimbot"
        assert first.timestamp == 1370157709

    def test_a_private_profiles_comment_thread_returns_none(self, fake_transport):
        def handler(request):
            return httpx.Response(200, json={"success": False, "error": "This profile is private."})

        fake_transport(handler)
        assert _run(fetch_profile_comments(TARGET_STEAMID64)) is None

    def test_a_transport_failure_returns_none(self, fake_transport):
        def handler(request):
            raise httpx.ConnectError("boom")

        fake_transport(handler)
        assert _run(fetch_profile_comments(TARGET_STEAMID64)) is None

    def test_a_non_200_status_returns_none(self, fake_transport):
        def handler(request):
            return httpx.Response(500)

        fake_transport(handler)
        assert _run(fetch_profile_comments(TARGET_STEAMID64)) is None


class TestClassifyAccusatoryRatio:
    def test_excludes_the_targets_own_comments_from_the_sample(self):
        comments = [
            ProfileComment(author_steamid64=TARGET_STEAMID64, text="cheater!", timestamp=1),
            ProfileComment(author_steamid64="other", text="hello", timestamp=2),
        ]

        ratio, sample_size = classify_accusatory_ratio(comments, TARGET_STEAMID64)

        assert sample_size == 1
        assert ratio == 0.0

    def test_matches_are_case_insensitive_substrings(self):
        comments = [
            ProfileComment(author_steamid64="a", text="Total CHEATER, obvious AimBot", timestamp=1),
            ProfileComment(
                author_steamid64="b", text="great player, no hacks here, GG", timestamp=2
            ),
        ]

        ratio, sample_size = classify_accusatory_ratio(comments, TARGET_STEAMID64)

        assert sample_size == 2
        assert ratio == 0.5

    def test_empty_sample_after_excluding_self_is_zero_not_a_division_error(self):
        comments = [ProfileComment(author_steamid64=TARGET_STEAMID64, text="cheater", timestamp=1)]

        ratio, sample_size = classify_accusatory_ratio(comments, TARGET_STEAMID64)

        assert (ratio, sample_size) == (0.0, 0)

    def test_no_comments_at_all(self):
        assert classify_accusatory_ratio([], TARGET_STEAMID64) == (0.0, 0)
