"""_run_checker/_normalize_emails/_kill_orphaned_chromium's own mapping and
cleanup logic, plus run_scan's orchestration (mode dispatch into ScanRun.execute
- its own lifecycle is ScanRun's concern, covered end to end by
tests/core/scans/test_run.py, same split as git_recon's
test_run_scan_orchestration.py). The real mailcat checkers/psutil process tree
are mocked out - only this module's own glue is under test.
"""

import asyncio
import contextlib
from types import SimpleNamespace

import pytest

from app.core.scans.run import ScanCancelled
from app.features.email_search.models.email_search_models import MailSearch
from app.features.email_search.service import email_search_service as svc
from app.features.email_search.service.email_search_service import (
    _kill_orphaned_chromium,
    _normalize_emails,
    _run_checker,
    cancel_scan,
)


def _run(coro):
    return asyncio.run(coro)


class TestNormalizeEmails:
    def test_wraps_a_single_string_in_a_list(self):
        assert _normalize_emails("a@example.com") == ["a@example.com"]

    def test_leaves_a_list_as_is(self):
        assert _normalize_emails(["a@example.com", "b@example.com"]) == [
            "a@example.com",
            "b@example.com",
        ]

    def test_converts_other_iterables_to_a_list(self):
        assert _normalize_emails(("a@example.com",)) == ["a@example.com"]


class TestRunChecker:
    async def _checker_returning(self, value):
        async def checker(username, req_session_fun, timeout):
            return value

        checker.__name__ = "fake_checker"
        return checker

    def test_maps_a_plain_dict_result_to_a_found_entry(self, monkeypatch):
        monkeypatch.setattr(svc, "_kill_orphaned_chromium", lambda before_pids: None)

        async def checker(username, req_session_fun, timeout):
            return {"gmail": "user@gmail.com"}

        checker.__name__ = "gmail_checker"

        result = _run(_run_checker(checker, "user", None, 5, asyncio.Semaphore(1)))

        assert result == {
            "checker_name": "gmail_checker",
            "found": True,
            "provider_name": "gmail",
            "emails": ["user@gmail.com"],
            "error": None,
        }

    def test_maps_an_smtp_style_tuple_result_carrying_an_error_alongside_a_hit(self, monkeypatch):
        monkeypatch.setattr(svc, "_kill_orphaned_chromium", lambda before_pids: None)

        async def checker(username, req_session_fun, timeout):
            return ({"yandex": ["user@yandex.com"]}, "partial SMTP response")

        checker.__name__ = "yandex_checker"

        result = _run(_run_checker(checker, "user", None, 5, asyncio.Semaphore(1)))

        assert result == {
            "checker_name": "yandex_checker",
            "found": True,
            "provider_name": "yandex",
            "emails": ["user@yandex.com"],
            "error": "partial SMTP response",
        }

    def test_maps_a_falsy_result_to_not_found(self, monkeypatch):
        monkeypatch.setattr(svc, "_kill_orphaned_chromium", lambda before_pids: None)

        async def checker(username, req_session_fun, timeout):
            return None

        checker.__name__ = "empty_checker"

        result = _run(_run_checker(checker, "user", None, 5, asyncio.Semaphore(1)))

        assert result == {"checker_name": "empty_checker", "found": False, "error": None}

    def test_a_raised_exception_is_caught_and_mapped_to_not_found_with_the_error(self, monkeypatch):
        monkeypatch.setattr(svc, "_kill_orphaned_chromium", lambda before_pids: None)

        async def checker(username, req_session_fun, timeout):
            raise RuntimeError("checker blew up")

        checker.__name__ = "broken_checker"

        result = _run(_run_checker(checker, "user", None, 5, asyncio.Semaphore(1)))

        assert result == {
            "checker_name": "broken_checker",
            "found": False,
            "error": "checker blew up",
        }

    def test_always_runs_the_chromium_cleanup_even_when_the_checker_fails(self, monkeypatch):
        cleanup_calls = []
        monkeypatch.setattr(
            svc, "_kill_orphaned_chromium", lambda before_pids: cleanup_calls.append(1)
        )

        async def checker(username, req_session_fun, timeout):
            raise RuntimeError("boom")

        checker.__name__ = "broken_checker"

        _run(_run_checker(checker, "user", None, 5, asyncio.Semaphore(1)))

        assert cleanup_calls == [1]

    def test_is_bounded_by_the_given_semaphore(self, monkeypatch):
        monkeypatch.setattr(svc, "_kill_orphaned_chromium", lambda before_pids: None)
        semaphore = asyncio.Semaphore(1)
        concurrent = 0
        max_concurrent = 0

        async def checker(username, req_session_fun, timeout):
            nonlocal concurrent, max_concurrent
            concurrent += 1
            max_concurrent = max(max_concurrent, concurrent)
            await asyncio.sleep(0.01)
            concurrent -= 1
            return None

        checker.__name__ = "slow_checker"

        async def _scenario():
            await asyncio.gather(
                _run_checker(checker, "user", None, 5, semaphore),
                _run_checker(checker, "user", None, 5, semaphore),
            )

        _run(_scenario())
        assert max_concurrent == 1


class TestKillOrphanedChromium:
    def test_kills_a_new_chromium_shaped_child_process(self, monkeypatch):
        killed = []
        chromium_child = SimpleNamespace(
            pid=999, name=lambda: "chrome", kill=lambda: killed.append(999)
        )
        other_child = SimpleNamespace(
            pid=888, name=lambda: "python", kill=lambda: killed.append(888)
        )

        fake_process = SimpleNamespace(
            children=lambda recursive=True: [chromium_child, other_child]
        )
        monkeypatch.setattr(svc.psutil, "Process", lambda: fake_process)

        _kill_orphaned_chromium(before_pids=set())

        assert killed == [999]

    def test_skips_a_child_that_already_existed_before_the_checker_ran(self, monkeypatch):
        killed = []
        chromium_child = SimpleNamespace(
            pid=999, name=lambda: "chrome", kill=lambda: killed.append(999)
        )
        fake_process = SimpleNamespace(children=lambda recursive=True: [chromium_child])
        monkeypatch.setattr(svc.psutil, "Process", lambda: fake_process)

        _kill_orphaned_chromium(before_pids={999})

        assert killed == []

    def test_swallows_a_psutil_error_without_raising(self, monkeypatch):
        def _raise():
            raise svc.psutil.Error("boom")

        monkeypatch.setattr(svc.psutil, "Process", _raise)

        _kill_orphaned_chromium(before_pids=set())  # must not raise


class TestCancelScan:
    def test_delegates_to_scan_run_cancel_with_the_feature_name(self, monkeypatch):
        captured = {}

        async def fake_cancel(feature_name, search_id):
            captured["feature_name"] = feature_name
            captured["search_id"] = search_id
            return True

        monkeypatch.setattr(svc.ScanRun, "cancel", fake_cancel)

        assert _run(cancel_scan(42)) is True
        assert captured == {"feature_name": "email_search", "search_id": 42}


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

        monkeypatch.setattr(svc.ScanRun, "execute", fake_execute)

        @contextlib.asynccontextmanager
        async def fake_managed_session():
            yield None

        monkeypatch.setattr(svc, "managed_session", fake_managed_session)

        async def fake_get_config(db):
            return _fake_config()

        monkeypatch.setattr(svc, "get_email_search_config", fake_get_config)
        return captured

    def _start(self, username="alice", queue=None):
        _run(svc.run_scan(username, queue or asyncio.Queue()))

    def test_hands_scan_run_the_right_feature_name_model_and_fields(self, monkeypatch, captured):
        checker_a, checker_b = _make_checkers(2)
        monkeypatch.setattr(
            svc, "get_active_checkers", lambda smtp, headless: [checker_a, checker_b]
        )

        self._start(username="alice")

        assert captured["feature_name"] == "email_search"
        assert captured["model"] is MailSearch
        assert captured["create_fields"] == {"username": "alice"}
        assert captured["started_fields"] == {"username": "alice", "total_providers": 2}

    def test_run_work_reports_progress_and_collects_found_providers(self, monkeypatch, captured):
        checker_a, checker_b = _make_checkers(2)
        monkeypatch.setattr(
            svc, "get_active_checkers", lambda smtp, headless: [checker_a, checker_b]
        )
        monkeypatch.setattr(
            svc,
            "_run_checker",
            _fake_run_checker(
                {
                    "checker_a": {
                        "checker_name": "checker_a",
                        "found": True,
                        "provider_name": "gmail",
                        "emails": ["a@gmail.com"],
                    },
                    "checker_b": {"checker_name": "checker_b", "found": False, "error": None},
                }
            ),
        )
        self._start()

        outcome = _run(captured["run_work"](7))

        assert outcome.fields == {"total_providers_checked": 2, "found_count": 1}

    def test_run_work_persists_found_providers_via_persist_children(self, monkeypatch, captured):
        checker_a, checker_b = _make_checkers(2)
        monkeypatch.setattr(
            svc, "get_active_checkers", lambda smtp, headless: [checker_a, checker_b]
        )
        monkeypatch.setattr(
            svc,
            "_run_checker",
            _fake_run_checker(
                {
                    "checker_a": {
                        "checker_name": "checker_a",
                        "found": True,
                        "provider_name": "gmail",
                        "emails": ["a@gmail.com"],
                    },
                    "checker_b": {"checker_name": "checker_b", "found": False, "error": None},
                }
            ),
        )
        self._start()
        outcome = _run(captured["run_work"](7))

        persisted = {}

        async def fake_add_provider_results(db, search_id, found_providers):
            persisted["search_id"] = search_id
            persisted["found_providers"] = found_providers

        monkeypatch.setattr(svc, "add_provider_results", fake_add_provider_results)
        _run(outcome.persist_children(None))

        assert persisted == {
            "search_id": 7,
            "found_providers": [{"provider_name": "gmail", "emails": ["a@gmail.com"]}],
        }

    def test_run_work_raises_scan_cancelled_with_partial_results_on_cancellation(
        self, monkeypatch, captured
    ):
        checker_a, checker_b = _make_checkers(2)
        monkeypatch.setattr(
            svc, "get_active_checkers", lambda smtp, headless: [checker_a, checker_b]
        )

        async def slow_run_checker(checker, username, req_session_fun, timeout, semaphore):
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


def _fake_config(**overrides):
    defaults = dict(
        timeout_seconds=5,
        max_concurrency=4,
        proxy_url=None,
        use_tor=False,
        enable_smtp_checks=False,
        enable_headless_checks=False,
    )
    return SimpleNamespace(**{**defaults, **overrides})


def _make_checkers(count):
    checkers = []
    for i in range(count):

        async def checker(username, req_session_fun, timeout):
            return None

        checker.__name__ = f"checker_{chr(ord('a') + i)}"
        checkers.append(checker)
    return checkers


def _fake_run_checker(results_by_name):
    async def _run_checker(checker, username, req_session_fun, timeout, semaphore):
        return results_by_name[checker.__name__]

    return _run_checker
