"""Parsers against trimmed recordings of real t.me pages (fixtures/), plus the drift cases: a
changed layout must raise `SourceDriftError`, never read as an empty or missing channel."""

import datetime
from pathlib import Path

import pytest

from app.core.external_sources.contract import SourceDriftError
from app.features.telegram_search.service.tme_parser import (
    ForwardSource,
    channel_from_link,
    parse_count,
    parse_preview_page,
    parse_profile_page,
)

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("239", 239),
        ("83 253", 83253),
        ("83\xa0253", 83253),
        ("32.1K", 32100),
        ("43K", 43000),
        ("10.3M", 10_300_000),
        ("1.31M", 1_310_000),
        ("2B", 2_000_000_000),
        ("", None),
        ("n/a", None),
    ],
)
def test_parse_count(text, expected):
    assert parse_count(text) == expected


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        ("https://t.me/Podborki/148", "podborki"),
        ("https://t.me/s/durov", "durov"),
        ("https://telegram.me/durov", "durov"),
        ("https://t.me/durov?start=x", "durov"),
        ("https://example.com/durov", None),
        ("https://t.me/+invite", None),
        ("https://t.me/joinchat/AbCdEf", None),
        ("https://t.me/addlist/folder", None),
        ("https://t.me/proxy?server=x", None),
        (None, None),
    ],
)
def test_channel_from_link(href, expected):
    assert channel_from_link(href) == expected


class TestProfilePage:
    def test_channel_card(self):
        profile = parse_profile_page(_fixture("profile_channel.html"))

        assert profile is not None
        assert profile.title == "Telegram Info"
        assert profile.kind == "channel"
        assert profile.member_count == 83253
        assert profile.online_count is None
        assert profile.description.startswith("Новости о Telegram\n\n")
        assert "https://t.me/tginfochat" in profile.description_links
        assert profile.photo_url

    def test_group_card_reports_members_and_online(self):
        profile = parse_profile_page(_fixture("profile_group.html"))

        assert profile.kind == "group"
        assert profile.member_count == 94201
        assert profile.online_count == 4780

    def test_missing_username_is_none_not_an_error(self):
        assert parse_profile_page(_fixture("profile_not_found.html")) is None

    def test_user_card_is_classified_as_user(self):
        html = (
            '<div class="tgme_page_title"><span dir="auto">Someone</span></div>'
            '<div class="tgme_page_extra">@someone</div>'
        )
        assert parse_profile_page(html).kind == "user"

    def test_verified_badge_is_a_flag_not_part_of_the_title(self):
        html = (
            '<div class="tgme_page_title"><span dir="auto">Pavel Durov</span>'
            '<i class="verified-icon"> ✔</i></div>'
            '<div class="tgme_page_extra">10 287 298 subscribers</div>'
        )
        profile = parse_profile_page(html)
        assert profile.title == "Pavel Durov"
        assert profile.verified is True

    def test_layout_change_is_drift(self):
        with pytest.raises(SourceDriftError, match="no title and no not-found marker"):
            parse_profile_page("<html><body><div class='new_layout'>x</div></body></html>")


class TestPreviewPage:
    def test_posts_cursor_and_counters(self):
        page = parse_preview_page(_fixture("preview_page.html"))

        assert [p.id for p in page.posts] == list(range(101, 109))
        assert page.older_cursor == 101
        assert page.counters["subscribers"] == 83300
        assert page.counters["photos"] == 1380

    def test_post_fields(self):
        posts = {p.id: p for p in parse_preview_page(_fixture("preview_page.html")).posts}

        first = posts[101]
        assert first.url == "https://t.me/tginfo/101"
        assert first.date == datetime.datetime(2026, 7, 13, 17, 45, 13, tzinfo=datetime.UTC)
        assert first.views == 32100
        assert first.has_media is True
        assert first.forwarded_from is None
        assert len(first.links) == 4
        assert first.text.startswith("Эксклюзивный доступ к новому Bot API\n")

        assert posts[108].text == ""

    def test_three_forward_shapes(self):
        posts = {p.id: p for p in parse_preview_page(_fixture("preview_page.html")).posts}

        assert posts[104].forwarded_from == ForwardSource(
            name="Подборки каналов", username="podborki"
        )
        # A private channel or a user who allows attribution: a name, no link.
        assert posts[106].forwarded_from == ForwardSource(name="The AnalitiQ", username=None)
        # A sender who hid the forward source.
        assert posts[107].forwarded_from == ForwardSource(name=None, username=None)

    def test_oldest_page_has_the_channel_created_service_post_and_no_cursor(self):
        page = parse_preview_page(_fixture("preview_first_page.html"))

        assert page.older_cursor is None
        [post] = page.posts
        assert post.id == 1
        assert post.is_service is True
        assert post.text == "Channel created"
        assert post.views is None

    def test_channel_with_no_posts_is_an_empty_page(self):
        page = parse_preview_page('<div class="tgme_channel_info"></div>')
        assert page.posts == []
        assert page.older_cursor is None

    def test_missing_channel_info_is_drift(self):
        with pytest.raises(SourceDriftError, match="no channel info block"):
            parse_preview_page("<html><body>redesigned</body></html>")

    def test_message_without_post_id_is_drift(self):
        html = (
            '<div class="tgme_channel_info"></div>'
            '<div class="tgme_widget_message_wrap"><div class="tgme_widget_message"></div></div>'
        )
        with pytest.raises(SourceDriftError, match="without data-post"):
            parse_preview_page(html)

    def test_unreadable_post_date_is_drift(self):
        html = (
            '<div class="tgme_channel_info"></div>'
            '<div class="tgme_widget_message_wrap"><div class="tgme_widget_message" '
            'data-post="x/5"><a class="tgme_widget_message_date">'
            '<time datetime="yesterday"></time></a></div></div>'
        )
        with pytest.raises(SourceDriftError, match="unreadable post date"):
            parse_preview_page(html)

    def test_posts_behind_renamed_markup_are_drift_not_an_empty_channel(self):
        html = _fixture("preview_page.html").replace("tgme_widget_message_wrap", "tgme_post_wrap")
        with pytest.raises(SourceDriftError, match="posts present but unreadable"):
            parse_preview_page(html)
