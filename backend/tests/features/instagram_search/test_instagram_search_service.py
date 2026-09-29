"""Orchestration tests for perform_profile_lookup - `_fetch_profile_sync` (the
actual blocking Instaloader call) is monkeypatched so these focus on mode
selection and result mapping, not real network calls. Exception-to-status-code
mapping itself is `instagram_common.raise_mapped_instaloader_exception`'s own
concern, exhaustively covered in test_instagram_common.py - this only checks
that a mapped failure actually propagates out of perform_profile_lookup.
"""

import asyncio

import instaloader
import pytest

from app.core.exceptions import AppHTTPException
from app.features.instagram_search.schemas.instagram_search_schemas import (
    InstagramProfileRequest,
)
from app.features.instagram_search.service import instagram_search_service

SESSION_DICT = {"sessionid": "abc", "csrftoken": "def", "ds_user_id": "123"}

PROFILE_FIELDS = {
    "username": "someuser",
    "userid": 42,
    "full_name": "Some User",
    "biography": "bio #tag @mention",
    "biography_hashtags": ["tag"],
    "biography_mentions": ["mention"],
    "external_url": "https://example.com",
    "followers": 100,
    "followees": 10,
    "mediacount": 5,
    "igtvcount": 0,
    "is_private": False,
    "is_verified": False,
    "is_business_account": False,
    "business_category_name": None,
    "has_public_story": False,
    "has_highlight_reels": False,
    "profile_pic_url": "https://example.com/pic.jpg",
}


def _run(coro):
    return asyncio.run(coro)


async def _fake_no_session(db):
    return None


async def _fake_with_session(db):
    return SESSION_DICT


@pytest.fixture(autouse=True)
def _patch_no_session(monkeypatch):
    monkeypatch.setattr(instagram_search_service, "get_session_dict", _fake_no_session)


def _request(username="someuser"):
    return InstagramProfileRequest(username=username)


def test_anonymous_lookup_returns_mapped_profile(monkeypatch):
    def _fake_fetch(username, session_data):
        assert username == "someuser"
        assert session_data is None
        return dict(PROFILE_FIELDS)

    monkeypatch.setattr(instagram_search_service, "_fetch_profile_sync", _fake_fetch)

    result = _run(instagram_search_service.perform_profile_lookup(_request(), db=None))

    assert result.mode == "anonymous"
    assert result.username == "someuser"
    assert result.followers == 100
    assert result.biography_hashtags == ["tag"]


def test_session_lookup_passes_session_data_and_sets_mode(monkeypatch):
    monkeypatch.setattr(instagram_search_service, "get_session_dict", _fake_with_session)

    def _fake_fetch(username, session_data):
        assert session_data == SESSION_DICT
        return dict(PROFILE_FIELDS)

    monkeypatch.setattr(instagram_search_service, "_fetch_profile_sync", _fake_fetch)

    result = _run(instagram_search_service.perform_profile_lookup(_request(), db=None))
    assert result.mode == "session"


def test_private_profile_returns_data_not_error(monkeypatch):
    def _fake_fetch(username, session_data):
        return {**PROFILE_FIELDS, "is_private": True, "followers": None}

    monkeypatch.setattr(instagram_search_service, "_fetch_profile_sync", _fake_fetch)

    result = _run(instagram_search_service.perform_profile_lookup(_request(), db=None))
    assert result.is_private is True


def test_a_mapped_instaloader_exception_propagates_as_app_http_exception(monkeypatch):
    def _fake_fetch(username, session_data):
        raise instaloader.exceptions.ProfileNotExistsException("nope")

    monkeypatch.setattr(instagram_search_service, "_fetch_profile_sync", _fake_fetch)

    with pytest.raises(AppHTTPException) as exc_info:
        _run(instagram_search_service.perform_profile_lookup(_request(), db=None))

    assert exc_info.value.status_code == 404
    assert exc_info.value.error_code == "INSTAGRAM_PROFILE_NOT_FOUND"
