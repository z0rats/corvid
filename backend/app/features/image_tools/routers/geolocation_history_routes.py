import logging
from typing import Literal

from fastapi import APIRouter, Response, status

from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException

from ..crud.geolocation_history_crud import delete_search, get_search, list_searches
from ..schemas.geolocation_history_schemas import GeolocationSearchDetail, GeolocationSearchSummary
from ..service.geolocation_report_service import generate_geolocation_report

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/image/geolocate/history", tags=["Image Tools"])


@router.get(
    "",
    response_model=list[GeolocationSearchSummary],
    summary="List past AI geolocation analyses",
    description="List past AI photo-geolocation analyses, most recent first",
)
async def read_searches(
    db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100
) -> list[GeolocationSearchSummary]:
    return await list_searches(db, skip, limit)


@router.get(
    "/{search_id}",
    response_model=GeolocationSearchDetail,
    summary="Get an AI geolocation analysis",
    description="Get a past AI photo-geolocation analysis, including its full clue list",
    responses={404: {"description": "Analysis not found"}},
)
async def read_search(search_id: int, db: ReadSessionDep) -> GeolocationSearchDetail:
    search = await get_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
            error_code="GEOLOCATION_HISTORY_NOT_FOUND",
        )
    return search


@router.get(
    "/{search_id}/report",
    summary="Export an AI geolocation analysis as a report",
    description="Download a past AI photo-geolocation analysis as an HTML or PDF report",
    responses={404: {"description": "Analysis not found"}},
)
async def export_search_report(
    search_id: int,
    db: ReadSessionDep,
    format: Literal["html", "pdf"] = "html",
) -> Response:
    search = await get_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
            error_code="GEOLOCATION_HISTORY_NOT_FOUND",
        )

    content, media_type, filename = generate_geolocation_report(search, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete an AI geolocation analysis",
    description="Delete a past AI photo-geolocation analysis from history",
    responses={404: {"description": "Analysis not found"}},
)
async def delete_search_endpoint(search_id: int, db: SessionDep) -> None:
    search = await delete_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
            error_code="GEOLOCATION_HISTORY_NOT_FOUND",
        )
    logger.info("Deleted image geolocation search %s", search_id)
