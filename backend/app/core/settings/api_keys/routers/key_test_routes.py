from typing import Annotated

from fastapi import APIRouter, Path, Request, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep
from app.core.settings.api_keys.schemas.key_test_schemas import KeyTestResult
from app.core.settings.api_keys.service.key_test_service import (
    run_all_key_tests,
    run_key_test,
)

router = APIRouter(prefix="/api/services", tags=["Service Configuration"])

ServiceKey = Annotated[str, Path(min_length=1, max_length=100, description="Service key")]


@router.post(
    "/test",
    response_model=list[KeyTestResult],
    status_code=status.HTTP_200_OK,
    summary="Test every configured API key",
    description="Live check of each testable service whose keys are all saved, with the "
    "remaining quota where the provider reports it. Services that can't be tested without "
    "spending quota are skipped.",
)
@limiter.limit("10/minute")
async def test_all_keys_endpoint(request: Request, db: ReadSessionDep) -> list[KeyTestResult]:
    return await run_all_key_tests(db)


@router.post(
    "/{service_key}/test",
    response_model=KeyTestResult,
    status_code=status.HTTP_200_OK,
    summary="Test one service's API key",
    description="Live check of the saved key(s) of one service. A provider failure is a "
    "status in the result, not an HTTP error.",
    responses={404: {"description": "No keyed service with that name"}},
)
@limiter.limit("10/minute")
async def test_key_endpoint(
    request: Request, service_key: ServiceKey, db: ReadSessionDep
) -> KeyTestResult:
    return await run_key_test(db, service_key)
