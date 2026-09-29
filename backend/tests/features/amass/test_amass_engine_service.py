"""asyncio.create_subprocess_exec (for both `amass engine` and the `ae_isready`
readiness probe) is monkeypatched directly, so these tests focus on
ensure_engine_ready's own state machine: not-installed short-circuit, reusing an
already-ready engine without spawning a second one, starting it when not
running, and surfacing (never raising) a failure to become ready."""

import asyncio

from app.features.amass.service import amass_engine_service as svc


def _run(coro):
    return asyncio.run(coro)


class _FakeProcess:
    def __init__(self):
        self.returncode = None
        self.pid = 777
        self.terminated = False
        self.killed = False

    def terminate(self):
        self.terminated = True
        self.returncode = 0

    def kill(self):
        self.killed = True
        self.returncode = -9

    async def wait(self):
        return self.returncode


def _reset_module_state():
    svc._engine_process = None
    svc._start_lock = asyncio.Lock()


class TestEnsureEngineReady:
    def setup_method(self):
        _reset_module_state()

    def teardown_method(self):
        _reset_module_state()

    def test_returns_false_when_amass_is_not_installed(self, monkeypatch):
        monkeypatch.setattr(svc, "is_amass_available", lambda: False)

        assert _run(svc.ensure_engine_ready()) is False

    def test_spawns_the_engine_and_waits_for_it_to_become_ready(self, monkeypatch):
        spawned = []

        async def fake_create_subprocess_exec(*args, **kwargs):
            spawned.append(args)
            return _FakeProcess()

        monkeypatch.setattr(svc, "is_amass_available", lambda: True)
        monkeypatch.setattr(svc.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
        monkeypatch.setattr(svc, "_is_engine_ready", _make_ready_sequence([False, True]))
        monkeypatch.setattr(svc, "ENGINE_READY_POLL_SECONDS", 0.01)

        assert _run(svc.ensure_engine_ready()) is True
        assert spawned == [(svc.BINARY_NAME, "engine")]

    def test_does_not_spawn_a_second_engine_when_already_ready(self, monkeypatch):
        spawn_count = 0

        async def fake_create_subprocess_exec(*args, **kwargs):
            nonlocal spawn_count
            spawn_count += 1
            return _FakeProcess()

        monkeypatch.setattr(svc, "is_amass_available", lambda: True)
        monkeypatch.setattr(svc.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
        monkeypatch.setattr(svc, "_is_engine_ready", _make_ready_sequence([True]))
        svc._engine_process = _FakeProcess()

        assert _run(svc.ensure_engine_ready()) is True
        assert spawn_count == 0

    def test_returns_false_when_the_engine_never_becomes_ready(self, monkeypatch):
        monkeypatch.setattr(svc, "is_amass_available", lambda: True)

        async def fake_create_subprocess_exec(*args, **kwargs):
            return _FakeProcess()

        monkeypatch.setattr(svc.asyncio, "create_subprocess_exec", fake_create_subprocess_exec)
        monkeypatch.setattr(svc, "_is_engine_ready", _make_ready_sequence([False]))
        monkeypatch.setattr(svc, "ENGINE_READY_TIMEOUT_SECONDS", 0.02)
        monkeypatch.setattr(svc, "ENGINE_READY_POLL_SECONDS", 0.01)

        assert _run(svc.ensure_engine_ready()) is False


def _make_ready_sequence(results: list[bool]):
    """Returns an async fn yielding each of `results` in order, then repeats the
    last one - lets a test express "not ready yet, then ready" or "never ready"."""

    async def _is_ready():
        value = results.pop(0) if len(results) > 1 else results[0]
        return value

    return _is_ready


class TestStopEngine:
    def setup_method(self):
        _reset_module_state()

    def teardown_method(self):
        _reset_module_state()

    def test_is_a_noop_when_never_started(self):
        _run(svc.stop_engine())  # must not raise
        assert svc._engine_process is None

    def test_terminates_a_running_process(self):
        process = _FakeProcess()
        svc._engine_process = process

        _run(svc.stop_engine())

        assert process.terminated is True
        assert svc._engine_process is None

    def test_force_kills_if_terminate_does_not_stop_it_in_time(self, monkeypatch):
        class _StubbornProcess(_FakeProcess):
            def terminate(self):
                self.terminated = True
                # returncode stays None - simulates a process that ignores SIGTERM

            async def wait(self):
                if not self.killed:
                    await asyncio.sleep(999)
                return self.returncode

        process = _StubbornProcess()
        svc._engine_process = process
        monkeypatch.setattr(asyncio, "wait_for", _make_fast_timeout_wait_for())

        _run(svc.stop_engine())

        assert process.killed is True


def _make_fast_timeout_wait_for():
    """Replaces asyncio.wait_for with a variant that treats any call as an
    immediate timeout - stop_engine()'s own `timeout=10` grace period would
    otherwise make this test wait for real."""
    real_wait_for = asyncio.wait_for

    async def _fast_wait_for(awaitable, timeout):
        return await real_wait_for(awaitable, timeout=0.01)

    return _fast_wait_for


class TestIsAmassAvailable:
    def test_true_only_when_both_binaries_are_present(self, monkeypatch):
        present = {"amass", "ae_isready"}
        monkeypatch.setattr(svc, "is_binary_available", lambda name: name in present)
        assert svc.is_amass_available() is True

        present.discard("ae_isready")
        assert svc.is_amass_available() is False
