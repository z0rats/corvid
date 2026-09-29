import asyncio
import logging

import httpx
import pytest

from app.features.steam_recon.service.steam_api_client import (
    SteamApiClient,
    SteamApiError,
    SteamKeyRejectedError,
    SteamPrivateError,
    SteamRateLimitedError,
)

KEY = "SECRETKEY0123456789ABCDEF01234567"


def _run(coro):
    return asyncio.run(coro)


def _client(handler) -> SteamApiClient:
    return SteamApiClient(KEY, transport=httpx.MockTransport(handler))


def _call(handler, method: str, *args):
    async def go():
        async with _client(handler) as client:
            return await getattr(client, method)(*args)

    return _run(go())


def test_resolve_vanity_returns_steamid_on_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/ISteamUser/ResolveVanityURL/v1/"
        assert request.url.params["vanityurl"] == "robinwalker"
        assert request.url.params["key"] == KEY
        return httpx.Response(200, json={"response": {"success": 1, "steamid": "7656119796"}})

    assert _call(handler, "resolve_vanity", "robinwalker") == "7656119796"


def test_resolve_vanity_returns_none_when_no_match():
    def handler(request):
        return httpx.Response(200, json={"response": {"success": 42, "message": "No match"}})

    assert _call(handler, "resolve_vanity", "nobody") is None


def test_player_summaries_are_batched_by_100_and_keyed_by_steamid():
    seen_batches: list[int] = []
    ids = [str(76561197960265729 + i) for i in range(250)]

    def handler(request):
        batch = request.url.params["steamids"].split(",")
        seen_batches.append(len(batch))
        return httpx.Response(
            200, json={"response": {"players": [{"steamid": s, "personaname": s} for s in batch]}}
        )

    result = _call(handler, "get_player_summaries", ids)

    assert seen_batches == [100, 100, 50]
    assert set(result) == set(ids)


def test_player_bans_are_keyed_by_steamid():
    def handler(request):
        return httpx.Response(
            200, json={"players": [{"SteamId": "1", "VACBanned": True, "NumberOfVACBans": 2}]}
        )

    result = _call(handler, "get_player_bans", ["1"])

    assert result["1"]["NumberOfVACBans"] == 2


@pytest.mark.parametrize(
    "body, expected",
    [({"response": {"player_level": 42}}, 42), ({"response": {}}, None), ({}, None)],
)
def test_steam_level_is_none_when_absent(body, expected):
    assert _call(lambda r: httpx.Response(200, json=body), "get_steam_level", "1") == expected


@pytest.mark.parametrize(
    "body, expected",
    [({"response": {"game_count": 7, "games": []}}, 7), ({"response": {}}, None)],
)
def test_owned_games_count_is_none_for_a_private_library(body, expected):
    assert _call(lambda r: httpx.Response(200, json=body), "get_owned_games_count", "1") == expected


@pytest.mark.parametrize(
    "status, exc_type",
    [
        (403, SteamKeyRejectedError),
        (401, SteamPrivateError),
        (500, SteamApiError),
        (404, SteamApiError),
    ],
)
def test_error_statuses_map_to_typed_exceptions(status, exc_type):
    with pytest.raises(exc_type):
        _call(lambda r: httpx.Response(status), "get_steam_level", "1")


def test_rate_limit_carries_retry_after():
    handler = lambda r: httpx.Response(429, headers={"Retry-After": "7"})  # noqa: E731
    with pytest.raises(SteamRateLimitedError) as info:
        _call(handler, "get_steam_level", "1")
    assert info.value.retry_after == 7.0


def test_rate_limit_without_retry_after_header():
    with pytest.raises(SteamRateLimitedError) as info:
        _call(lambda r: httpx.Response(429), "get_steam_level", "1")
    assert info.value.retry_after is None


def test_non_json_body_raises_steam_api_error():
    with pytest.raises(SteamApiError):
        _call(lambda r: httpx.Response(200, text="<html>"), "get_steam_level", "1")


def test_transport_failure_never_leaks_the_key(caplog):
    """The key rides in the request URL, and httpx embeds URLs in its error text."""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError(f"cannot connect to {request.url}")

    with caplog.at_level(logging.DEBUG), pytest.raises(SteamApiError) as info:
        _call(handler, "get_steam_level", "1")

    assert KEY not in str(info.value)
    assert KEY not in caplog.text
    assert info.value.__cause__ is None
