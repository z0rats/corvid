import asyncio

import httpx
import pytest

from app.core.exceptions import AppHTTPException
from app.features.steam_recon.schemas.steam_recon_schemas import ProfileRequest
from app.features.steam_recon.service import steam_profile_service
from app.features.steam_recon.service.steam_api_client import SteamApiClient

ID64 = "76561197960435530"

SUMMARY = {
    "steamid": ID64,
    "personaname": "Robin",
    "realname": "Robin Walker",
    "profileurl": "https://steamcommunity.com/id/robinwalker/",
    "avatarfull": "https://avatars.example/full.jpg",
    "communityvisibilitystate": 3,
    "timecreated": 1063324800,
    "lastlogoff": 1700000000,
    "loccountrycode": "US",
    "locstatecode": "WA",
    "loccityid": 1234,
}
BANS = {
    "SteamId": ID64,
    "CommunityBanned": False,
    "VACBanned": True,
    "NumberOfVACBans": 1,
    "DaysSinceLastBan": 30,
    "NumberOfGameBans": 0,
    "EconomyBan": "none",
}


def _lookup(target: str):
    return asyncio.run(
        steam_profile_service.perform_profile_lookup(ProfileRequest(target=target), db=None)
    )


@pytest.fixture
def steam(monkeypatch):
    """Serve canned Steam responses through a real client on a mock transport.

    `routes` maps an API path to a response (or a callable returning one); `state` is the
    configured key (None simulates 'no key set').
    """
    routes: dict = {
        "/ISteamUser/GetPlayerSummaries/v2/": httpx.Response(
            200, json={"response": {"players": [SUMMARY]}}
        ),
        "/ISteamUser/GetPlayerBans/v1/": httpx.Response(200, json={"players": [BANS]}),
        "/IPlayerService/GetSteamLevel/v1/": httpx.Response(
            200, json={"response": {"player_level": 12}}
        ),
        "/IPlayerService/GetOwnedGames/v1/": httpx.Response(
            200, json={"response": {"game_count": 34}}
        ),
    }
    state = {"key": "test-key"}
    requested: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requested.append(request.url.path)
        response = routes[request.url.path]
        return response(request) if callable(response) else response

    async def fake_key(db):
        return state["key"]

    async def fake_names(country, state_code, city_id):
        return {"country": "United States", "state": "Washington", "city": "Bellevue"}

    monkeypatch.setattr(steam_profile_service, "get_steam_api_key", fake_key)
    monkeypatch.setattr(steam_profile_service, "resolve_location_names", fake_names)
    monkeypatch.setattr(
        steam_profile_service,
        "SteamApiClient",
        lambda key: SteamApiClient(key, transport=httpx.MockTransport(handler)),
    )
    return type("Steam", (), {"routes": routes, "state": state, "requested": requested})


def test_full_profile_is_assembled_from_every_source(steam):
    result = _lookup(ID64)

    profile = result.profile
    assert profile.steamid64 == ID64
    assert profile.persona_name == "Robin"
    assert profile.visibility == "public"
    assert profile.level == 12
    assert profile.game_count == 34
    assert profile.bans is not None
    assert profile.bans.vac_banned is True
    assert profile.bans.number_of_vac_bans == 1
    assert profile.bans.days_since_last_ban == 30
    assert profile.location is not None
    assert (profile.location.country_code, profile.location.city) == ("US", "Bellevue")
    assert any(link.id == "steamid_io" and ID64 in link.url for link in result.quick_links)


def test_vanity_names_are_resolved_before_the_lookup(steam):
    steam.routes["/ISteamUser/ResolveVanityURL/v1/"] = httpx.Response(
        200, json={"response": {"success": 1, "steamid": ID64}}
    )

    assert _lookup("https://steamcommunity.com/id/robinwalker").profile.steamid64 == ID64
    assert steam.requested[0] == "/ISteamUser/ResolveVanityURL/v1/"


def test_a_steamid64_target_skips_vanity_resolution(steam):
    _lookup(ID64)
    assert "/ISteamUser/ResolveVanityURL/v1/" not in steam.requested


def test_unknown_vanity_is_a_404(steam):
    steam.routes["/ISteamUser/ResolveVanityURL/v1/"] = httpx.Response(
        200, json={"response": {"success": 42}}
    )
    with pytest.raises(AppHTTPException) as info:
        _lookup("nobody-here")
    assert (info.value.status_code, info.value.error_code) == (404, "STEAM_PROFILE_NOT_FOUND")


def test_unrecognized_target_is_a_400_and_makes_no_requests(steam):
    with pytest.raises(AppHTTPException) as info:
        _lookup("https://evil.example/profiles/" + ID64)
    assert (info.value.status_code, info.value.error_code) == (400, "STEAM_INVALID_TARGET")
    assert steam.requested == []


def test_missing_key_is_a_400(steam):
    steam.state["key"] = None
    with pytest.raises(AppHTTPException) as info:
        _lookup(ID64)
    assert (info.value.status_code, info.value.error_code) == (400, "STEAM_NOT_CONFIGURED")
    assert steam.requested == []


def test_no_summary_for_the_id_is_a_404(steam):
    steam.routes["/ISteamUser/GetPlayerSummaries/v2/"] = httpx.Response(
        200, json={"response": {"players": []}}
    )
    with pytest.raises(AppHTTPException) as info:
        _lookup(ID64)
    assert info.value.status_code == 404


def test_private_extras_degrade_to_none_instead_of_failing(steam):
    steam.routes["/IPlayerService/GetSteamLevel/v1/"] = httpx.Response(200, json={"response": {}})
    steam.routes["/IPlayerService/GetOwnedGames/v1/"] = httpx.Response(200, json={"response": {}})
    steam.routes["/ISteamUser/GetPlayerBans/v1/"] = httpx.Response(500)

    profile = _lookup(ID64).profile

    assert (profile.level, profile.game_count, profile.bans) == (None, None, None)
    assert profile.persona_name == "Robin"


def test_profile_without_location_or_visibility_fields(steam):
    steam.routes["/ISteamUser/GetPlayerSummaries/v2/"] = httpx.Response(
        200, json={"response": {"players": [{"steamid": ID64, "communityvisibilitystate": 1}]}}
    )

    profile = _lookup(ID64).profile

    assert profile.visibility == "private"
    assert profile.location is None
    assert profile.created_at is None


@pytest.mark.parametrize(
    "status, expected_status, expected_code",
    [
        (403, 403, "STEAM_KEY_REJECTED"),
        (429, 429, "STEAM_RATE_LIMITED"),
        (500, 502, "STEAM_API_ERROR"),
    ],
)
def test_summary_failures_map_to_http_errors(steam, status, expected_status, expected_code):
    steam.routes["/ISteamUser/GetPlayerSummaries/v2/"] = httpx.Response(status)
    with pytest.raises(AppHTTPException) as info:
        _lookup(ID64)
    assert (info.value.status_code, info.value.error_code) == (expected_status, expected_code)


def test_a_rejected_key_on_an_optional_call_still_fails_the_lookup(steam):
    steam.routes["/IPlayerService/GetSteamLevel/v1/"] = httpx.Response(403)
    with pytest.raises(AppHTTPException) as info:
        _lookup(ID64)
    assert info.value.error_code == "STEAM_KEY_REJECTED"
