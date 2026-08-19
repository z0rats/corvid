"""ScanRun's shared lifecycle (create -> started -> run_work -> terminal event
+ mark row), exercised against real MaigretSearch/MailSearch tables with fake
run_work coroutines and Cancellable adapters - the counterpart to
test_scan_crud.py (which only covers the bare create_running/mark_* helpers
ScanRun itself calls).
"""

import asyncio
import contextlib

import pytest
from sqlalchemy import select

import app.core.scans.run as run_module
from app.core.scans.crud import ScanColumns
from app.core.scans.run import ScanCancelled, ScanEvent, ScanOutcome, ScanRun
from app.features.email_search.models.email_search_models import MailSearch
from app.features.username_search.models.username_search_models import MaigretSearch
from tests.conftest import run as _run

MAIGRET_COLUMNS = ScanColumns(error_column="error_message", completed_at_column="completed_at")


@pytest.fixture
def session_factory(monkeypatch, make_session_factory):
    factory = make_session_factory([MaigretSearch.__table__, MailSearch.__table__])

    @contextlib.asynccontextmanager
    async def fake_managed_session():
        async with factory() as db:
            yield db
            await db.commit()

    monkeypatch.setattr(run_module, "managed_session", fake_managed_session)
    return factory


async def _row(factory, model, row_id):
    async with factory() as db:
        return (await db.execute(select(model).where(model.id == row_id))).scalar_one()


class FakeCancellable:
    """Records whether/when cancel() was awaited, without touching any real
    asyncio task or subprocess - just enough to verify ScanRun.cancel()
    registers/deregisters it and awaits its cancel()."""

    def __init__(self):
        self.cancel_called = False

    async def cancel(self) -> None:
        self.cancel_called = True


class TestExecuteSuccessPath:
    def test_started_then_completed_events_and_row(self, session_factory):
        async def run_work(search_id):
            assert isinstance(search_id, int)
            return ScanOutcome(fields={"total_sites_checked": 5, "found_count": 2})

        events = []

        async def _scenario():
            await ScanRun.execute(
                "username_search",
                MaigretSearch,
                run_work,
                events.append,
                columns=MAIGRET_COLUMNS,
                create_fields={"username": "alice", "source": "maigret"},
                started_fields={"username": "alice", "total_sites": 5},
            )
            return await _row(session_factory, MaigretSearch, events[0].data["search_id"])

        row = _run(_scenario())

        assert [e.type for e in events if e is not None] == ["started", "completed"]
        assert events[-1] is None  # sentinel
        assert events[0].data == {"search_id": row.id, "username": "alice", "total_sites": 5}
        assert events[1].data == {"search_id": row.id, "total_sites_checked": 5, "found_count": 2}
        assert row.status == "completed"
        assert row.total_sites_checked == 5
        assert row.found_count == 2

    def test_db_only_fields_persist_without_appearing_on_the_wire(self, session_factory):
        async def run_work(search_id):
            return ScanOutcome(
                fields={"total_sites_checked": 1, "found_count": 0}, db_only_fields={"tags": ["x"]}
            )

        events = []

        async def _scenario():
            await ScanRun.execute(
                "username_search",
                MaigretSearch,
                run_work,
                events.append,
                columns=MAIGRET_COLUMNS,
                create_fields={"username": "bob", "source": "maigret"},
            )
            return await _row(session_factory, MaigretSearch, events[0].data["search_id"])

        row = _run(_scenario())

        assert "tags" not in events[1].data
        assert row.tags == ["x"]

    def test_registry_is_empty_after_completion(self, session_factory):
        async def run_work(search_id):
            return ScanOutcome()

        async def _scenario():
            await ScanRun.execute(
                "username_search",
                MaigretSearch,
                run_work,
                lambda e: None,
                columns=MAIGRET_COLUMNS,
                create_fields={"username": "carol", "source": "maigret"},
                cancellable=FakeCancellable(),
            )

        _run(_scenario())
        assert not ScanRun._registry


class TestExecuteFailurePath:
    def test_exception_marks_failed_and_emits_failed_event(self, session_factory):
        async def run_work(search_id):
            raise RuntimeError("boom")

        events = []

        async def _scenario():
            await ScanRun.execute(
                "email_search",
                MailSearch,
                run_work,
                events.append,
                columns=MAIGRET_COLUMNS,
                create_fields={"username": "dave"},
            )
            return await _row(session_factory, MailSearch, events[0].data["search_id"])

        row = _run(_scenario())

        assert [e.type for e in events if e is not None] == ["started", "failed"]
        assert events[1].data["error"] == "boom"
        assert row.status == "failed"
        assert row.error_message == "boom"


class TestExecuteCancellation:
    def test_scan_cancelled_exception_marks_cancelled_with_partial_outcome(self, session_factory):
        async def run_work(search_id):
            raise ScanCancelled(ScanOutcome(fields={"total_sites_checked": 3, "found_count": 1}))

        events = []

        async def _scenario():
            await ScanRun.execute(
                "username_search",
                MaigretSearch,
                run_work,
                events.append,
                columns=MAIGRET_COLUMNS,
                create_fields={"username": "erin", "source": "maigret"},
            )
            return await _row(session_factory, MaigretSearch, events[0].data["search_id"])

        row = _run(_scenario())

        assert [e.type for e in events if e is not None] == ["started", "cancelled"]
        assert events[1].data == {"search_id": row.id, "total_sites_checked": 3, "found_count": 1}
        assert row.status == "cancelled"
        assert row.total_sites_checked == 3

    def test_bare_cancelled_error_marks_cancelled_with_empty_outcome(self, session_factory):
        async def run_work(search_id):
            raise asyncio.CancelledError()

        events = []

        async def _scenario():
            with pytest.raises(asyncio.CancelledError):
                await ScanRun.execute(
                    "email_search",
                    MailSearch,
                    run_work,
                    events.append,
                    columns=MAIGRET_COLUMNS,
                    create_fields={"username": "frank"},
                )
            return await _row(session_factory, MailSearch, events[0].data["search_id"])

        row = _run(_scenario())

        assert [e.type for e in events if e is not None] == ["started", "cancelled"]
        assert row.status == "cancelled"

    def test_cancel_waits_for_real_stop_before_returning(self, session_factory):
        """The whole point of the Cancellable protocol: `ScanRun.cancel()` only
        returns once the underlying work has actually unwound (row marked,
        terminal event emitted, registry deregistered) - not merely once a
        cancel signal was sent."""
        release = asyncio.Event()
        stopped = False

        async def run_work(search_id):
            nonlocal stopped
            try:
                await release.wait()
            except asyncio.CancelledError:
                stopped = True
                raise
            return ScanOutcome()

        events = []
        search_id_holder = {}

        async def _runner():
            from app.core.scans.cancellable import TaskCancellable

            cancellable = TaskCancellable(asyncio.current_task())
            await ScanRun.execute(
                "username_search",
                MaigretSearch,
                run_work,
                events.append,
                columns=MAIGRET_COLUMNS,
                create_fields={"username": "grace", "source": "maigret"},
                cancellable=cancellable,
            )

        async def _scenario():
            task = asyncio.create_task(_runner())
            # Wait until 'started' has been emitted and the cancellable is registered.
            while not events:
                await asyncio.sleep(0)
            search_id = events[0].data["search_id"]
            search_id_holder["id"] = search_id

            cancelled = await ScanRun.cancel("username_search", search_id)
            assert cancelled is True
            # cancel() only returned above once run_work had actually observed
            # the CancelledError and finished its own cleanup - TaskCancellable.
            # cancel() already awaited `task` internally (suppressing the
            # CancelledError it re-raises), so awaiting it again here would
            # just raise CancelledError a second time for no reason.
            assert stopped is True
            assert task.cancelled()

        _run(_scenario())
        row = _run(_row(session_factory, MaigretSearch, search_id_holder["id"]))
        assert row.status == "cancelled"
        assert [e.type for e in events if e is not None] == ["started", "cancelled"]

    def test_cancel_returns_false_for_unknown_search(self):
        assert _run(ScanRun.cancel("username_search", 999999)) is False

    def test_cancel_awaits_the_registered_cancellable(self, session_factory):
        fake = FakeCancellable()
        release = asyncio.Event()

        async def run_work(search_id):
            await release.wait()
            return ScanOutcome()

        events = []

        async def _scenario():
            task = asyncio.create_task(
                ScanRun.execute(
                    "email_search",
                    MailSearch,
                    run_work,
                    events.append,
                    columns=MAIGRET_COLUMNS,
                    create_fields={"username": "heidi"},
                    cancellable=fake,
                )
            )
            while not events:
                await asyncio.sleep(0)

            search_id = events[0].data["search_id"]
            assert ("email_search", search_id) in ScanRun._registry

            cancelled = await ScanRun.cancel("email_search", search_id)
            assert cancelled is True
            assert fake.cancel_called is True

            # FakeCancellable.cancel() doesn't actually stop run_work - release
            # it manually so the background task doesn't leak past the test.
            release.set()
            await task

        _run(_scenario())


class TestFeatureNamespacing:
    def test_same_search_id_across_two_features_does_not_collide(self, session_factory):
        """Two different scan-style models each have their own independently
        incrementing primary key, so it's entirely possible for username_search's
        search #1 and email_search's search #1 to be in flight at the same time -
        the registry key must include feature_name, not just search_id."""
        release_a = asyncio.Event()
        release_b = asyncio.Event()

        async def run_work_a(search_id):
            await release_a.wait()
            return ScanOutcome()

        async def run_work_b(search_id):
            await release_b.wait()
            return ScanOutcome()

        events_a, events_b = [], []
        cancellable_a = FakeCancellable()
        cancellable_b = FakeCancellable()

        async def _scenario():
            task_a = asyncio.create_task(
                ScanRun.execute(
                    "username_search",
                    MaigretSearch,
                    run_work_a,
                    events_a.append,
                    columns=MAIGRET_COLUMNS,
                    create_fields={"username": "ivan", "source": "maigret"},
                    cancellable=cancellable_a,
                )
            )
            task_b = asyncio.create_task(
                ScanRun.execute(
                    "email_search",
                    MailSearch,
                    run_work_b,
                    events_b.append,
                    columns=MAIGRET_COLUMNS,
                    create_fields={"username": "ivan"},
                    cancellable=cancellable_b,
                )
            )
            while not events_a or not events_b:
                await asyncio.sleep(0)

            search_id_b = events_b[0].data["search_id"]

            # Cancel only feature "email_search"'s scan; username_search's own
            # scan (which may well share the same numeric id) must be unaffected.
            cancelled = await ScanRun.cancel("email_search", search_id_b)
            assert cancelled is True
            assert cancellable_b.cancel_called is True
            assert cancellable_a.cancel_called is False

            release_a.set()
            release_b.set()
            await task_a
            await task_b

        _run(_scenario())


class TestScanEvent:
    def test_is_a_type_data_dataclass(self):
        event = ScanEvent("progress", {"checked": 1})
        assert event.type == "progress"
        assert event.data == {"checked": 1}
