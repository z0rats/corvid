"""reddit_search runs as investigation items: report sections and graph entities."""

import datetime
from collections import Counter
from typing import Any

from app.core.entities.model import Extraction, entity
from app.core.reports.schemas import ReportRow, ReportSection
from app.core.run_sources.source import RunSource
from app.features.reddit_search.crud.reddit_search_crud import get_search_with_results
from app.features.reddit_search.models.reddit_search_models import RedditSearch

# The report lists the newest items and the busiest subreddits, not a user's full history -
# the full set stays in the feature's own JSON export.
REPORT_ITEM_LIMIT = 50
TOP_SUBREDDITS = 15
_SNIPPET_LENGTH = 200


def _snippet(text: str | None) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= _SNIPPET_LENGTH else text[:_SNIPPET_LENGTH].rstrip() + "…"


def _date(unix: int) -> str:
    return datetime.datetime.fromtimestamp(unix, datetime.UTC).strftime("%Y-%m-%d")


def _top_subreddits(search: RedditSearch) -> list[tuple[str, int]]:
    return Counter(result.subreddit for result in search.results).most_common(TOP_SUBREDDITS)


def build_sections(search: RedditSearch, locale: str) -> list[ReportSection]:
    posts = sum(result.kind == "post" for result in search.results)
    removed = sum(result.removed or result.deleted for result in search.results)
    summary = ReportSection(
        title="Reddit search",
        rows=[
            ReportRow("Username", f"u/{search.username}"),
            ReportRow("Searched at", search.searched_at.strftime("%Y-%m-%d %H:%M UTC")),
            ReportRow("Posts", str(posts)),
            ReportRow("Comments", str(len(search.results) - posts)),
            ReportRow("Removed or deleted", str(removed)),
        ],
    )
    if search.subreddit_filter:
        summary.rows.append(ReportRow("Subreddit filter", f"r/{search.subreddit_filter}"))
    sections = [summary]

    subreddits = _top_subreddits(search)
    if subreddits:
        sections.append(
            ReportSection(
                title="Most active subreddits",
                rows=[ReportRow(f"r/{name}", str(count)) for name, count in subreddits],
            )
        )

    newest = search.results[:REPORT_ITEM_LIMIT]
    if newest:
        sections.append(
            ReportSection(
                title=f"Newest {len(newest)} of {len(search.results)} items",
                rows=[
                    ReportRow(
                        f"{_date(result.created_utc)} · r/{result.subreddit}",
                        _snippet(result.title or result.body) or "-",
                        href=f"https://www.reddit.com{result.permalink}",
                    )
                    for result in newest
                ],
            )
        )
    return sections


def extract_entities(search: RedditSearch) -> Extraction:
    root = entity("username", search.username, f"u/{search.username}")
    out = Extraction(root=root)
    for name, _count in _top_subreddits(search):
        out.link(root, entity("subreddit", name, f"r/{name}"), "active in")
    return out


def _target(search: Any) -> str:
    return search.username


REDDIT_SEARCH_RUN_SOURCE = RunSource(
    feature="reddit_search",
    label="Reddit search",
    model=RedditSearch,
    load=get_search_with_results,
    target=_target,
    build_sections=build_sections,
    extract=extract_entities,
)
