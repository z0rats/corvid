import logging
from collections.abc import Callable
from typing import Any

from fastapi import APIRouter, status
from pydantic import BaseModel

from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.scans.feature import ScanFeature

logger = logging.getLogger(__name__)


def add_run_routes(
    router: APIRouter,
    feature: ScanFeature,
    *,
    display_name: str,
    summary_schema: type[BaseModel],
    detail_schema: type[BaseModel],
    not_found_code: str,
    not_running_code: str | None = None,
    base: str = "history",
    noun: str = "search",
    not_found_detail: str | None = None,
    with_results: bool = False,
    to_detail: Callable[[Any], BaseModel] | None = None,
    after_delete: Callable[[int], None] | None = None,
) -> None:
    """Mount a scan feature's run-history routes on `router`, identical in shape across
    every scan feature:

    - `POST /{base}/{id}/cancel` - 202, or 404 `not_running_code` if nothing is running
    - `GET /{base}` - `list[summary_schema]`, newest first, `skip`/`limit` paged
    - `GET /{base}/{id}` - `detail_schema` (eager-loading the result rows if
      `with_results`; `to_detail` replaces plain `model_validate`), or 404
    - `DELETE /{base}/{id}` - 204 (then `after_delete(id)`), or 404

    The scan-start (`POST /scan`) route stays in the feature: its request shape and
    rate limit are the feature's own.
    """
    plural = "searches" if noun == "search" else f"{noun}s"
    not_found_detail = not_found_detail or f"{noun.capitalize()} not found"
    not_running_code = not_running_code or not_found_code
    load = feature.history.get_with_results if with_results else feature.history.get
    build_detail = to_detail or detail_schema.model_validate

    def _not_found(detail: str, error_code: str) -> AppHTTPException:
        return AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=detail, error_code=error_code
        )

    @router.post(
        f"/{base}/{{search_id}}/cancel",
        status_code=status.HTTP_202_ACCEPTED,
        summary=f"Cancel a running {display_name} {noun}",
        description=f"Cancel a currently-running {display_name} {noun}, keeping whatever it "
        "found before cancellation",
        responses={404: {"description": f"No running {noun} with that ID"}},
    )
    async def cancel_run(search_id: int) -> None:
        if not await feature.cancel(search_id):
            raise _not_found(f"No running {noun} with that ID", not_running_code)
        logger.info("Cancellation requested for %s %s %s", display_name, noun, search_id)

    @router.get(
        f"/{base}",
        response_model=list[summary_schema],  # type: ignore[valid-type]
        summary=f"List past {display_name} {plural}",
        description=f"List past and in-progress {display_name} {plural}, most recent first",
    )
    async def list_runs(
        db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100
    ) -> list[Any]:
        runs = await feature.history.list(db, skip=skip, limit=limit)
        return [summary_schema.model_validate(run) for run in runs]

    @router.get(
        f"/{base}/{{search_id}}",
        response_model=detail_schema,
        summary=f"Get a past {display_name} {noun}",
        description=f"Get a past {display_name} {noun}, including its full result",
        responses={404: {"description": not_found_detail}},
    )
    async def read_run(search_id: int, db: ReadSessionDep) -> Any:
        run = await load(db, search_id)
        if not run:
            raise _not_found(not_found_detail, not_found_code)
        return build_detail(run)

    @router.delete(
        f"/{base}/{{search_id}}",
        status_code=status.HTTP_204_NO_CONTENT,
        summary=f"Delete a {display_name} {noun}",
        description=f"Permanently delete a past {display_name} {noun} and its results",
        responses={404: {"description": not_found_detail}},
    )
    async def delete_run(search_id: int, db: SessionDep) -> None:
        run = await feature.history.delete(db, search_id)
        if not run:
            raise _not_found(not_found_detail, not_found_code)
        if after_delete is not None:
            after_delete(search_id)
        logger.info("Deleted %s %s %s", display_name, noun, search_id)
