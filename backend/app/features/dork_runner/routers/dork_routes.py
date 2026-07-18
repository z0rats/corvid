import logging

from fastapi import APIRouter, Query, Request, status

from app.core.config.rate_limit_config import limiter
from app.features.dork_runner.config.dork_templates import get_templates_for_target_type
from app.features.dork_runner.schemas.dork_schemas import DorkRunRequest, DorkRunResponse, DorkTemplateInfo, TargetType
from app.features.dork_runner.service.dork_query_service import perform_dork_run

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/dork-runner", tags=["Dork Runner"])


@router.post(
    "/run",
    response_model=DorkRunResponse,
    status_code=status.HTTP_200_OK,
    summary="Run dork templates against a target",
    description="Runs a set of parameterized Google/Bing/DuckDuckGo dork templates against a domain, "
                 "username, or email, aggregating results into one response",
)
@limiter.limit("5/minute")
async def run_dork_scan(request: Request, dork_request: DorkRunRequest) -> DorkRunResponse:
    logger.info(
        "Dork run requested - target: %s, type: %s, engine: %s",
        dork_request.target, dork_request.target_type, dork_request.engine,
    )
    result = await perform_dork_run(dork_request)
    logger.info(
        "Dork run completed - target: %s, queries: %s, results: %s",
        dork_request.target, result.queries_run, result.total_results,
    )
    return result


@router.get(
    "/templates",
    response_model=list[DorkTemplateInfo],
    status_code=status.HTTP_200_OK,
    summary="List dork templates applicable to a target type",
)
async def list_dork_templates(target_type: TargetType = Query(...)) -> list[DorkTemplateInfo]:
    templates = get_templates_for_target_type(target_type)
    return [
        DorkTemplateInfo(
            key=t.key,
            pattern=t.pattern,
            description=t.description,
            target_types=list(t.target_types),
        )
        for t in templates
    ]
