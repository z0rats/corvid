from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.features.reddit_search.models.reddit_search_models import RedditSearch, RedditSearchResult


async def create_search(
    db: AsyncSession,
    username: str,
    *,
    subreddit_filter: str | None,
    date_from: int | None,
    date_to: int | None,
    include_nsfw: bool,
) -> RedditSearch:
    """Create a new Reddit history search"""
    search = RedditSearch(
        username=username,
        subreddit_filter=subreddit_filter,
        date_from=date_from,
        date_to=date_to,
        include_nsfw=include_nsfw,
    )
    db.add(search)
    await db.flush()
    await db.refresh(search)
    return search


async def get_search(db: AsyncSession, search_id: int) -> RedditSearch | None:
    """Get a search by ID, without its results"""
    result = await db.execute(select(RedditSearch).where(RedditSearch.id == search_id))
    return result.scalar_one_or_none()


async def get_search_with_results(db: AsyncSession, search_id: int) -> RedditSearch | None:
    """Get a search by ID, including all pages of results persisted so far"""
    result = await db.execute(
        select(RedditSearch)
        .where(RedditSearch.id == search_id)
        .options(selectinload(RedditSearch.results))
    )
    return result.scalar_one_or_none()


async def list_searches(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[tuple[RedditSearch, int]]:
    """List past searches with their result count, most recent first"""
    result = await db.execute(
        select(RedditSearch, func.count(RedditSearchResult.id))
        .outerjoin(RedditSearchResult, RedditSearchResult.search_id == RedditSearch.id)
        .group_by(RedditSearch.id)
        .order_by(RedditSearch.searched_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return [(row[0], row[1]) for row in result.all()]


async def add_results(db: AsyncSession, search_id: int, kind: str, rows: list[dict]) -> list[RedditSearchResult]:
    """Persist a page of results, skipping any (kind, reddit_id) pair already
    stored for this search - keeps re-fetching a page (e.g. paging back) idempotent."""
    if not rows:
        return []

    existing_ids = set(
        (
            await db.execute(
                select(RedditSearchResult.reddit_id).where(
                    RedditSearchResult.search_id == search_id,
                    RedditSearchResult.kind == kind,
                )
            )
        ).scalars().all()
    )

    new_results = []
    for row in rows:
        if row["reddit_id"] in existing_ids:
            continue
        result = RedditSearchResult(search_id=search_id, **row)
        db.add(result)
        new_results.append(result)
        existing_ids.add(row["reddit_id"])

    await db.flush()
    return new_results


async def delete_search(db: AsyncSession, search_id: int) -> RedditSearch | None:
    """Delete a search and its results"""
    search = await get_search(db, search_id)
    if not search:
        return None

    await db.delete(search)
    await db.flush()
    return search
