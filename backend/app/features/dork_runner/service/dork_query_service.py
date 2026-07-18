import asyncio
import logging

from app.core.exceptions import AppHTTPException
from app.features.dork_runner.config.dork_templates import DorkTemplate, get_templates_for_target_type
from app.features.dork_runner.config.search_engines_config import MAX_QUERIES_PER_RUN, REQUEST_DELAY_SECONDS
from app.features.dork_runner.schemas.dork_schemas import DorkResult, DorkRunRequest, DorkRunResponse
from app.features.dork_runner.service.engines import bing_engine, duckduckgo_engine, google_engine

logger = logging.getLogger(__name__)

_ENGINES = {
    "duckduckgo": duckduckgo_engine,
    "google": google_engine,
    "bing": bing_engine,
}


def _resolve_templates(request: DorkRunRequest) -> list[DorkTemplate]:
    applicable = get_templates_for_target_type(request.target_type)

    if request.template_keys:
        requested = set(request.template_keys)
        templates = [t for t in applicable if t.key in requested]
        unknown = requested - {t.key for t in applicable}
        if unknown:
            raise AppHTTPException(
                status_code=400,
                detail=f"Unknown or inapplicable template key(s) for target type '{request.target_type}': {sorted(unknown)}",
                error_code="DORK_INVALID_TEMPLATE",
            )
    else:
        templates = applicable

    return templates[:MAX_QUERIES_PER_RUN]


async def perform_dork_run(request: DorkRunRequest) -> DorkRunResponse:
    """Run the resolved templates sequentially against the chosen engine.

    Queries run one at a time (not fanned out in parallel) with a politeness
    delay between them, to keep the request pattern from looking like abuse to
    the target search engine and reduce block/CAPTCHA risk.
    """
    engine_module = _ENGINES[request.engine]
    templates = _resolve_templates(request)

    results: list[DorkResult] = []
    errors: list[str] = []

    try:
        for index, template in enumerate(templates):
            query = template.pattern.format(target=request.target)
            try:
                raw_results = await engine_module.search(query)
                for raw in raw_results:
                    results.append(DorkResult(
                        template_key=template.key,
                        query=query,
                        title=raw.title,
                        url=raw.url,
                        snippet=raw.snippet,
                    ))
                if not raw_results:
                    logger.debug("Dork query '%s' via %s returned no results", query, request.engine)
            except Exception as e:
                logger.warning("Dork query '%s' via %s failed: %s", query, request.engine, e)
                errors.append(f"{template.key}: {e}")

            if index < len(templates) - 1:
                await asyncio.sleep(REQUEST_DELAY_SECONDS)
    except Exception as e:
        logger.error("Unexpected error during dork run for '%s': %s", request.target, e, exc_info=True)
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred during the dork run",
            error_code="DORK_RUN_ERROR",
        )

    return DorkRunResponse(
        target=request.target,
        target_type=request.target_type,
        engine=request.engine,
        results=results,
        total_results=len(results),
        queries_run=len(templates),
        errors=errors,
    )
