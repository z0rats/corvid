"""Activity metrics and indicators computed from a sample of a channel's preview posts. Pure
functions over parsed posts - no I/O."""

import re
import statistics
from collections import Counter
from urllib.parse import urlsplit

from app.features.ioc_tools.ioc_extractor.service.ioc_extractor_service import extract_iocs
from app.features.telegram_search.config.telegram_search_config import (
    MAX_INDICATORS_PER_TYPE,
    POST_TEXT_MAX_CHARS,
    TELEGRAM_DOMAINS,
    TOP_FORWARD_SOURCES_N,
    TOP_MENTIONS_N,
    TOP_POSTS_N,
)
from app.features.telegram_search.schemas.telegram_search_schemas import (
    ChannelMetrics,
    ForwardSourceStat,
    MentionStat,
    SampledPost,
)
from app.features.telegram_search.service.tme_parser import PreviewPost, channel_from_link

# `@name` not preceded by a word character, so `user@example.com` is not a mention.
_MENTION_RE = re.compile(r"(?<![\w@.])@([A-Za-z][A-Za-z0-9_]{3,31})\b")
_INDICATOR_TYPES = ("urls", "domains", "ips", "emails", "cves", "md5", "sha1", "sha256")


def _ratio(part: int, whole: int) -> float | None:
    return round(part / whole, 4) if whole else None


def _forward_stat(post: PreviewPost, count: int = 1) -> ForwardSourceStat | None:
    source = post.forwarded_from
    if source is None:
        return None
    return ForwardSourceStat(name=source.name, username=source.username, count=count)


def to_sampled_post(post: PreviewPost) -> SampledPost:
    text = post.text
    if len(text) > POST_TEXT_MAX_CHARS:
        text = text[: POST_TEXT_MAX_CHARS - 1].rstrip() + "…"
    return SampledPost(
        id=post.id,
        url=post.url,
        date=post.date,
        views=post.views,
        text=text,
        forwarded_from=_forward_stat(post),
        has_media=post.has_media,
        link_count=len(post.links),
    )


def _top_forward_sources(posts: list[PreviewPost]) -> list[ForwardSourceStat]:
    """Most-reposted sources. A linked source is keyed by username, a named-only one by name;
    every hidden sender folds into one `name=None, username=None` row."""
    counts: Counter[tuple[str | None, str | None]] = Counter()
    names: dict[tuple[str | None, str | None], str | None] = {}
    for post in posts:
        source = post.forwarded_from
        if source is None:
            continue
        key = (source.username, None) if source.username else (None, source.name)
        counts[key] += 1
        names.setdefault(key, source.name)
    return [
        ForwardSourceStat(name=names[key], username=key[0], count=count)
        for key, count in counts.most_common(TOP_FORWARD_SOURCES_N)
    ]


def _top_mentions(posts: list[PreviewPost], own_username: str) -> list[MentionStat]:
    """Channels a post links to (t.me links) or names (@mentions), counted once per post, the
    channel itself excluded - who a channel promotes is a pivot, like its forward sources."""
    counts: Counter[str] = Counter()
    for post in posts:
        mentioned = {name.lower() for name in _MENTION_RE.findall(post.text)}
        mentioned.update(filter(None, (channel_from_link(link) for link in post.links)))
        if post.forwarded_from and post.forwarded_from.username:
            mentioned.discard(post.forwarded_from.username)
        mentioned.discard(own_username)
        counts.update(mentioned)
    return [
        MentionStat(username=name, count=count)
        for name, count in counts.most_common(TOP_MENTIONS_N)
    ]


def compute_metrics(
    posts: list[PreviewPost], own_username: str, member_count: int | None
) -> ChannelMetrics:
    """`posts` are the sampled regular posts (service messages already dropped)."""
    dates = sorted(p.date for p in posts if p.date is not None)
    views = [p.views for p in posts if p.views is not None]
    forwarded = sum(1 for p in posts if p.forwarded_from is not None)

    posts_per_day = None
    if len(dates) >= 2:
        span_days = (dates[-1] - dates[0]).total_seconds() / 86400
        if span_days > 0:
            # N posts span N-1 intervals.
            posts_per_day = round((len(dates) - 1) / span_days, 2)

    avg_views = round(statistics.fmean(views)) if views else None
    return ChannelMetrics(
        posts_sampled=len(posts),
        first_sampled_at=dates[0] if dates else None,
        last_post_at=dates[-1] if dates else None,
        posts_per_day=posts_per_day,
        avg_views=avg_views,
        median_views=round(statistics.median(views)) if views else None,
        max_views=max(views) if views else None,
        views_to_members=(
            round(avg_views / member_count, 4) if avg_views is not None and member_count else None
        ),
        forwarded_count=forwarded,
        forwarded_ratio=_ratio(forwarded, len(posts)),
        media_ratio=_ratio(sum(1 for p in posts if p.has_media), len(posts)),
        top_forward_sources=_top_forward_sources(posts),
        top_mentions=_top_mentions(posts, own_username),
    )


def top_posts(posts: list[PreviewPost]) -> list[SampledPost]:
    ranked = sorted(
        (p for p in posts if p.views is not None), key=lambda p: p.views or 0, reverse=True
    )
    return [to_sampled_post(p) for p in ranked[:TOP_POSTS_N]]


def _is_telegram_host(value: str) -> bool:
    host = ((urlsplit(value).hostname or "") if "://" in value else value).lower().rstrip(".")
    return any(host == d or host.endswith(f".{d}") for d in TELEGRAM_DOMAINS)


def extract_indicators(posts: list[PreviewPost], description: str | None) -> dict[str, list[str]]:
    """IOCs from post text, link targets and the channel description via `ioc_extractor`,
    minus Telegram's own hosts. Only non-empty types are returned, each capped."""
    chunks = [description or ""]
    for post in posts:
        chunks.append(post.text)
        chunks.extend(post.links)
    content = "\n".join(chunk for chunk in chunks if chunk)
    try:
        extracted = extract_iocs(content)
    except ValueError:
        # extract_iocs rejects empty/too-short content - a channel with nothing to extract.
        return {}

    indicators: dict[str, list[str]] = {}
    for ioc_type in _INDICATOR_TYPES:
        values = getattr(extracted, ioc_type)
        if ioc_type in ("urls", "domains"):
            values = [v for v in values if not _is_telegram_host(v)]
        if values:
            indicators[ioc_type] = values[:MAX_INDICATORS_PER_TYPE]
    return indicators
