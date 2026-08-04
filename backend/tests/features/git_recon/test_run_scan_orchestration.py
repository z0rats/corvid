"""run_scan/run_scan_task's own orchestration logic (mode dispatch, validation,
persistence, SSE event shape) - the actual gitcolombo clone/API calls are
mocked out rather than exercised, per this coverage push's "base logic only,
no real subprocess/API calls" scope for this module."""
import asyncio

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.features.git_recon.models.git_recon_models import GitReconSearch
from app.features.git_recon.service import git_recon_service as svc
from app.features.git_recon.service.git_recon_service import GitReconError, run_scan, run_scan_task


def _run(coro):
    return asyncio.run(coro)


class TestRunScanDispatch:
    def test_search_mode_delegates_to_search_runner(self, monkeypatch):
        monkeypatch.setattr(svc, "_run_search_mode_sync", lambda username, token, ignore_noreply: {"stats": "search-result"})

        result = _run(run_scan(
            mode="search", target="octocat", include_forks=False,
            resolve_github_logins=False, ignore_noreply=False, github_token=None,
        ))

        assert result == {"stats": "search-result"}

    def test_search_mode_rejects_invalid_nickname_before_running(self, monkeypatch):
        called = False

        def fail(*args, **kwargs):
            nonlocal called
            called = True

        monkeypatch.setattr(svc, "_run_search_mode_sync", fail)

        with pytest.raises(GitReconError):
            _run(run_scan(
                mode="search", target="not a valid nickname!!!", include_forks=False,
                resolve_github_logins=False, ignore_noreply=False, github_token=None,
            ))
        assert called is False

    def test_url_mode_clones_the_single_validated_url(self, monkeypatch):
        captured = {}

        def fake_clone(sources, repos_dir, *, resolve_github_logins):
            captured["sources"] = sources
            return {"stats": "cloned"}

        monkeypatch.setattr(svc, "_run_clone_mode_sync", fake_clone)

        result = _run(run_scan(
            mode="url", target="https://github.com/octocat/Hello-World", include_forks=False,
            resolve_github_logins=False, ignore_noreply=False, github_token=None,
        ))

        assert captured["sources"] == ["https://github.com/octocat/Hello-World"]
        assert result == {"stats": "cloned"}

    def test_nickname_mode_raises_when_no_public_repos_found(self, monkeypatch):
        monkeypatch.setattr(svc, "_get_public_repos_count", lambda nickname, token: 0)

        with pytest.raises(GitReconError, match="No public repos"):
            _run(run_scan(
                mode="nickname", target="octocat", include_forks=False,
                resolve_github_logins=False, ignore_noreply=False, github_token=None,
            ))

    def test_nickname_mode_truncates_to_max_repos_and_adds_a_note(self, monkeypatch):
        many_repos = {f"https://github.com/octocat/repo{i}" for i in range(30)}
        monkeypatch.setattr(svc, "_get_public_repos_count", lambda nickname, token: 30)
        monkeypatch.setattr(svc, "_get_github_repos", lambda nickname, count, include_forks, token: many_repos)
        monkeypatch.setattr(
            svc, "_run_clone_mode_sync",
            lambda sources, repos_dir, *, resolve_github_logins: {"stats": "ok", "sources_scanned": len(sources)},
        )

        result = _run(run_scan(
            mode="nickname", target="octocat", include_forks=False,
            resolve_github_logins=False, ignore_noreply=False, github_token=None,
        ))

        assert result["sources_scanned"] == 25  # MAX_REPOS_PER_SCAN
        assert any("found 30 public repo" in note for note in result["notes"])

    def test_unknown_mode_raises_git_recon_error(self):
        with pytest.raises(GitReconError, match="Unknown scan mode"):
            _run(run_scan(
                mode="bogus", target="x", include_forks=False,
                resolve_github_logins=False, ignore_noreply=False, github_token=None,
            ))


class TestRunScanTask:
    @pytest.fixture
    def session_factory(self, monkeypatch):
        engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool,
        )

        async def _create_tables():
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all, tables=[GitReconSearch.__table__])

        _run(_create_tables())
        factory = async_sessionmaker(engine, expire_on_commit=False)

        import contextlib

        @contextlib.asynccontextmanager
        async def fake_managed_session():
            async with factory() as db:
                yield db
                await db.commit()

        monkeypatch.setattr(svc, "managed_session", fake_managed_session)
        return factory

    def test_success_path_persists_and_emits_started_then_completed(self, monkeypatch, session_factory):
        async def fake_run_scan(**kwargs):
            return {"repos": [{"url": "r1", "cloned": True}], "persons": [{"key": "p1"}]}

        monkeypatch.setattr(svc, "run_scan", fake_run_scan)

        async def _scenario():
            queue = asyncio.Queue()
            await run_scan_task(
                mode="url", target="https://github.com/octocat/Hello-World", include_forks=False,
                resolve_github_logins=False, ignore_noreply=False, github_token=None, queue=queue,
            )
            events = []
            while True:
                item = queue.get_nowait()
                if item is None:
                    break
                events.append(item)
            return events

        events = _run(_scenario())

        assert events[0]["type"] == "started"
        assert events[-1]["type"] == "completed"
        assert events[-1]["repos_scanned"] == 1
        assert events[-1]["persons_found"] == 1

    def test_git_recon_error_marks_search_failed_and_emits_failed_event(self, monkeypatch, session_factory):
        async def fake_run_scan(**kwargs):
            raise GitReconError("No repositories to scan")

        monkeypatch.setattr(svc, "run_scan", fake_run_scan)

        async def _scenario():
            queue = asyncio.Queue()
            await run_scan_task(
                mode="url", target="https://github.com/octocat/Hello-World", include_forks=False,
                resolve_github_logins=False, ignore_noreply=False, github_token=None, queue=queue,
            )
            events = []
            while True:
                item = queue.get_nowait()
                if item is None:
                    break
                events.append(item)
            return events

        events = _run(_scenario())

        assert events[-1] == {
            "type": "failed", "search_id": events[0]["search_id"], "error": "No repositories to scan",
        }

    def test_timeout_error_marks_search_failed_with_timeout_message(self, monkeypatch, session_factory):
        async def fake_run_scan(**kwargs):
            raise TimeoutError()

        monkeypatch.setattr(svc, "run_scan", fake_run_scan)

        async def _scenario():
            queue = asyncio.Queue()
            await run_scan_task(
                mode="url", target="https://github.com/octocat/Hello-World", include_forks=False,
                resolve_github_logins=False, ignore_noreply=False, github_token=None, queue=queue,
            )
            events = []
            while True:
                item = queue.get_nowait()
                if item is None:
                    break
                events.append(item)
            return events

        events = _run(_scenario())

        assert events[-1]["type"] == "failed"
        assert events[-1]["error"] == "Scan timed out"
