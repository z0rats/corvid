import asyncio

import httpx
import pytest

from app.core import release_check


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture(autouse=True)
def _reset_cache():
    """Every test starts from a clean module-level cache."""
    release_check._cached_version = None
    release_check._cached_at = 0.0
    release_check._cache_ttl = release_check.FAILURE_CACHE_TTL_SECONDS
    yield
    release_check._cached_version = None
    release_check._cached_at = 0.0
    release_check._cache_ttl = release_check.FAILURE_CACHE_TTL_SECONDS


def _fake_fetch(tag_name):
    async def _inner():
        return tag_name
    return _inner


def _raising_fetch(exc):
    async def _inner():
        raise exc
    return _inner


def test_returns_version_without_leading_v(monkeypatch):
    monkeypatch.setattr(release_check, "_fetch_latest_tag", _fake_fetch("v2.0.3"))

    result = _run(release_check.get_latest_release_version())

    assert result == "2.0.3"


def test_caches_result_within_ttl(monkeypatch):
    calls = {"count": 0}

    async def _fetch():
        calls["count"] += 1
        return "v2.0.3"

    monkeypatch.setattr(release_check, "_fetch_latest_tag", _fetch)

    first = _run(release_check.get_latest_release_version())
    second = _run(release_check.get_latest_release_version())

    assert first == second == "2.0.3"
    assert calls["count"] == 1


def test_refetches_after_success_ttl_expires(monkeypatch):
    monkeypatch.setattr(release_check, "_fetch_latest_tag", _fake_fetch("v2.0.3"))
    _run(release_check.get_latest_release_version())

    monkeypatch.setattr(release_check, "_fetch_latest_tag", _fake_fetch("v2.1.0"))
    release_check._cached_at -= release_check.SUCCESS_CACHE_TTL_SECONDS + 1

    result = _run(release_check.get_latest_release_version())

    assert result == "2.1.0"


def test_returns_none_when_github_is_unreachable(monkeypatch):
    monkeypatch.setattr(
        release_check, "_fetch_latest_tag", _raising_fetch(httpx.ConnectError("offline"))
    )

    result = _run(release_check.get_latest_release_version())

    assert result is None


def test_keeps_last_known_good_version_on_later_failure(monkeypatch):
    monkeypatch.setattr(release_check, "_fetch_latest_tag", _fake_fetch("v2.0.3"))
    _run(release_check.get_latest_release_version())

    monkeypatch.setattr(
        release_check, "_fetch_latest_tag", _raising_fetch(httpx.ConnectError("offline"))
    )
    release_check._cached_at -= release_check.SUCCESS_CACHE_TTL_SECONDS + 1

    result = _run(release_check.get_latest_release_version())

    assert result == "2.0.3"


def test_retries_sooner_after_a_failure_than_after_a_success(monkeypatch):
    """A failed lookup should only block retries for FAILURE_CACHE_TTL_SECONDS,
    not the full SUCCESS_CACHE_TTL_SECONDS - so a transient rate-limit/outage
    doesn't black out the update-check feature for a full hour."""
    monkeypatch.setattr(
        release_check, "_fetch_latest_tag", _raising_fetch(httpx.ConnectError("offline"))
    )
    _run(release_check.get_latest_release_version())

    monkeypatch.setattr(release_check, "_fetch_latest_tag", _fake_fetch("v2.0.3"))
    release_check._cached_at -= release_check.FAILURE_CACHE_TTL_SECONDS + 1

    result = _run(release_check.get_latest_release_version())

    assert result == "2.0.3"
