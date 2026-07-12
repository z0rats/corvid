import logging

from fastapi import APIRouter, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.features.reddit_search.crud.reddit_search_crud import (
    add_results,
    create_search,
    delete_search,
    get_search,
    get_search_with_results,
    list_searches,
)
from app.features.reddit_search.schemas.reddit_search_schemas import (
    RedditCursor,
    ScanRequest,
    ScanResponse,
    SearchDetail,
    SearchSummary,
)
from app.features.reddit_search.service.reddit_search_service import LIMIT, fetch_both, to_result_row

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reddit-search", tags=["Reddit Search"])


@router.post(
    "/scan",
    response_model=ScanResponse,
    summary="Fetch a page of a user's Reddit history",
    description="Query Arctic Shift and PullPush in parallel for one page of a user's post or "
    "comment history, merge and persist the results, and return a cursor for the next page",
    responses={404: {"description": "search_id given but no such search exists"}},
)
@limiter.limit("10/minute")
async def scan(request: Request, db: SessionDep, scan_request: ScanRequest) -> ScanResponse:
    if scan_request.search_id is not None:
        search = await get_search(db, scan_request.search_id)
        if not search:
            raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found", error_code="REDDIT_SEARCH_NOT_FOUND")
    else:
        search = await create_search(
            db,
            scan_request.username,
            subreddit_filter=scan_request.filters.subreddit,
            date_from=scan_request.filters.date_from,
            date_to=scan_request.filters.date_to,
            include_nsfw=scan_request.filters.include_nsfw,
        )

    items, sources, _arctic_down = await fetch_both(
        scan_request.username,
        scan_request.kind,
        subreddit=scan_request.filters.subreddit,
        date_from=scan_request.filters.date_from,
        date_to=scan_request.filters.date_to,
        include_nsfw=scan_request.filters.include_nsfw,
        cursor_before=scan_request.cursor.before if scan_request.cursor else None,
        cursor_after=scan_request.cursor.after if scan_request.cursor else None,
    )

    singular_kind = "post" if scan_request.kind == "posts" else "comment"
    rows = [to_result_row(item, scan_request.kind) for item in items]
    await add_results(db, search.id, singular_kind, rows)

    has_more = len(items) >= LIMIT
    next_cursor = RedditCursor(before=rows[-1]["created_utc"]) if has_more and rows else None

    logger.info("Reddit search %s: fetched %d %s for '%s' from %s", search.id, len(items), scan_request.kind, scan_request.username, sources)

    return ScanResponse(
        search_id=search.id,
        items=rows,
        sources=sources,
        has_more=has_more,
        next_cursor=next_cursor,
    )


@router.get(
    "/history",
    response_model=list[SearchSummary],
    summary="List past Reddit searches",
    description="List past Reddit history searches, most recent first",
)
async def read_searches(db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100) -> list[SearchSummary]:
    rows = await list_searches(db, skip=skip, limit=limit)
    summaries = []
    for search, count in rows:
        summary = SearchSummary.model_validate(search)
        summary.result_count = count
        summaries.append(summary)
    return summaries


@router.get(
    "/history/{search_id}",
    response_model=SearchDetail,
    summary="Get a past Reddit search",
    description="Get a past Reddit search, including every page of results fetched so far",
    responses={404: {"description": "Search not found"}},
)
async def read_search(search_id: int, db: ReadSessionDep) -> SearchDetail:
    search = await get_search_with_results(db, search_id)
    if not search:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found", error_code="REDDIT_SEARCH_NOT_FOUND")
    detail = SearchDetail.model_validate(search)
    detail.result_count = len(detail.results)
    return detail


@router.delete(
    "/history/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a Reddit search",
    description="Permanently delete a past Reddit search and its results",
    responses={404: {"description": "Search not found"}},
)
async def delete_search_endpoint(search_id: int, db: SessionDep) -> None:
    search = await delete_search(db, search_id)
    if not search:
        raise AppHTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Search not found", error_code="REDDIT_SEARCH_NOT_FOUND")
    logger.info("Deleted reddit search %s", search_id)
