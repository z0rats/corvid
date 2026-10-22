"""Parsers for Telegram's public web pages: the `t.me/<name>` contact card and the `t.me/s/<name>`
message preview. HTML scraping, so every selector the result depends on is checked and a changed
page raises `SourceDriftError` rather than reading as an empty channel."""

import datetime
import re
from dataclasses import dataclass, field
from typing import Literal

from bs4 import BeautifulSoup, Tag

from app.core.external_sources.contract import SourceDriftError
from app.features.telegram_search.utils.channel_name import RESERVED_PATHS

ChannelKind = Literal["channel", "group", "user", "unknown"]

_PROFILE_LABEL = "Telegram profile page"
_PREVIEW_LABEL = "Telegram channel preview"
_NOT_FOUND_TITLE_PREFIX = "Telegram: Contact @"
_COUNT_RE = re.compile(r"^\s*([\d.,]+)\s*([KMB]?)\s*$", re.IGNORECASE)
_SUFFIX = {"": 1, "K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
_POST_ID_RE = re.compile(r"^[^/]+/(\d+)$")
_BEFORE_RE = re.compile(r"[?&]before=(\d+)")
_MEDIA_SELECTOR = (
    ".tgme_widget_message_photo_wrap, .tgme_widget_message_video_player, "
    ".tgme_widget_message_document_wrap, .tgme_widget_message_roundvideo_player, "
    ".tgme_widget_message_voice_player, .tgme_widget_message_sticker_wrap"
)
_TME_LINK_RE = re.compile(
    r"^(?:https?:)?//(?:www\.)?(?:t\.me|telegram\.me)/(?:s/)?([A-Za-z][A-Za-z0-9_]{3,31})(?:/|$|\?)"
)


@dataclass(frozen=True)
class ChannelProfile:
    title: str
    kind: ChannelKind
    member_count: int | None
    online_count: int | None
    description: str | None
    description_links: list[str]
    verified: bool
    photo_url: str | None


@dataclass(frozen=True)
class ForwardSource:
    name: str | None
    # Set only when Telegram links the source - a public channel. A private channel or a user
    # who allows forward attribution shows a name only; a hidden one shows neither.
    username: str | None


@dataclass(frozen=True)
class PreviewPost:
    id: int
    url: str
    date: datetime.datetime | None
    views: int | None
    text: str
    links: list[str]
    forwarded_from: ForwardSource | None
    has_media: bool
    is_service: bool


@dataclass(frozen=True)
class PreviewPage:
    posts: list[PreviewPost]
    # The `before=` cursor of the next-older page, or None on the channel's oldest page.
    older_cursor: int | None
    counters: dict[str, int] = field(default_factory=dict)


def parse_count(text: str) -> int | None:
    """`83 253`, `10.3M`, `32.1K`, `239` -> int. None when there is no number at all."""
    compact = text.replace("\xa0", "").replace(" ", "")
    match = _COUNT_RE.match(compact)
    if not match:
        return None
    number, suffix = match.groups()
    if suffix:
        return int(round(float(number.replace(",", ".")) * _SUFFIX[suffix.upper()]))
    return int(number.replace(",", "").replace(".", ""))


def channel_from_link(href: str | None) -> str | None:
    """Lowercase channel username from a `t.me/<name>[/<post>]` link, or None."""
    match = _TME_LINK_RE.match(href or "")
    if not match or match.group(1).lower() in RESERVED_PATHS:
        return None
    return match.group(1).lower()


def _attr(tag: Tag, name: str) -> str | None:
    """A single-valued attribute as `str` (bs4 types it as possibly a list)."""
    value = tag.get(name)
    return value if isinstance(value, str) else None


def _hrefs(tag: Tag) -> list[str]:
    return [href for a in tag.select("a[href]") if (href := _attr(a, "href"))]


def _text_with_breaks(tag: Tag) -> str:
    """The tag's text with `<br>` as newlines (bs4's `get_text` drops them)."""
    for br in tag.find_all("br"):
        br.replace_with("\n")
    return tag.get_text("").strip()


def _parse_extra(extra: str | None) -> tuple[ChannelKind, int | None, int | None]:
    """`83 253 subscribers` (channel), `94 201 members, 4 780 online` (group), `@name` (user)."""
    if not extra:
        return "unknown", None, None
    text = extra.strip()
    if text.startswith("@"):
        return "user", None, None
    parts = [p.strip() for p in text.split(",")]
    kind: ChannelKind = "unknown"
    members = online = None
    for part in parts:
        number, _, word = part.rpartition(" ")
        word = word.lower()
        if word.startswith("subscriber"):
            kind, members = "channel", parse_count(number)
        elif word.startswith("member"):
            kind, members = "group", parse_count(number)
        elif word == "online":
            online = parse_count(number)
    return kind, members, online


def parse_profile_page(html: str) -> ChannelProfile | None:
    """The `t.me/<name>` card. None when no public chat has this username - Telegram answers
    200 with a generic "Contact @name" card then, not a 404."""
    soup = BeautifulSoup(html, "lxml")
    title_tag = soup.select_one(".tgme_page_title")
    if title_tag is None:
        og_title = soup.find("meta", property="og:title")
        if og_title and str(og_title.get("content", "")).startswith(_NOT_FOUND_TITLE_PREFIX):
            return None
        raise SourceDriftError(
            f"{_PROFILE_LABEL}: page layout changed - no title and no not-found marker"
        )

    extra_tag = soup.select_one(".tgme_page_extra")
    kind, members, online = _parse_extra(extra_tag.get_text(" ") if extra_tag else None)

    description = None
    description_links: list[str] = []
    description_tag = soup.select_one(".tgme_page_description")
    if description_tag is not None:
        description_links = _hrefs(description_tag)
        description = _text_with_breaks(description_tag) or None

    verified_icon = title_tag.select_one(".verified-icon")
    if verified_icon is not None:
        verified_icon.decompose()
    photo = soup.select_one("img.tgme_page_photo_image")
    return ChannelProfile(
        title=title_tag.get_text(" ", strip=True),
        kind=kind,
        member_count=members,
        online_count=online,
        description=description,
        description_links=description_links,
        verified=verified_icon is not None,
        photo_url=_attr(photo, "src") if photo else None,
    )


def _parse_forward(message: Tag) -> ForwardSource | None:
    block = message.select_one(".tgme_widget_message_forwarded_from")
    if block is None:
        return None
    name_tag = block.select_one(".tgme_widget_message_forwarded_from_name")
    name = name_tag.get_text(" ", strip=True) if name_tag else ""
    username = channel_from_link(_attr(name_tag, "href")) if name_tag is not None else None
    return ForwardSource(name=name or None, username=username)


def _parse_post(message: Tag) -> PreviewPost:
    data_post = message.get("data-post") or ""
    id_match = _POST_ID_RE.match(str(data_post))
    if not id_match:
        raise SourceDriftError(f"{_PREVIEW_LABEL}: page layout changed - message without data-post")

    date_tag = message.select_one(".tgme_widget_message_date time[datetime]")
    date = None
    if date_tag is not None:
        try:
            date = datetime.datetime.fromisoformat(_attr(date_tag, "datetime") or "")
        except ValueError as exc:
            raise SourceDriftError(
                f"{_PREVIEW_LABEL}: page layout changed - unreadable post date"
            ) from exc

    views_tag = message.select_one(".tgme_widget_message_views")
    text_tag = message.select_one(".tgme_widget_message_text")
    links = _hrefs(text_tag) if text_tag is not None else []
    text = _text_with_breaks(text_tag) if text_tag is not None else ""

    return PreviewPost(
        id=int(id_match.group(1)),
        url=f"https://t.me/{data_post}",
        date=date,
        views=parse_count(views_tag.get_text()) if views_tag is not None else None,
        text=text,
        links=links,
        forwarded_from=_parse_forward(message),
        has_media=message.select_one(_MEDIA_SELECTOR) is not None,
        is_service="service_message" in (message.get("class") or []),
    )


def parse_preview_page(html: str) -> PreviewPage:
    """One page (~20 posts, oldest first) of the `t.me/s/<name>` preview."""
    soup = BeautifulSoup(html, "lxml")
    info = soup.select_one(".tgme_channel_info")
    if info is None:
        raise SourceDriftError(f"{_PREVIEW_LABEL}: page layout changed - no channel info block")
    messages = soup.select(".tgme_widget_message_wrap .tgme_widget_message")

    counters: dict[str, int] = {}
    for counter in info.select(".tgme_channel_info_counter"):
        value = counter.select_one(".counter_value")
        kind = counter.select_one(".counter_type")
        count = parse_count(value.get_text()) if value else None
        if kind is not None and count is not None:
            counters[kind.get_text(strip=True).lower()] = count

    older_cursor = None
    prev_link = soup.find("link", rel="prev")
    if prev_link is not None:
        match = _BEFORE_RE.search(str(prev_link.get("href", "")))
        if match:
            older_cursor = int(match.group(1))

    # Zero matched messages is a legitimately empty channel only if the page has nothing to page
    # back to and an empty history - otherwise the message markup was renamed.
    history = soup.select_one(".tgme_channel_history")
    if not messages and (older_cursor is not None or (history and history.find(True))):
        raise SourceDriftError(
            f"{_PREVIEW_LABEL}: page layout changed - posts present but unreadable"
        )

    return PreviewPage(
        posts=[_parse_post(m) for m in messages],
        older_cursor=older_cursor,
        counters=counters,
    )
