"""_run_subs is exercised against a monkeypatched asyncio.create_subprocess_exec
(text-parsing logic, error/timeout mapping). run_scan_task's own lifecycle
(create running row -> started -> terminal event + mark row) is ScanRun's
concern, covered end to end by tests/core/scans/test_run.py - what's specific to
amass and worth testing here is only what run_scan_task itself builds: the
run_work closure's mapping from amass's output to a ScanOutcome, and that it's
handed to ScanRun.execute() with the right feature_name/model/create_fields/
cancellable, matching test_run_scan_orchestration.py's pattern for git_recon."""

import asyncio

import pytest

from app.core.scans.cancellable import ProcessCancellable
from app.core.scans.run import ScanCancelled, ScanRun
from app.features.amass.models.amass_models import AmassSearch
from app.features.amass.schemas.amass_schemas import AmassHost
from app.features.amass.service import amass_service as svc
from app.features.amass.service.amass_service import AmassError, get_amass_version


def _run(coro):
    return asyncio.run(coro)


class _FakeProcess:
    def __init__(self, stdout: bytes = b"", stderr: bytes = b"", returncode: int = 0, hang=False):
        self._stdout = stdout
        self._stderr = stderr
        # A real subprocess.Process.returncode is None while still running -
        # ProcessCancellable.cancel() relies on exactly that to decide whether
        # there's anything left to terminate.
        self.returncode = None if hang else returncode
        self._hang = hang
        self.pid = 4242
        self.terminated = False
        self.killed = False
        self.waited = False

    async def communicate(self):
        if self._hang:
            await asyncio.sleep(999)
        return self._stdout, self._stderr

    async def wait(self):
        if self._hang:
            await asyncio.sleep(999)
        self.waited = True
        return self.returncode

    def terminate(self):
        self.terminated = True
        self._hang = False
        self.returncode = 0

    def kill(self):
        self.killed = True
        self._hang = False
        self.returncode = -9


class TestRunSubs:
    def _patch(self, monkeypatch, process: _FakeProcess):
        async def fake_create_subprocess_exec(*args, **kwargs):
            return process

        monkeypatch.setattr(svc.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    def test_parses_hostname_ip_lines(self, monkeypatch):
        stdout = b"lightning.owasp.org 172.66.157.115\ndocs.owasp.org 2606:4700::6810:fe78\n"
        self._patch(monkeypatch, _FakeProcess(stdout=stdout, returncode=0))

        hosts = _run(svc._run_subs("owasp.org"))

        assert hosts == [
            AmassHost(hostname="lightning.owasp.org", ip="172.66.157.115"),
            AmassHost(hostname="docs.owasp.org", ip="2606:4700::6810:fe78"),
        ]

    def test_treats_no_names_discovered_as_empty(self, monkeypatch):
        self._patch(monkeypatch, _FakeProcess(stdout=b"No names were discovered\n", returncode=0))

        assert _run(svc._run_subs("example.com")) == []

    def test_handles_hostname_without_ip(self, monkeypatch):
        self._patch(monkeypatch, _FakeProcess(stdout=b"example.com\n", returncode=0))

        hosts = _run(svc._run_subs("example.com"))

        assert hosts == [AmassHost(hostname="example.com", ip=None)]

    def test_raises_amass_error_on_nonzero_exit(self, monkeypatch):
        self._patch(monkeypatch, _FakeProcess(stderr=b"boom", returncode=1))

        with pytest.raises(AmassError, match="boom"):
            _run(svc._run_subs("example.com"))

    def test_raises_amass_error_on_timeout(self, monkeypatch):
        process = _FakeProcess(hang=True)
        self._patch(monkeypatch, process)
        monkeypatch.setattr(svc, "SUBS_TIMEOUT_SECONDS", 0.01)

        with pytest.raises(AmassError, match="Timed out"):
            _run(svc._run_subs("example.com"))
        assert process.killed is True


class TestGetAmassVersion:
    def setup_method(self):
        get_amass_version.cache_clear()

    def teardown_method(self):
        get_amass_version.cache_clear()

    def test_delegates_to_cli_tool_version_with_a_custom_regex(self, monkeypatch):
        captured = {}

        def fake_get_cli_tool_version(binary_name, **kwargs):
            captured["binary_name"] = binary_name
            captured.update(kwargs)
            return "v5.1.1"

        monkeypatch.setattr(svc, "get_cli_tool_version", fake_get_cli_tool_version)

        assert get_amass_version() == "v5.1.1"
        assert captured["binary_name"] == "amass"
        assert captured["version_args"] == ("-version",)
        assert captured["version_regex"].search("v5.1.1").group(1) == "v5.1.1"


class TestRunScanTask:
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
        return captured

    def _patch_engine_and_subprocess(self, monkeypatch, *, ready=True, process=None):
        async def fake_ensure_engine_ready():
            return ready

        monkeypatch.setattr(svc, "ensure_engine_ready", fake_ensure_engine_ready)

        if process is not None:

            async def fake_create_subprocess_exec(*args, **kwargs):
                return process

            monkeypatch.setattr(svc.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

    def _start(self, **overrides):
        kwargs = dict(domain="example.com", brute_force=False, queue=asyncio.Queue())
        kwargs.update(overrides)
        _run(svc.run_scan_task(**kwargs))

    def test_hands_scan_run_the_right_feature_name_model_and_fields(self, monkeypatch, captured):
        process = _FakeProcess(returncode=0)
        self._patch_engine_and_subprocess(monkeypatch, process=process)
        monkeypatch.setattr(svc, "_run_subs", lambda domain: asyncio.sleep(0, result=[]))

        self._start(domain="example.com", brute_force=True)

        assert captured["feature_name"] == "amass"
        assert captured["model"] is AmassSearch
        assert captured["create_fields"] == {"domain": "example.com", "brute_force": True}
        assert captured["started_fields"] == {"domain": "example.com", "brute_force": True}
        assert isinstance(captured["cancellable"], ProcessCancellable)

    def test_run_work_maps_hosts_found_into_a_scan_outcome(self, monkeypatch, captured):
        process = _FakeProcess(returncode=0)
        self._patch_engine_and_subprocess(monkeypatch, process=process)
        hosts = [AmassHost(hostname="a.example.com", ip="1.2.3.4")]
        monkeypatch.setattr(svc, "_run_subs", lambda domain: asyncio.sleep(0, result=hosts))

        self._start()
        outcome = _run(captured["run_work"](123))

        assert outcome.fields == {"hosts_found": 1}
        assert outcome.db_only_fields["result"] == {
            "hosts": [{"hostname": "a.example.com", "ip": "1.2.3.4"}]
        }

    def test_run_work_raises_scan_cancelled_once_the_cancellable_was_triggered(
        self, monkeypatch, captured
    ):
        process = _FakeProcess(returncode=0)
        self._patch_engine_and_subprocess(monkeypatch, process=process)
        monkeypatch.setattr(svc, "_run_subs", lambda domain: asyncio.sleep(0, result=[]))

        self._start()
        captured["cancellable"].cancelled = True

        with pytest.raises(ScanCancelled) as exc_info:
            _run(captured["run_work"](123))
        assert exc_info.value.outcome.fields == {"hosts_found": 0}

    def test_wall_clock_timeout_cancels_the_process_and_still_reports_partial_results(
        self, monkeypatch, captured
    ):
        process = _FakeProcess(hang=True)
        self._patch_engine_and_subprocess(monkeypatch, process=process)
        monkeypatch.setattr(svc, "WALL_CLOCK_TIMEOUT_SECONDS", 0.01)
        hosts = [AmassHost(hostname="partial.example.com", ip=None)]
        monkeypatch.setattr(svc, "_run_subs", lambda domain: asyncio.sleep(0, result=hosts))

        self._start()

        with pytest.raises(ScanCancelled) as exc_info:
            _run(captured["run_work"](123))
        assert process.terminated is True
        assert exc_info.value.outcome.fields == {"hosts_found": 1}

    def test_engine_unavailable_uses_a_raising_run_work_and_spawns_no_subprocess(
        self, monkeypatch, captured
    ):
        calls = []

        async def fake_create_subprocess_exec(*args, **kwargs):
            calls.append(args)
            raise AssertionError("should not spawn a subprocess")

        self._patch_engine_and_subprocess(monkeypatch, ready=False)
        monkeypatch.setattr(svc.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)

        self._start()

        assert calls == []
        assert "cancellable" not in captured
        with pytest.raises(AmassError, match="not available"):
            _run(captured["run_work"](123))
