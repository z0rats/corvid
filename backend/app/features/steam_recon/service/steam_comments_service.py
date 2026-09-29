"""Fetches and classifies a Steam profile's comments (keyless `steamcommunity.com/comment/Profile
/render` endpoint - fixed host, confirmed live in docs/architecture/steam-recon.md's phase-0
verification) for the CS2 cheater-report's `accusatory_comments` signal.

A private profile's comment thread is unavailable, not an error - Steam answers it with
HTTP 200 and `{"success": false}`, so that's treated the same as "no comments" rather than
raised as a failure.
"""

import dataclasses
import logging

import httpx
from bs4 import BeautifulSoup

from app.features.steam_recon.config.cheater_scoring_config import ACCUSATION_LEXICON
from app.features.steam_recon.utils.steam_id_utils import account_id_to_steamid64

logger = logging.getLogger(__name__)

COMMENTS_URL_TEMPLATE = "https://steamcommunity.com/comment/Profile/render/{steamid}/-1/"
COMMENTS_TIMEOUT = 15.0
DEFAULT_MAX_COMMENTS = 200


@dataclasses.dataclass
class ProfileComment:
    author_steamid64: str | None
    text: str
    timestamp: int | None


def _parse_comments_html(html: str) -> list[ProfileComment]:
    soup = BeautifulSoup(html, "lxml")
    comments = []
    for node in soup.select(".commentthread_comment"):
        author_link = node.select_one(".commentthread_author_link")
        account_id = None
        if author_link and (raw_id := author_link.get("data-miniprofile")):
            try:
                account_id = int(str(raw_id))
            except ValueError:
                account_id = None

        text_node = node.select_one(".commentthread_comment_text")
        timestamp_node = node.select_one(".commentthread_comment_timestamp[data-timestamp]")
        timestamp = None
        if timestamp_node and (raw_timestamp := timestamp_node.get("data-timestamp")):
            try:
                timestamp = int(str(raw_timestamp))
            except ValueError:
                timestamp = None

        comments.append(
            ProfileComment(
                author_steamid64=account_id_to_steamid64(account_id) if account_id else None,
                text=(text_node.get_text(strip=True) if text_node else ""),
                timestamp=timestamp,
            )
        )
    return comments


async def fetch_profile_comments(
    steamid64: str, max_comments: int = DEFAULT_MAX_COMMENTS
) -> list[ProfileComment] | None:
    """Returns the profile's comments (newest first, as Steam orders them), or None if the
    comment thread is private/unavailable."""
    try:
        async with httpx.AsyncClient(timeout=COMMENTS_TIMEOUT) as client:
            response = await client.get(
                COMMENTS_URL_TEMPLATE.format(steamid=steamid64),
                params={"start": 0, "count": max_comments},
            )
        if response.status_code != 200:
            return None
        data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("Steam comments fetch failed for %s: %s", steamid64, type(exc).__name__)
        return None

    if not data.get("success"):
        return None
    return _parse_comments_html(data.get("comments_html") or "")


def classify_accusatory_ratio(
    comments: list[ProfileComment], target_steamid64: str
) -> tuple[float, int]:
    """Fraction of comments (excluding the target's own) matching the accusation lexicon, and
    the sample size that ratio was computed over."""
    others = [c for c in comments if c.author_steamid64 != target_steamid64]
    if not others:
        return 0.0, 0

    lexicon = tuple(term.lower() for term in ACCUSATION_LEXICON)
    matches = sum(1 for c in others if any(term in c.text.lower() for term in lexicon))
    return matches / len(others), len(others)
