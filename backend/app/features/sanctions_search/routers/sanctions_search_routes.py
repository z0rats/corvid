import logging

from fastapi import APIRouter, Query, status

from app.core.dependencies import ReadSessionDep
from app.core.exceptions import AppHTTPException
from app.features.sanctions_search.schemas.sanctions_search_schemas import SanctionsSearchResponse
from app.features.sanctions_search.service import sanctions_search_service
from app.features.sanctions_search.service.sanctions_search_service import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    MIN_QUERY_LENGTH,
    SanctionsSearchError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/sanctions-search", tags=["Sanctions Search"])


@router.get(
    "/search",
    response_model=SanctionsSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search the OFAC SDN list by name/alias",
    description="Free-text search by person/organization/vessel/aircraft name or alias against "
    "a locally cached mirror of the OFAC SDN sanctions list",
)
async def search_sanctions(
    db: ReadSessionDep,
    q: str = Query(..., min_length=MIN_QUERY_LENGTH, max_length=200),
    schema: str | None = Query(default=None, max_length=30),
    limit: int = Query(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
) -> SanctionsSearchResponse:
    try:
        result = await sanctions_search_service.search(db, query=q, schema=schema, limit=limit)
    except SanctionsSearchError as exc:
        raise AppHTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
            error_code="sanctions_list_not_loaded",
        ) from exc
    return SanctionsSearchResponse(**result)


@router.get(
    "/schemas",
    response_model=list[str],
    status_code=status.HTTP_200_OK,
    summary="List entity schemas present in the loaded list",
    description="Distinct OpenSanctions entity schemas (Person, Organization, Vessel, ...) "
    "currently in the local mirror, for the search filter dropdown",
)
async def list_sanctions_schemas() -> list[str]:
    return await sanctions_search_service.list_schemas()
