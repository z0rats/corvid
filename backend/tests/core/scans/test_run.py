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
from app.core.alerts.models.alerts_models import Alert
from app.core.scans.crud import ScanColumns
from app.core.scans.run import ScanCancelled, ScanEvent, ScanOutcome, ScanRun
from app.core.settings.telegram.models.telegram_settings_models import TelegramSettings
from app.features.email_search.models.email_search_models import MailSearch
from app.features.username_search.models.username_search_models import MaigretSearch
from tests.conftest import run as _run

MAIGRET_COLUMNS = ScanColumns(error_column="error_message", completed_at_column="completed_at")


@pytest.fixture
def session_factory(monkeypatch, make_session_factory):
    # Alert/TelegramSettings tables: ScanRun.execute() now raises an alert (and
    # checks Telegram settings) on every terminal transition - see alerts_service.
    factory = make_session_factory(
        [MaigretSearch.__table__, MailSearch.__table__, Alert.__table__, TelegramSettings.__table__]
    )

    @contextlib.asynccontextmanager
    async def fake_managed_session():
        async with factory() as db:
            yield db
            await db.commit()

    monkeypatch.setattr(run_module, "managed_session", fake_managed_session)

    async def _seed_telegram_settings():
        # Pre-create the singleton row so concurrent terminal events (see
        # TestFeatureNamespacing) don't race to INSERT it - `get_or_create_singleton`'s
        # own race handling assumes independent connections, not two sessions
        # sharing this fixture's single StaticPool-pinned SQLite connection.
        async with factory() as db:
            db.add(TelegramSettings(id=1))
            await db.commit()

    _run(_seed_telegram_settings())
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
        assert events[1].data["error"] == "Scan failed"
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

            cancelled = await ScanRun.cancel(MaigretSearch, search_id)
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
        assert _run(ScanRun.cancel(MaigretSearch, 999999)) is False

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
            assert (MailSearch, search_id) in ScanRun._registry

            cancelled = await ScanRun.cancel(MailSearch, search_id)
            assert cancelled is True
            assert fake.cancel_called is True

            # FakeCancellable.cancel() doesn't actually stop run_work - release
            # it manually so the background task doesn't leak past the test.
            release.set()
            await task

        _run(_scenario())


class TestTableNamespacing:
    def test_same_search_id_across_two_tables_does_not_collide(self, session_factory):
        """Two different scan-style models each have their own independently
        incrementing primary key, so it's entirely possible for username_search's
        search #1 and email_search's search #1 to be in flight at the same time -
        the registry key must include the table, not just search_id."""
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

            # Cancel only the MailSearch table's scan; username_search's own
            # scan (which may well share the same numeric id) must be unaffected.
            cancelled = await ScanRun.cancel(MailSearch, search_id_b)
            assert cancelled is True
            assert cancellable_b.cancel_called is True
            assert cancellable_a.cancel_called is False

            # Finish one at a time: both terminal writes share this fixture's single
            # StaticPool connection, and SQLAlchemy 2.1 refuses to commit one session
            # while the other's statement is open on it. The app's real pool gives each
            # session its own connection; the collision under test is the cancel above.
            release_a.set()
            await task_a
            release_b.set()
            await task_b

        _run(_scenario())


class TestHeavyScanQueue:
    """`heavy=True` runs share SCAN_MAX_CONCURRENT_HEAVY slots (capped at 1 here)."""

    @pytest.fixture(autouse=True)
    def one_heavy_slot(self, monkeypatch):
        monkeypatch.setattr(run_module.settings.scans, "max_concurrent_heavy", 1)
        monkeypatch.setattr(run_module, "_heavy_slots", None)

    @staticmethod
    def _start(run_work, events, *, heavy=True, cancellable=None, username="alice"):
        return asyncio.create_task(
            ScanRun.execute(
                "username_search",
                MaigretSearch,
                run_work,
                events.append,
                columns=MAIGRET_COLUMNS,
                create_fields={"username": username, "source": "maigret"},
                cancellable=cancellable,
                heavy=heavy,
            )
        )

    @staticmethod
    async def _until(predicate):
        while not predicate():
            await asyncio.sleep(0)

    @staticmethod
    def _types(events):
        return [e.type for e in events if e is not None]

    def test_second_heavy_run_queues_until_the_first_finishes(self, session_factory):
        release_first = asyncio.Event()
        second_started = False

        async def first_work(search_id):
            await release_first.wait()
            return ScanOutcome()

        async def second_work(search_id):
            nonlocal second_started
            second_started = True
            return ScanOutcome()

        first_events, second_events = [], []

        async def _scenario():
            first = self._start(first_work, first_events)
            await self._until(lambda: first_events)
            second = self._start(second_work, second_events, username="bob")
            await self._until(lambda: "queued" in self._types(second_events))
            await asyncio.sleep(0)
            assert second_started is False

            release_first.set()
            await first
            await second

        _run(_scenario())

        assert second_started is True
        assert self._types(second_events) == ["started", "queued", "running", "completed"]
        assert "queued" not in self._types(first_events)

    def test_cancel_while_queued_skips_the_work_and_leaks_no_slot(self, session_factory):
        release_first = asyncio.Event()
        queued_work_ran = False
        cancellable = FakeCancellable()

        async def first_work(search_id):
            await release_first.wait()
            return ScanOutcome()

        async def queued_work(search_id):
            nonlocal queued_work_ran
            queued_work_ran = True
            return ScanOutcome()

        first_events, queued_events, third_events = [], [], []

        async def _scenario():
            first = self._start(first_work, first_events)
            await self._until(lambda: first_events)
            queued = self._start(queued_work, queued_events, cancellable=cancellable)
            await self._until(lambda: "queued" in self._types(queued_events))

            search_id = queued_events[0].data["search_id"]
            assert await ScanRun.cancel(MaigretSearch, search_id) is True
            await queued

            release_first.set()
            await first
            # The single slot must be free again: a later heavy run goes straight through.
            await self._start(lambda _id: asyncio.sleep(0, ScanOutcome()), third_events)
            return await _row(session_factory, MaigretSearch, search_id)

        row = _run(_scenario())

        assert queued_work_ran is False
        assert cancellable.cancel_called is False  # dropped from the queue, nothing to stop
        assert row.status == "cancelled"
        assert self._types(queued_events) == ["started", "queued", "cancelled"]
        assert self._types(third_events) == ["started", "completed"]
        assert ScanRun._queued == {}

    def test_task_cancelled_while_queued_does_not_leak_a_slot(self, session_factory):
        release_first = asyncio.Event()

        async def first_work(search_id):
            await release_first.wait()
            return ScanOutcome()

        first_events, queued_events, third_events = [], [], []

        async def _scenario():
            first = self._start(first_work, first_events)
            await self._until(lambda: first_events)
            queued = self._start(lambda _id: asyncio.sleep(0, ScanOutcome()), queued_events)
            await self._until(lambda: "queued" in self._types(queued_events))

            queued.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await queued

            release_first.set()
            await first
            await self._start(lambda _id: asyncio.sleep(0, ScanOutcome()), third_events)

        _run(_scenario())

        assert "cancelled" in self._types(queued_events)
        assert self._types(third_events) == ["started", "completed"]

    def test_light_runs_are_not_queued_behind_heavy_ones(self, session_factory):
        release_heavy = asyncio.Event()

        async def heavy_work(search_id):
            await release_heavy.wait()
            return ScanOutcome()

        heavy_events, light_events = [], []

        async def _scenario():
            heavy = self._start(heavy_work, heavy_events)
            await self._until(lambda: heavy_events)
            await self._start(
                lambda _id: asyncio.sleep(0, ScanOutcome()), light_events, heavy=False
            )
            release_heavy.set()
            await heavy

        _run(_scenario())

        assert self._types(light_events) == ["started", "completed"]


class TestScanEvent:
    def test_is_a_type_data_dataclass(self):
        event = ScanEvent("progress", {"checked": 1})
        assert event.type == "progress"
        assert event.data == {"checked": 1}
