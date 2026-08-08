"""Orchestration tests for perform_youtube_lookup - the individual HTTP-fetch
functions (oEmbed/page-scrape/Data API) are monkeypatched so these focus purely
on how the service combines their results, not on real network calls."""
import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.youtube.schemas.youtube_schemas import YoutubeLookupRequest
from app.features.youtube.service import youtube_lookup_service

VIDEO_ID = "dQw4w9WgXcQ"
VIDEO_URL = f"https://www.youtube.com/watch?v={VIDEO_ID}"


def _run(coro):
    return asyncio.run(coro)


async def _fake_get_key_none(db):
    return None


def _fake_get_key_with(key: str | None):
    async def _fake(db):
        return key
    return _fake


async def _fake_oembed_success(video_url):
    return {
        "title": "Never Gonna Give You Up",
        "author_name": "Rick Astley",
        "author_url": "https://www.youtube.com/@RickAstleyYT",
        "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
        "html": "<iframe ...></iframe>",
        "provider_name": "YouTube",
        "width": 480,
        "height": 270,
    }


async def _fake_page_metadata_empty(video_url):
    return {}


async def _fake_page_metadata_full(video_url):
    return {
        "description": "Official music video",
        "duration": "PT3M33S",
        "datePublished": "2009-10-25",
        "channelId": "UCuAXFkgsw1L7xaCfnd5JJOw",
        "keywords": "rick astley, never gonna give you up",
        "interactionCount": "1500000000",
    }


@pytest.fixture(autouse=True)
def _patch_fetchers(monkeypatch):
    monkeypatch.setattr(youtube_lookup_service, "get_youtube_api_key", _fake_get_key_none)
    monkeypatch.setattr(youtube_lookup_service, "fetch_oembed_data", _fake_oembed_success)
    monkeypatch.setattr(youtube_lookup_service, "fetch_page_metadata", _fake_page_metadata_empty)


def test_perform_lookup_rejects_non_youtube_url():
    request = YoutubeLookupRequest(url="https://example.com/not-a-video")
    with pytest.raises(AppHTTPException) as exc_info:
        _run(youtube_lookup_service.perform_youtube_lookup(request, db=None))
    assert exc_info.value.error_code == "YOUTUBE_INVALID_URL"


def test_perform_lookup_returns_oembed_and_thumbnails_without_api_key():
    request = YoutubeLookupRequest(url=VIDEO_URL)
    result = _run(youtube_lookup_service.perform_youtube_lookup(request, db=None))

    assert result.video_id == VIDEO_ID
    assert result.video_url == VIDEO_URL
    assert result.oembed.title == "Never Gonna Give You Up"
    assert result.oembed.author_name == "Rick Astley"
    assert result.thumbnails["hqdefault"] == f"https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg"
    assert result.api_configured is False
    assert result.api_data is None
    assert result.page_metadata is None


def test_perform_lookup_maps_page_metadata_when_scrape_succeeds(monkeypatch):
    monkeypatch.setattr(youtube_lookup_service, "fetch_page_metadata", _fake_page_metadata_full)

    request = YoutubeLookupRequest(url=VIDEO_URL)
    result = _run(youtube_lookup_service.perform_youtube_lookup(request, db=None))

    assert result.page_metadata is not None
    assert result.page_metadata.duration == "PT3M33S"
    assert result.page_metadata.channel_id == "UCuAXFkgsw1L7xaCfnd5JJOw"
    assert result.page_metadata.interaction_count == "1500000000"


def test_perform_lookup_uses_data_api_when_key_configured(monkeypatch):
    monkeypatch.setattr(youtube_lookup_service, "get_youtube_api_key", _fake_get_key_with("test-key"))

    async def _fake_api_data(video_id, api_key):
        assert video_id == VIDEO_ID
        assert api_key == "test-key"
        return {
            "snippet": {"publishedAt": "2009-10-25T00:00:00Z", "channelTitle": "Rick Astley", "tags": ["80s"]},
            "contentDetails": {"duration": "PT3M33S"},
            "statistics": {"viewCount": "1500000000", "likeCount": "18000000"},
            "status": {"privacyStatus": "public"},
        }

    monkeypatch.setattr(youtube_lookup_service, "fetch_video_api_data", _fake_api_data)

    request = YoutubeLookupRequest(url=VIDEO_URL)
    result = _run(youtube_lookup_service.perform_youtube_lookup(request, db=None))

    assert result.api_configured is True
    assert result.api_data is not None
    assert result.api_data.channel_title == "Rick Astley"
    assert result.api_data.view_count == "1500000000"
    assert result.api_data.privacy_status == "public"


def test_perform_lookup_survives_data_api_failure(monkeypatch):
    monkeypatch.setattr(youtube_lookup_service, "get_youtube_api_key", _fake_get_key_with("test-key"))

    async def _fake_api_data_fails(video_id, api_key):
        return None

    monkeypatch.setattr(youtube_lookup_service, "fetch_video_api_data", _fake_api_data_fails)

    request = YoutubeLookupRequest(url=VIDEO_URL)
    result = _run(youtube_lookup_service.perform_youtube_lookup(request, db=None))

    assert result.api_configured is True
    assert result.api_data is None


def test_perform_lookup_propagates_oembed_failure(monkeypatch):
    async def _fake_oembed_fails(video_url):
        raise AppHTTPException(status_code=404, detail="not found", error_code="YOUTUBE_VIDEO_NOT_FOUND")

    monkeypatch.setattr(youtube_lookup_service, "fetch_oembed_data", _fake_oembed_fails)

    request = YoutubeLookupRequest(url=VIDEO_URL)
    with pytest.raises(AppHTTPException) as exc_info:
        _run(youtube_lookup_service.perform_youtube_lookup(request, db=None))
    assert exc_info.value.error_code == "YOUTUBE_VIDEO_NOT_FOUND"
