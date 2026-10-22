"""check_gravatar: SHA-256 of the normalized address, "Profile not found" as an empty result,
hidden accounts dropped, usernames read from account URLs (and not invented from ids), and the
`d=404` avatar check that tells a real avatar from Gravatar's default image."""

import httpx
import pytest

from app.core.external_sources.contract import SourceDriftError
from app.features.ioc_tools.ioc_lookup.single_lookup.service import gravatar_client
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import ServiceError
from tests.conftest import run as _run


def _response(status_code: int, json=None) -> httpx.Response:
    request = httpx.Request("GET", "https://api.gravatar.com/v3/profiles/x")
    return httpx.Response(status_code, request=request, json=json if json is not None else {})


class _FakeClient:
    def __init__(self, profile: httpx.Response, avatar: httpx.Response | Exception | None = None):
        self._profile = profile
        self._avatar = avatar if avatar is not None else _response(200)
        self.gets: list[str] = []
        self.heads: list[dict] = []

    async def get(self, url, **kwargs):
        self.gets.append(url)
        return self._profile

    async def head(self, url, **kwargs):
        self.heads.append({"url": url, **kwargs})
        if isinstance(self._avatar, Exception):
            raise self._avatar
        return self._avatar


def _patch_client(monkeypatch, profile, avatar=None) -> _FakeClient:
    fake = _FakeClient(profile, avatar)
    monkeypatch.setattr(gravatar_client, "get_client", lambda: fake)
    return fake


def _account(service, url, hidden=False):
    return {
        "service_type": service,
        "service_label": service.title(),
        "url": url,
        "is_hidden": hidden,
    }


_PROFILE = {
    "hash": "x",
    "display_name": "Beau Lebens",
    "profile_url": "https://gravatar.com/beau",
    "avatar_url": "https://0.gravatar.com/avatar/x",
    "location": "Golden, CO",
    "description": "Builds the web.",
    "job_title": "Lead",
    "company": "Automattic",
    "verified_accounts": [
        _account("github", "https://github.com/beaulebens"),
        _account("twitter", "https://x.com/hidden", hidden=True),
    ],
}


def test_hashes_the_normalized_address_with_sha256(monkeypatch):
    fake = _patch_client(monkeypatch, _response(200, json=_PROFILE))

    _run(gravatar_client.check_gravatar("  Beau@Example.COM "))

    expected = gravatar_client.gravatar_hash("beau@example.com")
    assert len(expected) == 64
    assert fake.gets == [f"https://api.gravatar.com/v3/profiles/{expected}"]
    assert fake.heads[0]["url"] == f"https://www.gravatar.com/avatar/{expected}"
    assert fake.heads[0]["params"] == {"d": "404"}


def test_maps_the_profile_and_drops_hidden_accounts(monkeypatch):
    _patch_client(monkeypatch, _response(200, json=_PROFILE))

    result = _run(gravatar_client.check_gravatar("beau@example.com"))

    assert result["found"] is True
    assert result["display_name"] == "Beau Lebens"
    assert result["has_avatar"] is True
    assert "hash" not in result
    assert result["verified_accounts"] == [
        {
            "service": "github",
            "label": "Github",
            "url": "https://github.com/beaulebens",
            "username": "beaulebens",
        }
    ]


def test_non_string_account_fields_are_dropped_not_stored(monkeypatch):
    odd = {"service_type": 7, "service_label": ["x"], "url": {"href": "x"}, "is_hidden": False}
    _patch_client(monkeypatch, _response(200, json={**_PROFILE, "verified_accounts": [odd]}))

    result = _run(gravatar_client.check_gravatar("beau@example.com"))

    assert result["verified_accounts"] == [
        {"service": None, "label": None, "url": None, "username": None}
    ]


@pytest.mark.parametrize(
    ("avatar", "expected"),
    [(_response(404), False), (_response(500), None), (httpx.ConnectError("down"), None)],
)
def test_avatar_check_reports_a_default_or_unknown_avatar(monkeypatch, avatar, expected):
    _patch_client(monkeypatch, _response(200, json=_PROFILE), avatar)

    assert _run(gravatar_client.check_gravatar("beau@example.com"))["has_avatar"] is expected


def test_a_long_about_is_truncated(monkeypatch):
    _patch_client(monkeypatch, _response(200, json={**_PROFILE, "description": "a" * 900}))

    result = _run(gravatar_client.check_gravatar("beau@example.com"))

    assert len(result["description"]) == 501
    assert result["description"].endswith("…")


def test_profile_not_found_is_an_empty_result_without_an_avatar_check(monkeypatch):
    fake = _patch_client(monkeypatch, _response(404, json={"error": "Profile not found"}))

    result = _run(gravatar_client.check_gravatar("nobody@example.com"))

    assert result["found"] is False
    assert result["display_name"] is None
    assert result["has_avatar"] is None
    assert result["verified_accounts"] == []
    assert fake.heads == []


def test_any_other_404_is_still_an_error(monkeypatch):
    _patch_client(monkeypatch, _response(404, json={"error": "No such route"}))

    with pytest.raises(ServiceError):
        _run(gravatar_client.check_gravatar("beau@example.com"))


def test_a_missing_verified_accounts_list_is_drift(monkeypatch):
    body = {k: v for k, v in _PROFILE.items() if k != "verified_accounts"}
    _patch_client(monkeypatch, _response(200, json=body))

    with pytest.raises(SourceDriftError):
        _run(gravatar_client.check_gravatar("beau@example.com"))


@pytest.mark.parametrize(
    ("url", "username"),
    [
        ("https://github.com/beaulebens", "beaulebens"),
        ("https://github.com/beaulebens/some-repo", "beaulebens"),
        ("https://mastodon.social/@beau/", "beau"),
        ("https://www.linkedin.com/in/beaulebens", "beaulebens"),
        ("https://www.reddit.com/user/spez", "spez"),
        ("https://www.youtube.com/@handle", "handle"),
        ("https://steamcommunity.com/id/vanity", "vanity"),
        ("https://beau.tumblr.com/", "beau"),
        ("https://www.facebook.com/beau.lebens", "beau.lebens"),
        # ids, not usernames: no pivot rather than a wrong one
        ("https://www.facebook.com/profile.php?id=100001", None),
        ("https://www.facebook.com/app_scoped_user_id/YXNpZADpBYTJY/", None),
        ("https://steamcommunity.com/profiles/76561197960287930", None),
        ("https://www.youtube.com/channel/UC123", None),
        ("https://example.com/", None),
        (None, None),
    ],
)
def test_username_from_account_url(url, username):
    assert gravatar_client.username_from_account_url(url) == username
