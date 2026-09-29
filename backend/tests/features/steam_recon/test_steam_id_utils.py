import pytest

from app.features.steam_recon.utils.steam_id_utils import (
    SteamTarget,
    account_id_to_steamid64,
    is_steamid64,
    parse_steam_target,
    steamid64_to_account_id,
)

# Robin Walker's public profile: account id 169802 == STEAM_0:0:84901 == [U:1:169802]
ID64 = "76561197960435530"
RESOLVED = SteamTarget("steamid64", ID64)


@pytest.mark.parametrize(
    "raw",
    [
        ID64,
        f"  {ID64}  ",
        "[U:1:169802]",
        "U:1:169802",
        "[u:1:169802]",
        "STEAM_0:0:84901",
        "STEAM_1:0:84901",
        "steam_0:0:84901",
        f"https://steamcommunity.com/profiles/{ID64}",
        f"https://steamcommunity.com/profiles/{ID64}/",
        f"http://www.steamcommunity.com/profiles/{ID64}/friends?foo=bar",
        f"steamcommunity.com/profiles/{ID64}",
    ],
)
def test_parse_steam_target_resolves_every_id_shape_to_steamid64(raw):
    assert parse_steam_target(raw) == RESOLVED


@pytest.mark.parametrize(
    "raw, vanity",
    [
        ("robinwalker", "robinwalker"),
        ("  robin_walker-1  ", "robin_walker-1"),
        ("https://steamcommunity.com/id/robinwalker", "robinwalker"),
        ("https://steamcommunity.com/id/robinwalker/", "robinwalker"),
        ("https://www.steamcommunity.com/id/robinwalker/games/?tab=all", "robinwalker"),
        ("steamcommunity.com/id/robinwalker", "robinwalker"),
        ("12345", "12345"),
    ],
)
def test_parse_steam_target_returns_vanity_for_names_and_id_urls(raw, vanity):
    assert parse_steam_target(raw) == SteamTarget("vanity", vanity)


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        None,
        "a",
        "has space",
        "bad!chars",
        "x" * 33,
        # 17 digits but outside the individual-account SteamID64 range
        "12345678901234567",
        "99999999999999999",
        # 32-bit account-id overflow / zero
        "[U:1:0]",
        "[U:1:99999999999]",
        "STEAM_0:0:0",
        # wrong universe / malformed
        "[G:1:169802]",
        "STEAM_9:0:84901",
        "STEAM_0:2:84901",
        # a non-Steam host must never be accepted, even with a Steam-looking path
        f"https://evil.example/profiles/{ID64}",
        f"https://steamcommunity.com.evil.example/profiles/{ID64}",
        "https://evil.example/id/robinwalker",
        # right host, wrong/missing path
        "https://steamcommunity.com/",
        "https://steamcommunity.com/profiles/",
        "https://steamcommunity.com/profiles/notanid",
        "https://steamcommunity.com/groups/valve",
        "https://steamcommunity.com/id/bad!vanity",
    ],
)
def test_parse_steam_target_rejects_unrecognized_input(raw):
    assert parse_steam_target(raw) is None


def test_is_steamid64_bounds():
    assert is_steamid64(ID64)
    assert is_steamid64("76561197960265729")  # account id 1
    assert not is_steamid64("76561197960265728")  # account id 0
    assert not is_steamid64("76561197960265727")
    assert not is_steamid64("76561202255233024")  # one past the 32-bit account-id range
    assert not is_steamid64("7656119796043553")  # 16 digits
    assert not is_steamid64("7656119796043553x")


def test_account_id_round_trip():
    assert account_id_to_steamid64(169802) == ID64
    assert steamid64_to_account_id(ID64) == 169802
