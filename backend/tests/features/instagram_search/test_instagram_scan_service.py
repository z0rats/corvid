"""run_scan_task's own orchestration logic (session/mode resolution, run_work's
mapping to a ScanOutcome, feature_name/model/create_fields/cancellable plumbing
into ScanRun.execute()) - ScanRun's own lifecycle is covered end to end by
tests/core/scans/test_run.py, and `_scan_sync`'s actual Instaloader iteration
by test_instagram_scan_sync.py; this module mocks both out.
"""

import asyncio

import instaloader
import pytest

from app.core.exceptions import AppHTTPException
from app.core.scans.cancellable import CooperativeCancellable
from app.core.scans.run import ScanCancelled, ScanRun
from app.features.instagram_search.models.instagram_search_models import InstagramSearch
from app.features.instagram_search.service import instagram_scan_service as svc


def _run(coro):
    return asyncio.run(coro)


async def _fake_no_session(db):
    return None


async def _fake_with_session(db):
    return {"sessionid": "abc", "csrftoken": "def", "ds_user_id": "123"}


@pytest.fixture(autouse=True)
def _patch_no_session(monkeypatch):
    monkeypatch.setattr(svc, "get_session_dict", _fake_no_session)


@pytest.fixture
def captured(monkeypatch):
    captured: dict = {}

    async def fake_execute(feature_name, model, run_work, on_event, **kwargs):
        captured.update(
            feature_name=feature_name, model=model, run_work=run_work, on_event=on_event, **kwargs
        )

    monkeypatch.setattr(ScanRun, "execute", fake_execute)
    return captured


def _start(**overrides):
    kwargs = dict(username="someuser", scan_type="followers", db=None, queue=asyncio.Queue())
    kwargs.update(overrides)
    _run(svc.run_scan_task(**kwargs))


class TestRunScanTaskDispatch:
    def test_hands_scan_run_the_right_feature_name_model_and_fields(self, captured):
        _start()

        assert captured["feature_name"] == "instagram_search"
        assert captured["model"] is InstagramSearch
        assert captured["create_fields"] == {
            "scan_type": "followers",
            "username": "someuser",
            "mode": "anonymous",
        }
        assert captured["started_fields"] == captured["create_fields"]
        assert isinstance(captured["cancellable"], CooperativeCancellable)
        assert captured["expected_exceptions"] == (AppHTTPException,)

    def test_resolves_mode_to_session_when_one_is_configured(self, monkeypatch, captured):
        monkeypatch.setattr(svc, "get_session_dict", _fake_with_session)
        _start()

        assert captured["create_fields"]["mode"] == "session"

    def test_run_work_passes_the_session_dict_and_deadline_into_the_sync_call(
        self, monkeypatch, captured
    ):
        monkeypatch.setattr(svc, "get_session_dict", _fake_with_session)
        capture_args = {}

        def fake_scan_sync(scan_type, username, session_data, stop_event, deadline):
            capture_args.update(
                scan_type=scan_type,
                username=username,
                session_data=session_data,
                stop_event=stop_event,
                deadline=deadline,
            )
            return {"items": [], "total_count": None, "truncated": False}

        monkeypatch.setattr(svc, "_scan_sync", fake_scan_sync)
        _start(scan_type="posts")

        _run(captured["run_work"](123))

        assert capture_args["scan_type"] == "posts"
        assert capture_args["username"] == "someuser"
        assert capture_args["session_data"] == {
            "sessionid": "abc",
            "csrftoken": "def",
            "ds_user_id": "123",
        }
        assert capture_args["stop_event"] is captured["cancellable"].stop_event


class TestRunWorkOutcomeMapping:
    def test_maps_a_successful_scan_result_to_a_scan_outcome(self, monkeypatch, captured):
        def fake_scan_sync(*args, **kwargs):
            return {
                "items": [{"username": "a"}, {"username": "b"}],
                "total_count": 2,
                "truncated": False,
            }

        monkeypatch.setattr(svc, "_scan_sync", fake_scan_sync)
        _start()

        outcome = _run(captured["run_work"](123))

        assert outcome.fields == {"item_count": 2, "total_count": 2, "truncated": False}
        assert outcome.db_only_fields == {"result": [{"username": "a"}, {"username": "b"}]}

    def test_run_work_raises_scan_cancelled_once_the_cancellable_was_triggered(
        self, monkeypatch, captured
    ):
        def fake_scan_sync(*args, **kwargs):
            return {"items": [{"username": "a"}], "total_count": None, "truncated": True}

        monkeypatch.setattr(svc, "_scan_sync", fake_scan_sync)
        _start()
        captured["cancellable"].stop_event.set()

        with pytest.raises(ScanCancelled) as exc_info:
            _run(captured["run_work"](123))
        assert exc_info.value.outcome.fields == {
            "item_count": 1,
            "total_count": None,
            "truncated": True,
        }

    def test_run_work_maps_an_instaloader_exception_to_app_http_exception(
        self, monkeypatch, captured
    ):
        def fake_scan_sync(*args, **kwargs):
            raise instaloader.exceptions.LoginRequiredException("login required")

        monkeypatch.setattr(svc, "_scan_sync", fake_scan_sync)
        _start(scan_type="followers")

        with pytest.raises(AppHTTPException) as exc_info:
            _run(captured["run_work"](123))
        assert exc_info.value.status_code == 401
        assert exc_info.value.error_code == "INSTAGRAM_SESSION_REQUIRED"
