import pytest
from pydantic import ValidationError

from app.features.instagram_search.schemas.instagram_search_schemas import (
    InstagramProfileRequest,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("someuser", "someuser"),
        ("@someuser", "someuser"),
        ("SomeUser", "someuser"),
        ("  @SomeUser  ", "someuser"),
        ("user.name_123", "user.name_123"),
    ],
)
def test_normalizes_username(raw, expected):
    assert InstagramProfileRequest(username=raw).username == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "@",
        "user name",
        "user/name",
        "a" * 31,
        "user!name",
    ],
)
def test_rejects_invalid_username(raw):
    with pytest.raises(ValidationError):
        InstagramProfileRequest(username=raw)
