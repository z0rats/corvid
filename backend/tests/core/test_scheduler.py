"""Characterizes the generic scheduler primitives in core/scheduler.py
(add_recurring_job/configure_recurring_job/wrap_job_errors) and locks in the
dependency inversion: core/scheduler.py must stay feature-agnostic, with
per-feature job wiring living in app/utils/scheduler_registry.py instead
(same pattern as app/utils/router_registry.py for routers).
"""

import ast
import asyncio
import inspect

import pytest
from apscheduler.triggers.interval import IntervalTrigger

import app.core.scheduler as scheduler_module
from app.core.scheduler import (
    add_recurring_job,
    configure_recurring_job,
    get_scheduler,
    wrap_job_errors,
)

FORBIDDEN_IMPORT_PREFIXES = ("app.features", "app.core.settings")


@pytest.fixture(autouse=True)
def reset_scheduler():
    scheduler_module._scheduler = None
    yield
    scheduler_module._scheduler = None


async def _noop() -> None:
    return None


class TestAddRecurringJob:
    def test_adds_job_with_expected_id_and_trigger(self):
        add_recurring_job("job_a", _noop, interval=5, unit="minutes")

        jobs = get_scheduler().get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "job_a"
        assert isinstance(jobs[0].trigger, IntervalTrigger)

    def test_repeated_call_with_same_id_replaces_instead_of_duplicating(self):
        # replace_existing only takes effect once a job is actually committed to the
        # jobstore, which APScheduler defers to start() for a not-yet-running
        # scheduler (pre-start add_job calls just queue onto a pending list) — so this
        # needs a started (paused, so nothing actually fires) scheduler to exercise it.
        async def _scenario():
            scheduler = get_scheduler()
            scheduler.start(paused=True)
            try:
                add_recurring_job("job_a", _noop, interval=5, unit="minutes")
                add_recurring_job("job_a", _noop, interval=10, unit="hours")
                return scheduler.get_jobs()
            finally:
                scheduler.shutdown(wait=False)

        jobs = asyncio.run(_scenario())
        assert len(jobs) == 1
        assert jobs[0].id == "job_a"


class TestConfigureRecurringJob:
    def test_enabled_false_removes_existing_job(self):
        add_recurring_job("job_b", _noop, interval=5, unit="minutes")

        configure_recurring_job("job_b", _noop, enabled=False, interval=5, unit="minutes")

        assert get_scheduler().get_jobs() == []

    def test_enabled_true_adds_job(self):
        configure_recurring_job("job_c", _noop, enabled=True, interval=15, unit="minutes")

        jobs = get_scheduler().get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "job_c"

    def test_enabled_true_reconfigures_existing_job(self):
        add_recurring_job("job_d", _noop, interval=5, unit="minutes")

        configure_recurring_job("job_d", _noop, enabled=True, interval=2, unit="hours")

        jobs = get_scheduler().get_jobs()
        assert len(jobs) == 1
        assert jobs[0].id == "job_d"


class TestWrapJobErrors:
    def test_exception_is_logged_and_swallowed(self, caplog):
        async def _boom() -> None:
            raise ValueError("kaboom")

        wrapped = wrap_job_errors("test job", _boom)

        with caplog.at_level("ERROR"):
            asyncio.run(wrapped())

        assert "Error in test job job" in caplog.text
        assert "kaboom" in caplog.text

    def test_success_path_does_not_log_error(self, caplog):
        async def _ok() -> None:
            return None

        wrapped = wrap_job_errors("test job", _ok)

        with caplog.at_level("ERROR"):
            asyncio.run(wrapped())

        assert caplog.text == ""


class TestDependencyInversion:
    def test_no_feature_or_feature_settings_imports(self):
        source = inspect.getsource(scheduler_module)
        tree = ast.parse(source)

        imported_modules = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.append(node.module)

        violations = [
            module for module in imported_modules if module.startswith(FORBIDDEN_IMPORT_PREFIXES)
        ]
        assert violations == [], (
            f"core/scheduler.py must stay feature-agnostic, found: {violations}"
        )
