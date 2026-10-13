"""user_scanner_service: how each module's `Result` maps onto our events/rows, and run_scan's
guards. The real package and network are replaced with a fake `user_scanner`; ScanRun's own
lifecycle is covered by tests/core/scans/test_run.py (same split as the mailcat service tests)."""

import asyncio
import contextlib
import enum
import sys
import types
from types import SimpleNamespace

import pytest

from app.core.scans.run import ScanCancelled, ScanRun
from app.features.email_search.models.email_search_models import MailSearch
from app.features.email_search.service import user_scanner_service as svc


def _run(coro):
    return asyncio.run(coro)


class _Status(enum.Enum):
    TAKEN = 0
    AVAILABLE = 1
    ERROR = 2
    SKIPPED = 3


def _result(status, **kw):
    defaults = dict(
        site_name="Etsy",
        category="shopping",
        url="https://etsy.test",
        extra={},
        media={},
        reason=None,
    )
    return SimpleNamespace(status=status, **{**defaults, **kw})


@pytest.fixture
def fake_package(monkeypatch):
    """A stand-in `user_scanner` whose `engine.check` returns whatever `behaviour[module name]` says
    (a Result, or an exception instance to raise, or a coroutine function to await)."""
    behaviour: dict = {}

    async def check(module, target):
        outcome = behaviour[module.__name__.split(".")[-1]]
        if isinstance(outcome, BaseException):
            raise outcome
        if callable(outcome):
            return await outcome(target)
        return outcome

    pkg = types.ModuleType("user_scanner")
    core = types.ModuleType("user_scanner.core")
    engine = types.ModuleType("user_scanner.core.engine")
    result = types.ModuleType("user_scanner.core.result")
    engine.check = check
    result.Status = _Status
    pkg.core, core.engine, core.result = core, engine, result
    for name, mod in {
        "user_scanner": pkg,
        "user_scanner.core": core,
        "user_scanner.core.engine": engine,
        "user_scanner.core.result": result,
    }.items():
        monkeypatch.setitem(sys.modules, name, mod)
    return behaviour


def _module(name):
    return SimpleNamespace(__name__=f"user_scanner.email_scan.shopping.{name}")


class TestRunModule:
    def _check(self, module, timeout=5):
        return _run(svc._run_module(module, "a@b.test", timeout, asyncio.Semaphore(1)))

    def test_a_registered_account_becomes_a_hit_with_its_profile_fields(self, fake_package):
        fake_package["etsy"] = _result(
            _Status.TAKEN,
            extra={"name": "Ann", "followers": 3},
            media={"avatar": "https://img.test/a.png"},
        )

        outcome = self._check(_module("etsy"))

        assert outcome == {
            "checker_name": "Etsy",
            "status": "registered",
            "provider_name": "Etsy",
            "emails": ["a@b.test"],
            "extra": {
                "category": "shopping",
                "url": "https://etsy.test",
                "fields": {"name": "Ann", "followers": 3},
                "links": {"avatar": "https://img.test/a.png"},
            },
        }

    def test_an_available_address_is_not_registered(self, fake_package):
        fake_package["etsy"] = _result(_Status.AVAILABLE)

        assert self._check(_module("etsy")) == {"checker_name": "Etsy", "status": "not_registered"}

    @pytest.mark.parametrize("status", [_Status.ERROR, _Status.SKIPPED])
    def test_errors_and_skips_are_never_reported_as_not_registered(self, fake_package, status):
        fake_package["etsy"] = _result(status, reason="403")

        assert self._check(_module("etsy")) == {
            "checker_name": "Etsy",
            "status": "error",
            "error": "403",
        }

    def test_a_raised_exception_is_an_error_not_a_crash(self, fake_package):
        fake_package["etsy"] = RuntimeError("boom")

        assert self._check(_module("etsy")) == {
            "checker_name": "etsy",
            "status": "error",
            "error": "boom",
        }

    def test_a_module_that_hangs_is_cut_off_by_the_timeout(self, fake_package):
        async def hang(_target):
            await asyncio.sleep(10)

        fake_package["etsy"] = hang

        outcome = self._check(_module("etsy"), timeout=0.05)

        assert outcome["status"] == "error"

    def test_is_bounded_by_the_semaphore(self, fake_package):
        running = peak = 0

        async def slow(_target):
            nonlocal running, peak
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.01)
            running -= 1
            return _result(_Status.AVAILABLE)

        fake_package["a"] = fake_package["b"] = slow
        semaphore = asyncio.Semaphore(1)

        async def scenario():
            await asyncio.gather(
                svc._run_module(_module("a"), "x@y.test", 5, semaphore),
                svc._run_module(_module("b"), "x@y.test", 5, semaphore),
            )

        _run(scenario())

        assert peak == 1


def _config(**overrides):
    defaults = dict(timeout_seconds=5, max_concurrency=4, proxy_url=None, use_tor=False)
    return SimpleNamespace(**{**defaults, **overrides})


@pytest.fixture
def captured(monkeypatch):
    captured = {}

    async def fake_execute(feature_name, model, run_work, on_event, **kwargs):
        captured.update(feature_name=feature_name, model=model, run_work=run_work, **kwargs)

    monkeypatch.setattr(ScanRun, "execute", fake_execute)

    @contextlib.asynccontextmanager
    async def fake_managed_session():
        yield None

    monkeypatch.setattr(svc, "managed_session", fake_managed_session)
    monkeypatch.setattr(svc, "is_available", lambda: True)
    monkeypatch.setattr(svc, "_configure_package", lambda: None)
    monkeypatch.setattr(svc, "get_runnable_modules", lambda: [_module("etsy"), _module("quora")])

    async def get_config(db):
        return _config()

    monkeypatch.setattr(svc, "get_email_search_config", get_config)
    return captured


def _start(queue=None, email="a@b.test"):
    _run(svc.run_scan(email, queue or asyncio.Queue()))


class TestRunScan:
    def test_creates_a_user_scanner_run_for_the_full_address(self, captured):
        _start()

        assert captured["feature_name"] == "email_search"
        assert captured["model"] is MailSearch
        assert captured["create_fields"] == {"username": "a@b.test", "source": "user_scanner"}
        assert captured["started_fields"] == {"username": "a@b.test", "total_providers": 2}

    def test_reports_progress_and_persists_only_registered_accounts(self, monkeypatch, captured):
        async def fake_run_module(module, email, timeout, semaphore):
            if module.__name__.endswith("etsy"):
                return {
                    "checker_name": "Etsy",
                    "status": "registered",
                    "provider_name": "Etsy",
                    "emails": [email],
                    "extra": {"category": "shopping"},
                }
            return {"checker_name": "Quora", "status": "error", "error": "403"}

        monkeypatch.setattr(svc, "_run_module", fake_run_module)
        queue: asyncio.Queue = asyncio.Queue()
        _start(queue)

        outcome = _run(captured["run_work"](7))

        assert outcome.fields == {
            "total_providers_checked": 2,
            "found_count": 1,
            "error_count": 1,
        }
        events = []
        while not queue.empty():
            events.append(queue.get_nowait())
        progress = [e["data"] for e in events if e and e.get("type") == "progress"]
        assert {p["checker_name"]: p["status"] for p in progress} == {
            "Etsy": "registered",
            "Quora": "error",
        }
        assert all(p["found"] == (p["status"] == "registered") for p in progress)

        persisted = {}

        async def fake_add(db, search_id, found):
            persisted.update(search_id=search_id, found=found)

        monkeypatch.setattr(svc, "add_provider_results", fake_add)
        _run(outcome.persist_children(None))
        assert persisted == {
            "search_id": 7,
            "found": [
                {"provider_name": "Etsy", "emails": ["a@b.test"], "extra": {"category": "shopping"}}
            ],
        }

    @pytest.mark.parametrize(
        "override", [{"use_tor": True}, {"proxy_url": "socks5://127.0.0.1:9050"}]
    )
    def test_refuses_to_run_when_tor_or_a_proxy_is_configured(
        self, monkeypatch, captured, override
    ):
        async def get_config(db):
            return _config(**override)

        monkeypatch.setattr(svc, "get_email_search_config", get_config)
        _start()

        with pytest.raises(RuntimeError, match="Tor/proxy"):
            _run(captured["run_work"](7))

    def test_fails_clearly_when_the_package_is_not_installed(self, monkeypatch, captured):
        monkeypatch.setattr(svc, "is_available", lambda: False)
        _start()

        assert captured["started_fields"]["total_providers"] == 0
        with pytest.raises(RuntimeError, match="not installed"):
            _run(captured["run_work"](7))

    def test_cancellation_keeps_what_was_found_so_far(self, monkeypatch, captured):
        async def slow(module, email, timeout, semaphore):
            await asyncio.sleep(10)

        monkeypatch.setattr(svc, "_run_module", slow)
        _start()

        async def scenario():
            task = asyncio.ensure_future(captured["run_work"](7))
            await asyncio.sleep(0)
            task.cancel()
            with pytest.raises(ScanCancelled) as info:
                await task
            return info.value

        assert _run(scenario()).outcome.fields == {
            "total_providers_checked": 0,
            "found_count": 0,
            "error_count": 0,
        }


def test_configure_package_points_its_settings_file_into_the_data_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("USER_SCANNER_CONFIG", raising=False)
    monkeypatch.setattr(svc.settings, "data_dir", str(tmp_path))

    svc._configure_package()

    import os

    assert os.environ["USER_SCANNER_CONFIG"] == str(tmp_path / "user_scanner_config.json")
