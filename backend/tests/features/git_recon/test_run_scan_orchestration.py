"""run_scan/run_scan_task's own orchestration logic (mode dispatch, validation,
run_work/feature_name plumbing into ScanRun) - only the real git clone/network
calls are mocked out here; the per-repo commit-slicing logic they'd otherwise
exercise (_track_commits_per_repo) is covered directly, against a fake
analyst, in tests/features/git_recon/test_identity_correlation.py.

run_scan_task's own lifecycle (create running row -> started -> terminal event
+ mark row) is no longer this module's concern - ScanRun.execute() owns that
now and is covered end to end by tests/core/scans/test_run.py. What's specific
to git_recon and still worth testing here is only what run_scan_task itself
builds: the run_work closure's mapping from a gitcolombo result to a ScanOutcome
(including its GitReconError/TimeoutError handling), and that it's handed to
ScanRun.execute() with the right feature_name/model/create_fields/cancellable.
"""
import asyncio

import pytest

from app.core.scans.cancellable import GitCloneCancellable
from app.core.scans.run import ScanCancelled
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
    """Captures the `run_work`/`cancellable` run_scan_task hands to ScanRun.execute()
    (mocked out here - its own lifecycle is ScanRun's concern, not this module's,
    see the module docstring), then calls that closure directly to check its
    result-mapping and error-handling."""

    @pytest.fixture
    def captured(self, monkeypatch):
        captured = {}

        async def fake_execute(feature_name, model, run_work, on_event, **kwargs):
            captured.update(feature_name=feature_name, model=model, run_work=run_work, on_event=on_event, **kwargs)

        monkeypatch.setattr(svc.ScanRun, "execute", fake_execute)
        return captured

    def _start(self, **overrides):
        kwargs = dict(
            mode="url", target="https://github.com/octocat/Hello-World", include_forks=False,
            resolve_github_logins=False, ignore_noreply=False, github_token=None, queue=asyncio.Queue(),
        )
        kwargs.update(overrides)
        _run(run_scan_task(**kwargs))

    def test_hands_scan_run_the_right_feature_name_model_and_fields(self, captured):
        self._start()

        assert captured["feature_name"] == "git_recon"
        assert captured["model"] is GitReconSearch
        assert captured["create_fields"] == {
            "mode": "url", "target": "https://github.com/octocat/Hello-World",
        }
        assert captured["started_fields"] == {
            "mode": "url", "target": "https://github.com/octocat/Hello-World",
        }
        assert isinstance(captured["cancellable"], GitCloneCancellable)

    def test_run_work_maps_a_successful_scan_result_to_a_scan_outcome(self, monkeypatch, captured):
        async def fake_run_scan(**kwargs):
            return {
                "repos": [{"url": "r1", "cloned": True}, {"url": "r2", "cloned": False}],
                "persons": [{"key": "p1"}],
            }

        monkeypatch.setattr(svc, "run_scan", fake_run_scan)
        self._start()

        outcome = _run(captured["run_work"](123))

        assert outcome.fields == {"repos_scanned": 1, "repos_failed": 1, "persons_found": 1}
        assert outcome.db_only_fields["result"]["persons"] == [{"key": "p1"}]

    def test_run_work_lets_git_recon_error_propagate_unwrapped(self, monkeypatch, captured):
        async def fake_run_scan(**kwargs):
            raise GitReconError("No repositories to scan")

        monkeypatch.setattr(svc, "run_scan", fake_run_scan)
        self._start()

        with pytest.raises(GitReconError, match="No repositories to scan"):
            _run(captured["run_work"](123))

    def test_run_work_rewrites_a_bare_timeout_error_with_a_message(self, monkeypatch, captured):
        async def fake_run_scan(**kwargs):
            raise TimeoutError()

        monkeypatch.setattr(svc, "run_scan", fake_run_scan)
        self._start()

        with pytest.raises(TimeoutError, match="Scan timed out"):
            _run(captured["run_work"](123))

    def test_run_work_raises_scan_cancelled_once_the_cancellable_was_triggered(self, monkeypatch, captured):
        async def fake_run_scan(**kwargs):
            return {"repos": [{"url": "r1", "cloned": False}], "persons": []}

        monkeypatch.setattr(svc, "run_scan", fake_run_scan)
        self._start()

        captured["cancellable"].cancelled = True

        with pytest.raises(ScanCancelled) as exc_info:
            _run(captured["run_work"](123))
        assert exc_info.value.outcome.fields == {"repos_scanned": 0, "repos_failed": 1, "persons_found": 0}
