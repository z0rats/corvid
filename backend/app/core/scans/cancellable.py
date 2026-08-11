"""Concrete `Cancellable` adapters (see `run.py`) for the three ways a scan's
underlying work can actually be stopped in this codebase: an asyncio task, a
subprocess, or (for git_recon, which has neither) killing the worker thread's
own child processes out from under it.
"""
import asyncio
import contextlib
import logging

import psutil

logger = logging.getLogger(__name__)


class TaskCancellable:
    """Wraps the asyncio.Task actually running the scan. Used by username_search
    (maigret), threat_actor_usernames, and email_search - each drives its scan
    as a plain coroutine, so `task.cancel()` delivers `asyncio.CancelledError`
    at its next `await`, same as before this refactor.
    """

    def __init__(self, task: asyncio.Task):
        self._task = task

    async def cancel(self) -> None:
        self._task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await self._task


class ProcessCancellable:
    """Wraps a subprocess handle. Used by social_analyzer, whose CLI subprocess
    has no asyncio-cancellation point to hook into - mailcat/social-analyzer's
    own `process.communicate()` call returns normally when the process is killed
    by another request, it doesn't raise `CancelledError`. `.cancelled` lets
    `run_work` tell that apart from a genuine nonzero-exit/crash after
    `communicate()` returns.
    """

    def __init__(self, process: asyncio.subprocess.Process):
        self._process = process
        self.cancelled = False

    async def cancel(self) -> None:
        if self._process.returncode is not None:
            return
        self.cancelled = True
        self._process.terminate()
        await self._process.wait()


_GIT_PROCESS_NAMES = {"git"}


class GitCloneCancellable:
    """git_recon's clone-mode scan runs gitcolombo's blocking `git clone`/`git log`
    subprocess calls inside a worker thread (`asyncio.to_thread`), so there is no
    asyncio-level cancellation point at all - `task.cancel()` on the outer scan
    task would only interrupt it at the next `await`, which for a thread already
    blocked in `Popen.wait()` never comes until the thread itself returns.

    `cancel()` instead reaps this scan's own child git processes directly (same
    psutil before/after-pid-diff pattern as email_search's
    `_kill_orphaned_chromium`, scoped to `before_pids` so a concurrent scan's
    own git children aren't touched) - killing them makes the worker thread's
    blocked subprocess calls return quickly on their own, so `_run_clone_mode_sync`
    finishes (with whatever repos it had already cloned) shortly after. Unlike
    `TaskCancellable`/`ProcessCancellable`, `cancel()` does NOT await that
    thread's own completion - it only waits for the kill itself, since a stuck
    OS thread can't be forcibly torn down and there's nothing to gain by
    blocking the cancel request on it. `run_work` notices via `.cancelled`
    once its `await asyncio.to_thread(...)` call does eventually return.
    """

    def __init__(self, before_pids: set[int]):
        self._before_pids = before_pids
        self.cancelled = False

    async def cancel(self) -> None:
        self.cancelled = True
        await asyncio.to_thread(self._kill_new_children)

    def _kill_new_children(self) -> None:
        try:
            children = psutil.Process().children(recursive=True)
        except psutil.Error:
            logger.debug("git_recon cancel: failed to list child processes", exc_info=True)
            return

        for child in children:
            if child.pid in self._before_pids:
                continue
            try:
                if child.name().lower() in _GIT_PROCESS_NAMES:
                    child.kill()
                    logger.info("Killed git process (pid=%s) for cancelled git_recon scan", child.pid)
            except psutil.NoSuchProcess:
                pass
