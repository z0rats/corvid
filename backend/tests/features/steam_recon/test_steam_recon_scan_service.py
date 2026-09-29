"""run_scan's own orchestration logic (target resolution, profile/graph/geolocation/cheater-report
assembly, mapping to a ScanOutcome) - `ScanRun.execute` itself is mocked out here, same split as
git_recon's test_run_scan_orchestration.py; its own lifecycle is covered by
tests/core/scans/test_run.py.
"""

import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanRun
from app.features.steam_recon.models.steam_recon_models import SteamReconSearch
from app.features.steam_recon.schemas.steam_recon_schemas import (
    CheaterReport,
    GeolocationHypothesis,
    ScanRequest,
)
from app.features.steam_recon.service import steam_recon_scan_service as svc
from app.features.steam_recon.service.steam_graph_service import FriendCandidate, GraphResult
from app.features.steam_recon.service.steam_recon_scan_service import SteamReconError, run_scan

SUMMARY = {
    "steamid": "1",
    "personaname": "Target",
    "communityvisibilitystate": 3,
    "timecreated": 1000000000,
}

CANDIDATES = [
    FriendCandidate("A", "A", None, 1, "US", None, None, 5, False, None),
    FriendCandidate("B", "B", None, 2, None, None, None, 0, True, None),
]

AGGREGATE = GeolocationHypothesis(
    confidence="high",
    num_voters=1,
    coverage=1.0,
    countries=[],
    states=[],
    cities=[],
    self_declared=None,
)


class FakeClient:
    def __init__(self, summary=SUMMARY, cs2_stats=None):
        self.summary = summary
        self.cs2_stats = cs2_stats

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def get_player_summaries(self, ids):
        return {ids[0]: self.summary} if self.summary else {}

    async def get_player_bans(self, ids):
        return {}

    async def get_steam_level(self, steamid):
        return 10

    async def get_owned_games_count(self, steamid):
        return 5

    async def get_cs2_stats(self, steamid):
        return self.cs2_stats


def _run(coro):
    return asyncio.run(coro)


@pytest.fixture
def captured(monkeypatch):
    captured = {}

    async def fake_execute(feature_name, model, run_work, on_event, **kwargs):
        captured.update(
            feature_name=feature_name, model=model, run_work=run_work, on_event=on_event, **kwargs
        )

    monkeypatch.setattr(ScanRun, "execute", fake_execute)
    monkeypatch.setattr(svc, "get_steam_api_key", _async(lambda db: "test-key"))
    monkeypatch.setattr(svc, "SteamApiClient", lambda key: FakeClient())
    monkeypatch.setattr(svc, "resolve_steamid64", _async(lambda client, target: "1"))
    monkeypatch.setattr(svc, "map_location", _async(lambda summary: None))
    monkeypatch.setattr(svc, "collect_friend_graph", _async_graph)
    monkeypatch.setattr(svc, "aggregate_locations", lambda candidates: object())
    monkeypatch.setattr(svc, "resolve_hypothesis_names", _async(lambda aggregate: AGGREGATE))
    return captured


def _async(fn):
    async def wrapper(*args, **kwargs):
        return fn(*args, **kwargs)

    return wrapper


async def _async_graph(client, steamid, max_friends, on_progress):
    on_progress("friends", {"friends_total": 2})
    on_progress("mutual", {"analyzed": 2, "total": 2})
    return GraphResult(friends_total=2, friends_analyzed=1, candidates=CANDIDATES)


def _start(target="1", max_friends=200, include_cs_report=True, queue=None):
    queue = queue if queue is not None else asyncio.Queue()
    _run(
        run_scan(
            ScanRequest(
                target=target, max_friends=max_friends, include_cs_report=include_cs_report
            ),
            queue,
        )
    )
    return queue


def _drain(queue: asyncio.Queue) -> list:
    events = []
    while not queue.empty():
        events.append(queue.get_nowait())
    return events


class TestOrchestrationSetup:
    def test_hands_scan_run_the_right_feature_name_model_and_fields(self, captured):
        _start(target="76561197960435530", max_friends=50, include_cs_report=False)

        assert captured["feature_name"] == "steam_recon"
        assert captured["model"] is SteamReconSearch
        assert captured["create_fields"] == {
            "target": "76561197960435530",
            "max_friends": 50,
            "include_cs_report": False,
        }
        assert isinstance(captured["cancellable"], TaskCancellable)
        assert captured["expected_exceptions"]


class TestRunWork:
    def test_emits_progress_events_with_a_stage_field_in_order(self, monkeypatch, captured):
        monkeypatch.setattr(
            svc,
            "_build_cheater_report",
            _async(
                lambda *a, **kw: CheaterReport(
                    probability=0.1, level="low", coverage=0.2, already_banned=False, signals=[]
                )
            ),
        )
        queue = _start(include_cs_report=True)

        _run(captured["run_work"](42))

        stages = [e["data"]["stage"] for e in _drain(queue) if e is not None]
        assert stages == ["resolving", "friends", "mutual", "scoring"]

    def test_builds_the_full_result_with_close_friends_and_geolocation(self, monkeypatch, captured):
        monkeypatch.setattr(
            svc,
            "_build_cheater_report",
            _async(
                lambda *a, **kw: CheaterReport(
                    probability=0.4, level="medium", coverage=0.6, already_banned=False, signals=[]
                )
            ),
        )
        _start(target="1", include_cs_report=True)

        outcome = _run(captured["run_work"](42))

        assert outcome.fields["steamid64"] == "1"
        assert outcome.fields["persona_name"] == "Target"
        assert outcome.fields["friends_total"] == 2
        assert outcome.fields["friends_analyzed"] == 1
        assert outcome.fields["friends_located"] == 1  # only candidate A has a country_code
        assert outcome.fields["cheater_probability"] == 0.4

        result = outcome.db_only_fields["result"]
        assert len(result["close_friends"]) == 2
        assert result["close_friends"][0]["steamid64"] == "A"
        assert result["cheater_report"]["probability"] == 0.4

    def test_skips_the_cheater_report_when_not_requested(self, monkeypatch, captured):
        build_called = False

        async def fail_if_called(*a, **kw):
            nonlocal build_called
            build_called = True

        monkeypatch.setattr(svc, "_build_cheater_report", fail_if_called)
        _start(include_cs_report=False)

        outcome = _run(captured["run_work"](42))

        assert build_called is False
        assert outcome.fields["cheater_probability"] is None
        assert outcome.db_only_fields["result"]["cheater_report"] is None

    def test_missing_api_key_raises_steam_recon_error(self, monkeypatch, captured):
        monkeypatch.setattr(svc, "get_steam_api_key", _async(lambda db: None))
        _start()

        with pytest.raises(SteamReconError, match="Steam Web API key"):
            _run(captured["run_work"](42))

    def test_unrecognized_target_is_a_steam_recon_error_not_an_http_exception(
        self, monkeypatch, captured
    ):
        async def fail_resolve(client, target):
            raise AppHTTPException(
                status_code=400, detail="Not a recognized target", error_code="STEAM_INVALID_TARGET"
            )

        monkeypatch.setattr(svc, "resolve_steamid64", fail_resolve)
        _start()

        with pytest.raises(SteamReconError, match="Not a recognized target"):
            _run(captured["run_work"](42))

    def test_target_friends_private_is_a_steam_recon_error(self, monkeypatch, captured):
        from app.features.steam_recon.service.steam_graph_service import FriendsPrivateError

        async def fail_graph(client, steamid, max_friends, on_progress):
            raise FriendsPrivateError("This profile's friends list is private")

        monkeypatch.setattr(svc, "collect_friend_graph", fail_graph)
        _start()

        with pytest.raises(SteamReconError, match="friends list is private"):
            _run(captured["run_work"](42))

    def test_no_profile_found_is_a_steam_recon_error(self, monkeypatch, captured):
        monkeypatch.setattr(svc, "SteamApiClient", lambda key: FakeClient(summary=None))
        _start()

        with pytest.raises(SteamReconError, match="no profile"):
            _run(captured["run_work"](42))

    def test_cancellation_mid_graph_collection_is_not_swallowed(self, monkeypatch, captured):
        async def cancelling_graph(client, steamid, max_friends, on_progress):
            raise asyncio.CancelledError()

        monkeypatch.setattr(svc, "collect_friend_graph", cancelling_graph)
        _start()

        with pytest.raises(asyncio.CancelledError):
            _run(captured["run_work"](42))
