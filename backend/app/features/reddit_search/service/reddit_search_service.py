import asyncio
import re
from urllib.parse import urlencode

import httpx

ARCTIC_BASE = "https://arctic-shift.photon-reddit.com"
PULLPUSH_BASE = "https://api.pullpush.io"
LIMIT = 100

DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=10.0, pool=5.0)

_REDDIT_URL_RE = re.compile(r"^https?://(www\.|old\.|new\.)?reddit\.com", re.IGNORECASE)
_LEADING_SLASHES_RE = re.compile(r"^/+")
_USER_PREFIX_RE = re.compile(r"^(u|user)/", re.IGNORECASE)
_TRAILING_JUNK_RE = re.compile(r"[/?#].*$")


def normalize_username(raw: str) -> str:
    """Strip whatever a user might paste around a username: a full reddit.com
    profile URL, leading slashes, a u//user/ prefix, a leading @, or trailing
    path/query/fragment junk. Mirrors Rosint's normalizeUsername()."""
    s = (raw or "").strip()
    s = _REDDIT_URL_RE.sub("", s)
    s = _LEADING_SLASHES_RE.sub("", s)
    s = _USER_PREFIX_RE.sub("", s)
    s = s.lstrip("@")
    s = _TRAILING_JUNK_RE.sub("", s)
    return s.strip()


def _build_urls(
    username: str,
    kind: str,
    *,
    subreddit: str | None,
    date_from: int | None,
    date_to: int | None,
    include_nsfw: bool,
    cursor_before: int | None,
    cursor_after: int | None,
) -> tuple[str, str]:
    """Build the parallel Arctic Shift / PullPush query URLs for one page of a
    user's post or comment history. Mirrors Rosint's buildUrls()."""
    params: list[tuple[str, str]] = [
        ("limit", str(LIMIT)),
        ("sort", "desc"),
        ("author", username),
    ]
    if subreddit:
        params.append(("subreddit", subreddit))
    if kind == "posts" and not include_nsfw:
        params.append(("over_18", "false"))

    before = cursor_before if cursor_before is not None else date_to
    after = cursor_after if cursor_after is not None else date_from
    if before is not None:
        params.append(("before", str(before)))
    if after is not None:
        params.append(("after", str(after)))

    query = urlencode(params)
    arctic_path = "posts/search" if kind == "posts" else "comments/search"
    pullpush_path = "submission" if kind == "posts" else "comment"

    arctic_url = f"{ARCTIC_BASE}/api/{arctic_path}?{query}"
    # PullPush requires a bare `?test` flag ahead of the real params to return results.
    pullpush_url = f"{PULLPUSH_BASE}/reddit/search/{pullpush_path}/?test&{query}"
    return arctic_url, pullpush_url


def _get_status(item: dict, kind: str) -> tuple[bool, bool]:
    """Mirrors Rosint's getStatus(): detect moderator-removed vs author-deleted content."""
    text = item.get("selftext") if kind == "posts" else item.get("body")
    removed = text == "[removed]" or (kind == "posts" and bool(item.get("removed_by_category")))
    deleted = text == "[deleted]" or item.get("author") == "[deleted]"
    return removed, deleted


async def _safe_fetch(client: httpx.AsyncClient, url: str) -> list[dict] | None:
    """Returns the archive's `data` array, or None if the request failed (distinct
    from an empty-but-successful response, needed for accurate `sources`/down detection)."""
    try:
        response = await client.get(url, headers={"Accept": "application/json"})
        if response.status_code != 200:
            return None
        body = response.json()
        return body.get("data") or []
    except (httpx.HTTPError, ValueError):
        return None


def _merge_and_sort(
    arctic_items: list[dict] | None,
    pullpush_items: list[dict] | None,
    kind: str,
    include_nsfw: bool,
) -> list[dict]:
    """Dedupe by Reddit item ID (Arctic Shift wins ties, since it's merged first)
    and sort desc by created_utc. Pulled out of fetch_both() so this logic is
    testable without a network round-trip."""
    seen: set[str] = set()
    merged: list[dict] = []
    for item in (arctic_items or []) + (pullpush_items or []):
        item_id = item.get("id")
        if item_id and item_id not in seen:
            seen.add(item_id)
            merged.append(item)

    # PullPush ignores over_18 server-side, so filter client-side (posts only;
    # comments have no over_18 field). Arctic results already match this filter.
    if kind == "posts" and not include_nsfw:
        merged = [p for p in merged if p.get("over_18") is False]

    merged.sort(key=lambda i: i.get("created_utc") or 0, reverse=True)
    return merged


async def fetch_both(
    username: str,
    kind: str,
    *,
    subreddit: str | None = None,
    date_from: int | None = None,
    date_to: int | None = None,
    include_nsfw: bool = True,
    cursor_before: int | None = None,
    cursor_after: int | None = None,
) -> tuple[list[dict], list[str], bool]:
    """Query Arctic Shift and PullPush in parallel for one page of a user's post/
    comment history, merge+dedupe by Reddit item ID, and sort desc by created_utc.
    Mirrors Rosint's fetchBoth(). Returns (items, sources, arctic_down)."""
    arctic_url, pullpush_url = _build_urls(
        username,
        kind,
        subreddit=subreddit,
        date_from=date_from,
        date_to=date_to,
        include_nsfw=include_nsfw,
        cursor_before=cursor_before,
        cursor_after=cursor_after,
    )

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        arctic_items, pullpush_items = await asyncio.gather(
            _safe_fetch(client, arctic_url),
            _safe_fetch(client, pullpush_url),
        )

    sources: list[str] = []
    if arctic_items:
        sources.append("Arctic Shift")
    if pullpush_items:
        sources.append("PullPush")
    arctic_down = arctic_items is None

    merged = _merge_and_sort(arctic_items, pullpush_items, kind, include_nsfw)
    return merged, sources, arctic_down


def to_result_row(item: dict, kind: str) -> dict:
    """Map a raw Arctic Shift / PullPush item into RedditSearchResult column values"""
    removed, deleted = _get_status(item, kind)
    singular_kind = "post" if kind == "posts" else "comment"
    return {
        "kind": singular_kind,
        "reddit_id": item.get("id"),
        "subreddit": item.get("subreddit") or "",
        "title": item.get("title"),
        "body": item.get("selftext") if kind == "posts" else item.get("body"),
        "score": item.get("score") or 0,
        "num_comments": item.get("num_comments") if kind == "posts" else None,
        "permalink": item.get("permalink") or "",
        "created_utc": int(item.get("created_utc") or 0),
        "over_18": bool(item.get("over_18")),
        "removed": removed,
        "deleted": deleted,
        "extra": {
            "domain": item.get("domain"),
            "is_self": item.get("is_self"),
            "link_flair_text": item.get("link_flair_text"),
            "distinguished": item.get("distinguished"),
            "spoiler": item.get("spoiler"),
        },
    }
