"""verify_access_token is the single dependency gating almost every /api/*
route (see access_control.py's module docstring) - these tests exercise it
through a real HTTP request/response cycle via TestClient, rather than
calling the function directly with a hand-built Header value, so they cover
the actual contract a client (or attacker) hits."""

import asyncio
from collections.abc import Callable

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.config.settings import settings
from app.core.security import access_control
from app.core.security.access_control import (
    AccessTokenFixedError,
    regenerate_access_token,
    verify_access_token,
)
from tests.conftest import run as _run

KNOWN_TOKEN = "test-token-abc123"


@pytest.fixture(autouse=True)
def reset_failed_auth_state(monkeypatch):
    """`_failed_auth_count`/`_last_failed_auth_alert_at` are process-wide module
    state (see access_control.py's rate-limit comment) - reset between tests so
    one test's failed requests don't affect another's cooldown window.

    `_fire_and_forget` is stubbed (autouse, so every test in this file gets it,
    not just ones using the `client` fixture below - `TestRegenerateAccessToken`
    builds its own raw `TestClient`/app) to just close the coroutine instead of
    scheduling it: a real `asyncio.create_task` here would open a DB session
    against the real app database. The failed-auth alert's own cooldown/counting
    logic is covered directly by `TestRecordFailedAuth` instead."""
    access_control._failed_auth_count = 0
    access_control._last_failed_auth_alert_at = None
    monkeypatch.setattr(access_control, "_fire_and_forget", lambda coro: coro.close())
    yield
    access_control._failed_auth_count = 0
    access_control._last_failed_auth_alert_at = None


@pytest.fixture
def client(monkeypatch):
    """A minimal app with one route behind the real dependency, and a fixed,
    known token (bypassing the file-backed lru_cache'd token source, which is
    an I/O edge orthogonal to the verification logic under test)."""
    monkeypatch.setattr(access_control, "get_access_token", lambda: KNOWN_TOKEN)

    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(verify_access_token)])
    async def protected():
        return {"ok": True}

    return TestClient(app)


def test_valid_bearer_token_is_accepted(client):
    response = client.get("/protected", headers={"Authorization": f"Bearer {KNOWN_TOKEN}"})

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_missing_authorization_header_is_rejected(client):
    response = client.get("/protected")

    assert response.status_code == 401


def test_wrong_token_is_rejected(client):
    response = client.get("/protected", headers={"Authorization": "Bearer wrong-token"})

    assert response.status_code == 401


def test_missing_bearer_prefix_is_rejected(client):
    response = client.get("/protected", headers={"Authorization": KNOWN_TOKEN})

    assert response.status_code == 401


def test_bearer_prefix_is_case_insensitive(client):
    response = client.get("/protected", headers={"Authorization": f"bearer {KNOWN_TOKEN}"})

    assert response.status_code == 200


def test_empty_bearer_token_is_rejected(client):
    response = client.get("/protected", headers={"Authorization": "Bearer "})

    assert response.status_code == 401


def test_token_as_query_param_is_not_accepted(client):
    # verify_access_token only reads the Authorization header; a token
    # leaked into a query string/URL (logs, browser history, referrers)
    # must not work as a bypass.
    response = client.get(f"/protected?token={KNOWN_TOKEN}")

    assert response.status_code == 401


def test_missing_and_wrong_token_return_the_same_error_detail(client):
    # Intentional: the 401 message doesn't distinguish "no header" from
    # "wrong token" so it can't be used as an oracle to probe for a partially
    # correct token or to distinguish an unset vs. misconfigured deployment.
    missing = client.get("/protected")
    wrong = client.get("/protected", headers={"Authorization": "Bearer wrong-token"})

    assert missing.status_code == wrong.status_code == 401
    assert missing.json()["detail"] == wrong.json()["detail"]


def _track_and_close(calls: list) -> Callable:
    """`_fire_and_forget` stub: record the coroutine without scheduling it (a
    real `asyncio.create_task` would open a DB session), closing it immediately
    to avoid a 'coroutine was never awaited' warning."""

    def _stub(coro):
        calls.append(coro)
        coro.close()

    return _stub


class TestRecordFailedAuth:
    """`_record_failed_auth`'s cooldown/counting logic, tested directly rather
    than through HTTP - `_fire_and_forget` is stubbed to record calls instead
    of scheduling a real task, since a real one would open a DB session."""

    def test_first_failure_fires_immediately_with_count_one(self, monkeypatch):
        calls = []
        monkeypatch.setattr(access_control, "_fire_and_forget", _track_and_close(calls))

        access_control._record_failed_auth()

        assert len(calls) == 1

    def test_repeated_failures_within_cooldown_fire_only_once(self, monkeypatch):
        calls = []
        monkeypatch.setattr(access_control, "_fire_and_forget", _track_and_close(calls))

        for _ in range(5):
            access_control._record_failed_auth()

        assert len(calls) == 1

    def test_failure_after_cooldown_expires_fires_again(self, monkeypatch):
        # Rather than mock time.monotonic (a process-global clock asyncio's own
        # loop also relies on), simulate elapsed time the same way
        # tests/core/test_release_check.py does: wind the module's own last-fired
        # timestamp back by more than the cooldown window.
        calls = []
        monkeypatch.setattr(access_control, "_fire_and_forget", _track_and_close(calls))

        access_control._record_failed_auth()
        access_control._last_failed_auth_alert_at -= (
            access_control._FAILED_AUTH_ALERT_COOLDOWN_SECONDS + 1
        )
        access_control._record_failed_auth()

        assert len(calls) == 2

    def test_count_resets_after_each_fired_alert(self, monkeypatch):
        # `_fire_and_forget` is stubbed to capture the coroutine instead of
        # scheduling a real asyncio.Task (which needs a running loop this
        # plain sync test doesn't have) - each captured coroutine is awaited
        # manually below, driving `_raise_failed_auth_alert` (itself stubbed
        # to just record its `count` argument) the same as the real task would.
        captured = []
        monkeypatch.setattr(access_control, "_fire_and_forget", captured.append)

        counts = []

        async def fake_raise_failed_auth_alert(count):
            counts.append(count)

        monkeypatch.setattr(
            access_control, "_raise_failed_auth_alert", fake_raise_failed_auth_alert
        )

        access_control._record_failed_auth()  # count=1, fires immediately
        access_control._record_failed_auth()  # count=2, suppressed
        access_control._record_failed_auth()  # count=3, suppressed
        access_control._last_failed_auth_alert_at -= (
            access_control._FAILED_AUTH_ALERT_COOLDOWN_SECONDS + 1
        )
        access_control._record_failed_auth()  # cooldown expired, fires with count=3

        assert len(captured) == 2

        async def _await_all():
            await asyncio.gather(*captured)

        _run(_await_all())

        assert counts == [1, 3]


class TestRegenerateAccessToken:
    @pytest.fixture(autouse=True)
    def _reset_cache(self):
        # get_access_token is a process-wide lru_cache; leaving a test-generated
        # token cached would leak into unrelated tests running later.
        yield
        access_control.get_access_token.cache_clear()

    def test_raises_when_env_var_pins_a_fixed_token(self, monkeypatch):
        monkeypatch.setattr(settings.api, "access_token", "fixed-from-env")

        with pytest.raises(AccessTokenFixedError):
            regenerate_access_token()

    def test_generates_and_persists_a_new_token(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings.api, "access_token", "")
        monkeypatch.setattr(settings, "data_dir", str(tmp_path))
        access_control.get_access_token.cache_clear()

        new_token = regenerate_access_token()

        assert new_token
        assert (tmp_path / ".access_token").read_text() == new_token

    def test_invalidates_the_cached_token_immediately(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings.api, "access_token", "")
        monkeypatch.setattr(settings, "data_dir", str(tmp_path))
        access_control.get_access_token.cache_clear()
        old_token = access_control.get_access_token()

        new_token = regenerate_access_token()

        assert access_control.get_access_token() == new_token
        assert new_token != old_token

    def test_old_token_is_rejected_and_new_token_accepted_after_regeneration(
        self, tmp_path, monkeypatch
    ):
        # Build a fresh app rather than using the `client` fixture above: that
        # fixture stubs get_access_token to a fixed value, which would break
        # regenerate_access_token's own `get_access_token.cache_clear()` call.
        monkeypatch.setattr(settings.api, "access_token", "")
        monkeypatch.setattr(settings, "data_dir", str(tmp_path))
        access_control.get_access_token.cache_clear()
        old_token = access_control.get_access_token()

        app = FastAPI()

        @app.get("/protected", dependencies=[Depends(verify_access_token)])
        async def protected():
            return {"ok": True}

        real_client = TestClient(app)
        new_token = regenerate_access_token()

        old_response = real_client.get(
            "/protected", headers={"Authorization": f"Bearer {old_token}"}
        )
        new_response = real_client.get(
            "/protected", headers={"Authorization": f"Bearer {new_token}"}
        )

        assert old_response.status_code == 401
        assert new_response.status_code == 200
