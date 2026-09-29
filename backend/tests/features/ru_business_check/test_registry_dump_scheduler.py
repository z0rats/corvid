"""registry_dump_scheduler_service: refreshes of one dump never overlap (the startup
catch-up and the scheduled job can fire together), and the lock spans the commit."""

import asyncio
import contextlib
import datetime

from app.features.ru_business_check.service import registry_dump_scheduler_service as svc


def _job(refresh, source="test-source"):
    return svc.DumpJob(source, "test dump", refresh, datetime.timedelta(days=1), 1)


def _patch_session(monkeypatch, events):
    @contextlib.asynccontextmanager
    async def fake_session():
        yield object()
        events.append("commit")

    monkeypatch.setattr(svc, "managed_session", fake_session)


def test_a_refresh_already_running_for_the_same_source_makes_the_second_a_no_op(monkeypatch):
    events: list[str] = []
    _patch_session(monkeypatch, events)
    release = asyncio.Event()

    async def slow_refresh(db):
        events.append("refresh started")
        await release.wait()
        return {"rows": 1}

    job = _job(slow_refresh)

    async def go():
        first = asyncio.create_task(svc.run_refresh(job))
        await asyncio.sleep(0)  # let the first take the lock
        second = await svc.run_refresh(job)
        release.set()
        return await first, second

    first, second = asyncio.run(go())
    assert first == {"rows": 1}
    assert second is None
    assert events == ["refresh started", "commit"]


def test_the_lock_is_held_until_the_transaction_committed(monkeypatch):
    events: list[str] = []
    _patch_session(monkeypatch, events)
    lock_states: list[bool] = []

    async def refresh(db):
        return {"rows": 1}

    job = _job(refresh, source="commit-source")

    @contextlib.asynccontextmanager
    async def observing_session():
        yield object()
        lock_states.append(svc.refresh_lock(job.source).locked())

    monkeypatch.setattr(svc, "managed_session", observing_session)
    asyncio.run(svc.run_refresh(job))
    assert lock_states == [True]


def test_different_sources_refresh_independently(monkeypatch):
    events: list[str] = []
    _patch_session(monkeypatch, events)
    release = asyncio.Event()

    async def slow_refresh(db):
        await release.wait()
        return {"rows": 1}

    async def go():
        first = asyncio.create_task(svc.run_refresh(_job(slow_refresh, "a")))
        await asyncio.sleep(0)
        other = asyncio.create_task(svc.run_refresh(_job(slow_refresh, "b")))
        await asyncio.sleep(0)
        release.set()
        return await first, await other

    assert asyncio.run(go()) == ({"rows": 1}, {"rows": 1})


def test_catch_up_skips_a_fresh_dump_and_survives_a_failing_one(monkeypatch):
    events: list[str] = []
    _patch_session(monkeypatch, events)

    async def is_stale(db, source, max_age):
        return source != "fresh"

    monkeypatch.setattr(svc, "is_stale", is_stale)
    calls: list[str] = []

    async def refresh_ok(db):
        calls.append("ok")
        return {}

    async def refresh_boom(db):
        calls.append("boom")
        raise ValueError("down")

    monkeypatch.setattr(
        svc,
        "dump_jobs",
        lambda: [_job(refresh_boom, "boom"), _job(refresh_ok, "fresh"), _job(refresh_ok, "stale")],
    )
    # "fresh" is skipped; "boom" fails without stopping the loop; "stale" is refreshed.
    asyncio.run(svc.refresh_dumps_if_stale())
    assert calls == ["boom", "ok"]


def test_every_dump_service_has_a_job():
    from app.features.ru_business_check.config.ru_business_check_config import AVAILABLE_SOURCES

    sources = {job.source for job in svc.dump_jobs()}
    assert sources == {"disqualified", "cbr_warning", "ofac_sdn"}
    assert {"disqualified_dump", "cbr_warning", "ofac_sdn"} <= set(AVAILABLE_SOURCES)


def test_replace_dump_refuses_to_run_without_the_sources_lock():
    import pytest

    from app.features.ru_business_check.service.registry_dump_common import (
        DumpSource,
        replace_dump,
    )

    source = DumpSource(
        key="unlocked-source",
        model=object,
        label="test",
        error=ValueError,
        allowed_prefix="https://example.invalid/",
        limit=1,
    )
    with pytest.raises(RuntimeError, match="without holding its refresh_lock"):
        asyncio.run(
            replace_dump(
                object(),
                source,
                [{"x": 1}],
                dump_date=datetime.date(2026, 9, 28),
                valid_until=None,
                url="https://example.invalid/x",
            )
        )
