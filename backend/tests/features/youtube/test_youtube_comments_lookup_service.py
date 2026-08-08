"""Orchestration tests for perform_youtube_comments_lookup - fetch_comment_threads and the
API-key lookup are monkeypatched so these focus on listing vs. search-and-filter behavior and
the truncation/cap bookkeeping, not on real network calls."""
import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.youtube.schemas.youtube_schemas import YoutubeCommentsRequest
from app.features.youtube.service import youtube_comments_lookup_service

VIDEO_ID = "dQw4w9WgXcQ"
VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


def _run(coro):
    return asyncio.run(coro)


def _raw_comment(comment_id, author, text, likes=0, replies=0):
    return {
        "id": comment_id,
        "snippet": {
            "totalReplyCount": replies,
            "topLevelComment": {
                "id": comment_id,
                "snippet": {
                    "authorDisplayName": author,
                    "authorChannelUrl": f"https://www.youtube.com/channel/{author}",
                    "authorProfileImageUrl": "https://example.com/avatar.jpg",
                    "textDisplay": text,
                    "likeCount": likes,
                    "publishedAt": "2024-01-01T00:00:00Z",
                    "updatedAt": "2024-01-02T00:00:00Z",
                },
            },
        },
    }


@pytest.fixture(autouse=True)
def _patch_api_key(monkeypatch):
    async def _fake_get_key(db):
        return "test-key"
    monkeypatch.setattr(youtube_comments_lookup_service, "get_youtube_api_key", _fake_get_key)


def test_rejects_non_youtube_url():
    request = YoutubeCommentsRequest(url="https://example.com/not-a-video")
    with pytest.raises(AppHTTPException) as exc_info:
        _run(youtube_comments_lookup_service.perform_youtube_comments_lookup(request, db=None))
    assert exc_info.value.error_code == "YOUTUBE_INVALID_URL"


def test_rejects_when_no_api_key_configured(monkeypatch):
    async def _fake_get_key_none(db):
        return None
    monkeypatch.setattr(youtube_comments_lookup_service, "get_youtube_api_key", _fake_get_key_none)

    request = YoutubeCommentsRequest(url=VIDEO_URL)
    with pytest.raises(AppHTTPException) as exc_info:
        _run(youtube_comments_lookup_service.perform_youtube_comments_lookup(request, db=None))
    assert exc_info.value.error_code == "YOUTUBE_COMMENTS_NOT_CONFIGURED"


def test_plain_listing_returns_one_page(monkeypatch):
    async def _fake_fetch(video_id, api_key, order, page_token, max_results):
        assert video_id == VIDEO_ID
        assert api_key == "test-key"
        assert page_token is None
        return {
            "items": [
                _raw_comment("c1", "alice", "great video"),
                _raw_comment("c2", "bob", "nice"),
            ],
            "nextPageToken": "page2",
        }
    monkeypatch.setattr(youtube_comments_lookup_service, "fetch_comment_threads", _fake_fetch)

    request = YoutubeCommentsRequest(url=VIDEO_URL)
    result = _run(youtube_comments_lookup_service.perform_youtube_comments_lookup(request, db=None))

    assert result.video_id == VIDEO_ID
    assert result.query is None
    assert result.next_page_token == "page2"
    assert result.pages_scanned == 1
    assert [c.comment_id for c in result.comments] == ["c1", "c2"]
    assert result.comments[0].author_display_name == "alice"
    assert result.comments[0].text == "great video"


def test_listing_passes_through_page_token_and_order(monkeypatch):
    captured = {}

    async def _fake_fetch(video_id, api_key, order, page_token, max_results):
        captured["order"] = order
        captured["page_token"] = page_token
        return {"items": [], "nextPageToken": None}
    monkeypatch.setattr(youtube_comments_lookup_service, "fetch_comment_threads", _fake_fetch)

    request = YoutubeCommentsRequest(url=VIDEO_URL, order="time", page_token="abc")
    _run(youtube_comments_lookup_service.perform_youtube_comments_lookup(request, db=None))

    assert captured["order"] == "time"
    assert captured["page_token"] == "abc"


def test_search_filters_by_text_and_author_stops_when_video_exhausted(monkeypatch):
    async def _fake_fetch(video_id, api_key, order, page_token, max_results):
        return {
            "items": [
                _raw_comment("c1", "alice", "this is spam content"),
                _raw_comment("c2", "bob", "totally normal comment"),
                _raw_comment("SPAMBOT99", "SPAMBOT99", "hi"),
            ],
            "nextPageToken": None,
        }
    monkeypatch.setattr(youtube_comments_lookup_service, "fetch_comment_threads", _fake_fetch)

    request = YoutubeCommentsRequest(url=VIDEO_URL, query="spam")
    result = _run(youtube_comments_lookup_service.perform_youtube_comments_lookup(request, db=None))

    assert result.query == "spam"
    assert [c.comment_id for c in result.comments] == ["c1", "SPAMBOT99"]
    assert result.truncated is False
    assert result.pages_scanned == 1
    assert result.next_page_token is None


def test_search_scans_multiple_pages_until_match_found(monkeypatch):
    pages = {
        None: {"items": [_raw_comment("c1", "alice", "nothing here")], "nextPageToken": "p2"},
        "p2": {"items": [_raw_comment("c2", "bob", "found the needle")], "nextPageToken": None},
    }

    async def _fake_fetch(video_id, api_key, order, page_token, max_results):
        return pages[page_token]
    monkeypatch.setattr(youtube_comments_lookup_service, "fetch_comment_threads", _fake_fetch)

    request = YoutubeCommentsRequest(url=VIDEO_URL, query="needle")
    result = _run(youtube_comments_lookup_service.perform_youtube_comments_lookup(request, db=None))

    assert [c.comment_id for c in result.comments] == ["c2"]
    assert result.pages_scanned == 2
    assert result.truncated is False


def test_search_truncates_when_page_cap_hit_before_exhausting(monkeypatch):
    monkeypatch.setattr(youtube_comments_lookup_service, "COMMENTS_SEARCH_MAX_PAGES", 2)

    call_count = {"n": 0}

    async def _fake_fetch(video_id, api_key, order, page_token, max_results):
        call_count["n"] += 1
        # every page has more after it and never contains a match
        return {"items": [_raw_comment(f"c{call_count['n']}", "alice", "no match here")], "nextPageToken": "more"}
    monkeypatch.setattr(youtube_comments_lookup_service, "fetch_comment_threads", _fake_fetch)

    request = YoutubeCommentsRequest(url=VIDEO_URL, query="needle")
    result = _run(youtube_comments_lookup_service.perform_youtube_comments_lookup(request, db=None))

    assert call_count["n"] == 2
    assert result.pages_scanned == 2
    assert result.truncated is True
    assert result.next_page_token == "more"
    assert result.comments == []


def test_search_truncates_when_result_cap_hit_before_exhausting(monkeypatch):
    monkeypatch.setattr(youtube_comments_lookup_service, "COMMENTS_SEARCH_MAX_RESULTS", 2)

    async def _fake_fetch(video_id, api_key, order, page_token, max_results):
        return {
            "items": [
                _raw_comment("c1", "alice", "needle one"),
                _raw_comment("c2", "bob", "needle two"),
                _raw_comment("c3", "carol", "needle three"),
            ],
            "nextPageToken": "more",
        }
    monkeypatch.setattr(youtube_comments_lookup_service, "fetch_comment_threads", _fake_fetch)

    request = YoutubeCommentsRequest(url=VIDEO_URL, query="needle")
    result = _run(youtube_comments_lookup_service.perform_youtube_comments_lookup(request, db=None))

    assert [c.comment_id for c in result.comments] == ["c1", "c2"]
    assert result.truncated is True
    assert result.pages_scanned == 1
