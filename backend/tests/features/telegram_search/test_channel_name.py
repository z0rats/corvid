import pytest

from app.features.telegram_search.utils.channel_name import PRIVATE_LINK_MESSAGE, normalize_channel


@pytest.mark.parametrize(
    "raw",
    [
        "durov",
        "@durov",
        "  @Durov  ",
        "t.me/durov",
        "https://t.me/durov",
        "https://t.me/s/durov",
        "https://t.me/durov/531",
        "https://t.me/s/durov?before=300",
        "http://www.t.me/durov",
        "telegram.me/durov",
        "https://telegram.dog/durov",
        "tg://resolve?domain=durov",
    ],
)
def test_every_accepted_shape_normalizes_to_the_lowercase_username(raw):
    assert normalize_channel(raw) == "durov"


@pytest.mark.parametrize(
    "raw", ["https://t.me/+AbCdEf123", "t.me/joinchat/AbCdEf123", "https://t.me/c/1234567/89"]
)
def test_private_links_are_rejected_with_their_own_message(raw):
    with pytest.raises(ValueError, match="private invite link"):
        normalize_channel(raw)
    assert "public channels" in PRIVATE_LINK_MESSAGE


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "abc",  # too short
        "a" * 33,  # too long
        "1channel",  # must start with a letter
        "bad-name",
        "@",
        "+15551234567",
        "https://example.com/durov",
        "https://t.me/",
        "https://t.me/addstickers/pack",
        "https://t.me/share/url?url=x",
    ],
)
def test_invalid_values_are_rejected(raw):
    with pytest.raises(ValueError):
        normalize_channel(raw)
