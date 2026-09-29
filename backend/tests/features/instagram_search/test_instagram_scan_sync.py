"""Direct tests for `_scan_sync`'s own loop: stop_event/deadline checks,
the SCAN_MAX_ITEMS cap, per-scan_type item mapping, and total_count/truncated
derivation. `instaloader.Profile.from_username` and the profile's own
get_followers/get_followees/get_posts are monkeypatched - no real network call.
"""

import datetime
import threading
import time

import instaloader

from app.features.instagram_search.config.instagram_search_config import SCAN_MAX_ITEMS
from app.features.instagram_search.service.instagram_scan_service import _scan_sync


class _FakeFollowNode:
    def __init__(self, username, full_name):
        self.username = username
        self.full_name = full_name


class _FakePost:
    def __init__(self, shortcode, likes=10, comments=2, is_video=False, caption="hello"):
        self.shortcode = shortcode
        self.likes = likes
        self.comments = comments
        self.is_video = is_video
        self.caption = caption
        self.date_utc = datetime.datetime(2026, 1, 1)


class _FakeIterator:
    def __init__(self, items, count=None):
        self._items = items
        self._count = count

    def __iter__(self):
        return iter(self._items)

    @property
    def count(self):
        if self._count is None:
            raise RuntimeError("count unavailable")
        return self._count


class _FakeProfile:
    def __init__(self, followers=None, followees=None, posts=None):
        self._followers = followers
        self._followees = followees
        self._posts = posts

    def get_followers(self):
        return self._followers

    def get_followees(self):
        return self._followees

    def get_posts(self):
        return self._posts


def _patch_from_username(monkeypatch, profile):
    monkeypatch.setattr(instaloader.Profile, "from_username", lambda context, username: profile)


def _no_stop():
    return threading.Event()


def _far_future_deadline():
    return time.monotonic() + 3600


class TestFollowersMapping:
    def test_maps_username_and_full_name_only(self, monkeypatch):
        nodes = [_FakeFollowNode("a", "A Name"), _FakeFollowNode("b", "B Name")]
        profile = _FakeProfile(followers=_FakeIterator(nodes, count=2))
        _patch_from_username(monkeypatch, profile)

        result = _scan_sync("followers", "target", None, _no_stop(), _far_future_deadline())

        assert result["items"] == [
            {"username": "a", "full_name": "A Name"},
            {"username": "b", "full_name": "B Name"},
        ]
        assert result["total_count"] == 2
        assert result["truncated"] is False


class TestPostsMapping:
    def test_maps_post_fields_and_builds_permalink(self, monkeypatch):
        post = _FakePost("ABC123", likes=50, comments=3, is_video=True, caption="x" * 600)
        profile = _FakeProfile(posts=_FakeIterator([post], count=1))
        _patch_from_username(monkeypatch, profile)

        result = _scan_sync("posts", "target", None, _no_stop(), _far_future_deadline())

        item = result["items"][0]
        assert item["shortcode"] == "ABC123"
        assert item["permalink"] == "https://www.instagram.com/p/ABC123/"
        assert item["is_video"] is True
        assert item["likes"] == 50
        assert item["comments"] == 3
        assert len(item["caption"]) == 500  # truncated


class TestStopConditions:
    def test_stops_early_when_the_stop_event_is_set(self, monkeypatch):
        nodes = [_FakeFollowNode(str(i), None) for i in range(10)]
        profile = _FakeProfile(followees=_FakeIterator(nodes, count=10))
        _patch_from_username(monkeypatch, profile)

        stop_event = threading.Event()
        stop_event.set()

        result = _scan_sync("followees", "target", None, stop_event, _far_future_deadline())

        assert result["items"] == []
        assert result["truncated"] is True

    def test_stops_once_the_deadline_has_passed(self, monkeypatch):
        nodes = [_FakeFollowNode(str(i), None) for i in range(10)]
        profile = _FakeProfile(followers=_FakeIterator(nodes, count=10))
        _patch_from_username(monkeypatch, profile)

        past_deadline = time.monotonic() - 1

        result = _scan_sync("followers", "target", None, _no_stop(), past_deadline)

        assert result["items"] == []
        assert result["truncated"] is True

    def test_stops_at_scan_max_items_and_reports_truncated(self, monkeypatch):
        nodes = [_FakeFollowNode(str(i), None) for i in range(SCAN_MAX_ITEMS + 10)]
        profile = _FakeProfile(followers=_FakeIterator(nodes, count=len(nodes)))
        _patch_from_username(monkeypatch, profile)

        result = _scan_sync("followers", "target", None, _no_stop(), _far_future_deadline())

        assert len(result["items"]) == SCAN_MAX_ITEMS
        assert result["truncated"] is True

    def test_not_truncated_when_the_full_list_is_short_and_exhausted(self, monkeypatch):
        nodes = [_FakeFollowNode("a", None)]
        profile = _FakeProfile(followers=_FakeIterator(nodes, count=1))
        _patch_from_username(monkeypatch, profile)

        result = _scan_sync("followers", "target", None, _no_stop(), _far_future_deadline())

        assert result["truncated"] is False

    def test_survives_a_total_count_that_is_unavailable(self, monkeypatch):
        nodes = [_FakeFollowNode("a", None)]
        profile = _FakeProfile(followers=_FakeIterator(nodes, count=None))
        _patch_from_username(monkeypatch, profile)

        result = _scan_sync("followers", "target", None, _no_stop(), _far_future_deadline())

        assert result["total_count"] is None
        assert result["truncated"] is False


class TestSessionUsage:
    def test_loads_the_session_when_one_is_given(self, monkeypatch):
        profile = _FakeProfile(followers=_FakeIterator([], count=0))
        _patch_from_username(monkeypatch, profile)

        captured = {}

        def fake_load_session(self, username, sessiondata):
            captured["sessiondata"] = sessiondata

        monkeypatch.setattr(instaloader.InstaloaderContext, "load_session", fake_load_session)

        session_data = {"sessionid": "abc", "csrftoken": "def", "ds_user_id": "123"}
        _scan_sync("followers", "target", session_data, _no_stop(), _far_future_deadline())

        assert captured["sessiondata"] == session_data
