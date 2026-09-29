import asyncio

import httpx
import pytest

from app.features.steam_recon.service import steam_graph_service as graph_mod
from app.features.steam_recon.service.steam_api_client import SteamApiClient
from app.features.steam_recon.service.steam_graph_service import (
    FriendsPrivateError,
    collect_friend_graph,
    select_candidates,
)

TARGET = "1"


def _friend(steamid, friend_since):
    return {"steamid": steamid, "friend_since": friend_since}


def _summary(steamid, *, public=True, **extra):
    return {
        "steamid": steamid,
        "personaname": f"user-{steamid}",
        "communityvisibilitystate": 3 if public else 1,
        **extra,
    }


class TestSelectCandidates:
    def test_filters_to_public_profiles_only(self):
        friends = [_friend("1", 100), _friend("2", 200)]
        summaries = {"1": _summary("1", public=True), "2": _summary("2", public=False)}

        result = select_candidates(friends, summaries, max_friends=10)

        assert [f["steamid"] for f in result] == ["1"]

    def test_sorts_oldest_friend_since_first(self):
        friends = [_friend("1", 300), _friend("2", 100), _friend("3", 200)]
        summaries = {s: _summary(s) for s in ("1", "2", "3")}

        result = select_candidates(friends, summaries, max_friends=10)

        assert [f["steamid"] for f in result] == ["2", "3", "1"]

    def test_missing_friend_since_sorts_last(self):
        friends = [_friend("1", None), _friend("2", 50)]
        summaries = {s: _summary(s) for s in ("1", "2")}

        result = select_candidates(friends, summaries, max_friends=10)

        assert [f["steamid"] for f in result] == ["2", "1"]

    def test_caps_at_max_friends(self):
        friends = [_friend(str(i), i) for i in range(5)]
        summaries = {str(i): _summary(str(i)) for i in range(5)}

        result = select_candidates(friends, summaries, max_friends=2)

        assert len(result) == 2


@pytest.fixture
def steam_graph(monkeypatch):
    """A 3-friend graph around the target: A and B are mutually connected through the target
    and each other, C is public but has a private friends list of its own."""
    friends = [_friend("A", 1), _friend("B", 2), _friend("C", 3)]
    summaries = {
        "A": _summary("A", loccountrycode="US"),
        "B": _summary("B", loccountrycode="US"),
        "C": _summary("C"),
    }
    friend_lists = {
        TARGET: friends,
        "A": [{"steamid": "B"}, {"steamid": TARGET}],
        "B": [{"steamid": "A"}, {"steamid": TARGET}],
        "C": None,  # private
    }
    bans = {"A": {"SteamId": "A", "VACBanned": True, "NumberOfGameBans": 0}}

    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        if request.url.path == "/ISteamUser/GetFriendList/v1/":
            steamid = params["steamid"]
            friends_for = friend_lists.get(steamid)
            if friends_for is None:
                return httpx.Response(401)
            return httpx.Response(200, json={"friendslist": {"friends": friends_for}})
        if request.url.path == "/ISteamUser/GetPlayerSummaries/v2/":
            ids = params["steamids"].split(",")
            return httpx.Response(200, json={"response": {"players": [summaries[i] for i in ids]}})
        if request.url.path == "/ISteamUser/GetPlayerBans/v1/":
            ids = params["steamids"].split(",")
            return httpx.Response(200, json={"players": [bans[i] for i in ids if i in bans]})
        raise AssertionError(f"unexpected path {request.url.path}")

    return httpx.MockTransport(handler)


def _run(coro):
    return asyncio.run(coro)


def test_collect_friend_graph_ranks_by_mutual_connections(steam_graph):
    async def go():
        events = []
        async with SteamApiClient("key", transport=steam_graph) as client:
            return await collect_friend_graph(
                client, TARGET, 10, lambda s, d: events.append((s, d))
            ), events

    result, events = _run(go())

    assert result.friends_total == 3
    # A and B are each mutually connected to the other via the target's own friend list.
    assert result.friends_analyzed == 2  # C's friend list is private
    by_id = {c.steamid64: c for c in result.candidates}
    assert by_id["A"].mutual_count == 1
    assert by_id["B"].mutual_count == 1
    assert by_id["C"].mutual_count == 0
    assert by_id["C"].friends_private is True
    assert by_id["A"].bans == {"SteamId": "A", "VACBanned": True, "NumberOfGameBans": 0}
    # "friends" and "profiles" fire once each before any "mutual" progress; the three "mutual"
    # events themselves may interleave depending on scheduling, so only their count is checked.
    assert [e[0] for e in events[:2]] == ["friends", "profiles"]
    assert [e[0] for e in events[2:]] == ["mutual"] * 3
    assert events[-1][1]["analyzed"] == 3


def test_collect_friend_graph_raises_when_target_friends_are_private():
    def handler(request):
        return httpx.Response(401)

    async def go():
        async with SteamApiClient("key", transport=httpx.MockTransport(handler)) as client:
            await collect_friend_graph(client, TARGET, 10, lambda s, d: None)

    with pytest.raises(FriendsPrivateError):
        _run(go())


def test_rate_limited_candidate_fetch_is_retried_then_succeeds(monkeypatch):
    monkeypatch.setattr(graph_mod, "FRIEND_FETCH_RETRY_BACKOFF_SECONDS", 0.0)
    attempts = {"A": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        if request.url.path == "/ISteamUser/GetFriendList/v1/" and params["steamid"] == TARGET:
            return httpx.Response(200, json={"friendslist": {"friends": [_friend("A", 1)]}})
        if request.url.path == "/ISteamUser/GetFriendList/v1/" and params["steamid"] == "A":
            attempts["A"] += 1
            if attempts["A"] < 2:
                return httpx.Response(429, headers={"Retry-After": "0"})
            return httpx.Response(200, json={"friendslist": {"friends": []}})
        if request.url.path == "/ISteamUser/GetPlayerSummaries/v2/":
            return httpx.Response(200, json={"response": {"players": [_summary("A")]}})
        if request.url.path == "/ISteamUser/GetPlayerBans/v1/":
            return httpx.Response(200, json={"players": []})
        raise AssertionError(request.url.path)

    async def go():
        async with SteamApiClient("key", transport=httpx.MockTransport(handler)) as client:
            return await collect_friend_graph(client, TARGET, 10, lambda s, d: None)

    result = _run(go())

    assert attempts["A"] == 2
    assert result.candidates[0].friends_private is False
