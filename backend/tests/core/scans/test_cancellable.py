"""The three Cancellable adapters (see core/scans/cancellable.py). GitCloneCancellable
gets the most coverage since it's new, novel (psutil-based process reaping, no
asyncio-level cancellation point), and has no existing test to mirror - unlike
email_search's `_kill_orphaned_chromium`, which this mirrors but which itself
has no test in this repo either.
"""
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import psutil

from app.core.scans.cancellable import GitCloneCancellable, ProcessCancellable, TaskCancellable


def _run(coro):
    return asyncio.run(coro)


class TestTaskCancellable:
    def test_cancel_stops_the_task_and_waits_for_it(self):
        stopped = False

        async def blocked():
            nonlocal stopped
            try:
                await asyncio.Event().wait()
            except asyncio.CancelledError:
                stopped = True
                raise

        async def _scenario():
            task = asyncio.create_task(blocked())
            await asyncio.sleep(0)  # let it actually start waiting

            await TaskCancellable(task).cancel()

            assert stopped is True
            assert task.cancelled()

        _run(_scenario())

    def test_cancel_on_an_already_finished_task_does_not_raise(self):
        async def _scenario():
            task = asyncio.create_task(asyncio.sleep(0))
            await task
            await TaskCancellable(task).cancel()  # should not raise

        _run(_scenario())


class TestProcessCancellable:
    def test_cancel_terminates_and_waits_for_the_process_and_sets_cancelled(self):
        process = MagicMock()
        process.returncode = None
        process.wait = AsyncMock()

        cancellable = ProcessCancellable(process)
        _run(cancellable.cancel())

        process.terminate.assert_called_once()
        process.wait.assert_awaited_once()
        assert cancellable.cancelled is True

    def test_cancel_is_a_no_op_once_the_process_already_exited(self):
        process = MagicMock()
        process.returncode = 0
        process.wait = AsyncMock()

        cancellable = ProcessCancellable(process)
        _run(cancellable.cancel())

        process.terminate.assert_not_called()
        assert cancellable.cancelled is False


class _FakeChild:
    def __init__(self, pid, name):
        self.pid = pid
        self._name = name
        self.killed = False

    def name(self):
        return self._name

    def kill(self):
        self.killed = True


class TestGitCloneCancellable:
    def test_kills_only_new_git_children_not_present_in_before_pids(self):
        pre_existing_git = _FakeChild(pid=100, name="git")
        new_git = _FakeChild(pid=200, name="git")
        new_unrelated = _FakeChild(pid=300, name="python3")

        fake_process = MagicMock()
        fake_process.children.return_value = [pre_existing_git, new_git, new_unrelated]

        cancellable = GitCloneCancellable(before_pids={100})

        with patch("app.core.scans.cancellable.psutil.Process", return_value=fake_process):
            _run(cancellable.cancel())

        assert cancellable.cancelled is True
        assert pre_existing_git.killed is False  # was already running before this scan
        assert new_git.killed is True  # spawned by this scan, git-shaped -> killed
        assert new_unrelated.killed is False  # spawned by this scan, but not a git process

    def test_cancelled_flag_is_set_even_if_no_children_are_found(self):
        fake_process = MagicMock()
        fake_process.children.return_value = []

        cancellable = GitCloneCancellable(before_pids=set())
        with patch("app.core.scans.cancellable.psutil.Process", return_value=fake_process):
            _run(cancellable.cancel())

        assert cancellable.cancelled is True

    def test_survives_a_process_that_disappears_mid_kill(self):
        vanishing = _FakeChild(pid=200, name="git")
        vanishing.kill = MagicMock(side_effect=psutil.NoSuchProcess(200))

        fake_process = MagicMock()
        fake_process.children.return_value = [vanishing]

        cancellable = GitCloneCancellable(before_pids=set())
        with patch("app.core.scans.cancellable.psutil.Process", return_value=fake_process):
            _run(cancellable.cancel())  # should not raise

        assert cancellable.cancelled is True

    def test_survives_psutil_error_listing_children(self):
        with patch("app.core.scans.cancellable.psutil.Process", side_effect=psutil.Error("boom")):
            cancellable = GitCloneCancellable(before_pids=set())
            _run(cancellable.cancel())  # should not raise

        assert cancellable.cancelled is True
