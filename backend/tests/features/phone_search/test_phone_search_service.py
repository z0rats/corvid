"""_run_checker's own mapping logic, plus run_scan's orchestration (config lookup,
active-checker list, mode dispatch into ScanRun.execute - its own lifecycle is
ScanRun's concern, covered end to end by tests/core/scans/test_run.py, same split
as email_search's own test_email_search_service.py).
"""

import asyncio
import contextlib
from types import SimpleNamespace

import pytest

from app.core.scans.run import ScanCancelled, ScanRun
from app.features.phone_search.models.phone_search_models import PhoneSearch
from app.features.phone_search.service import phone_search_service as svc
from app.features.phone_search.service.phone_search_service import _run_checker


def _run(coro):
    return asyncio.run(coro)


def _fake_checker(name, *, found=False, error=None, raises=None):
    async def check(phone_number, client, timeout):
        if raises:
            raise raises
        return found

    return SimpleNamespace(PROVIDER_NAME=name, check=check)


class TestRunChecker:
    def test_maps_a_found_result(self):
        checker = _fake_checker("Amazon", found=True)

        result = _run(_run_checker(checker, "+15551234567", None, 5))

        assert result == {"provider_name": "Amazon", "found": True, "error": None}

    def test_maps_a_not_found_result(self):
        checker = _fake_checker("Amazon", found=False)

        result = _run(_run_checker(checker, "+15551234567", None, 5))

        assert result == {"provider_name": "Amazon", "found": False, "error": None}

    def test_a_raised_exception_is_caught_and_mapped_to_not_found_with_the_error(self):
        checker = _fake_checker("Amazon", raises=RuntimeError("checker blew up"))

        result = _run(_run_checker(checker, "+15551234567", None, 5))

        assert result == {
            "provider_name": "Amazon",
            "found": False,
            "error": "checker blew up",
        }


class TestRunScan:
    @pytest.fixture
    def captured(self, monkeypatch):
        captured = {}

        async def fake_execute(feature_name, model, run_work, on_event, **kwargs):
            captured.update(
                feature_name=feature_name,
                model=model,
                run_work=run_work,
                on_event=on_event,
                **kwargs,
            )

        monkeypatch.setattr(ScanRun, "execute", fake_execute)

        @contextlib.asynccontextmanager
        async def fake_managed_session():
            yield None

        monkeypatch.setattr(svc, "managed_session", fake_managed_session)

        async def fake_get_config(db):
            return SimpleNamespace(timeout_seconds=5, proxy_url=None)

        monkeypatch.setattr(svc, "get_phone_search_config", fake_get_config)
        return captured

    def _start(self, phone_number="+15551234567", queue=None):
        _run(svc.run_scan(phone_number, queue or asyncio.Queue()))

    def test_hands_scan_run_the_right_feature_name_model_and_fields(self, monkeypatch, captured):
        checkers = [_fake_checker("Amazon"), _fake_checker("Microsoft")]
        monkeypatch.setattr(svc, "get_active_checkers", lambda: checkers)

        self._start(phone_number="+15551234567")

        assert captured["feature_name"] == "phone_search"
        assert captured["model"] is PhoneSearch
        assert captured["create_fields"] == {"phone_number": "+15551234567"}
        assert captured["started_fields"] == {
            "phone_number": "+15551234567",
            "total_providers": 2,
        }

    def test_run_work_reports_progress_and_collects_found_providers(self, monkeypatch, captured):
        checkers = [_fake_checker("Amazon", found=True), _fake_checker("Microsoft", found=False)]
        monkeypatch.setattr(svc, "get_active_checkers", lambda: checkers)
        self._start()

        outcome = _run(captured["run_work"](7))

        assert outcome.fields == {"total_providers_checked": 2, "found_count": 1}

    def test_run_work_persists_found_providers_via_persist_children(self, monkeypatch, captured):
        checkers = [_fake_checker("Amazon", found=True), _fake_checker("Microsoft", found=False)]
        monkeypatch.setattr(svc, "get_active_checkers", lambda: checkers)
        self._start()
        outcome = _run(captured["run_work"](7))

        persisted = {}

        async def fake_add_provider_results(db, search_id, found_providers):
            persisted["search_id"] = search_id
            persisted["found_providers"] = found_providers

        monkeypatch.setattr(svc, "add_provider_results", fake_add_provider_results)
        _run(outcome.persist_children(None))

        assert persisted == {"search_id": 7, "found_providers": [{"provider_name": "Amazon"}]}

    def test_run_work_raises_scan_cancelled_with_partial_results_on_cancellation(
        self, monkeypatch, captured
    ):
        checkers = [_fake_checker("Amazon"), _fake_checker("Microsoft")]
        monkeypatch.setattr(svc, "get_active_checkers", lambda: checkers)

        async def slow_run_checker(checker, phone_number, client, timeout):
            await asyncio.sleep(10)

        monkeypatch.setattr(svc, "_run_checker", slow_run_checker)
        self._start()

        async def _scenario():
            task = asyncio.ensure_future(captured["run_work"](7))
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(ScanCancelled) as exc_info:
                await task
            return exc_info.value

        exc = _run(_scenario())
        assert exc.outcome.fields == {"total_providers_checked": 0, "found_count": 0}
