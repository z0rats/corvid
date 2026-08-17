import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, Request, Response, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import LimitQuery, ReadSessionDep, SessionDep, SkipQuery
from app.core.exceptions import AppHTTPException
from app.core.scans.sse import sse_response
from app.features.ru_business_check.crud.ru_business_check_crud import (
    delete_search,
    get_search,
    list_searches,
)
from app.features.ru_business_check.schemas.ru_business_check_schemas import (
    ScanRequest,
    SearchDetail,
    SearchSummary,
)
from app.features.ru_business_check.service.report_service import (
    generate_ru_business_check_report,
)
from app.features.ru_business_check.service.ru_business_check_service import (
    cancel_scan,
    run_scan_task,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ru-business-check", tags=["RU Business Check"])


@router.post(
    "/scan",
    summary=(
        "Проверить юрлицо/ИП по ИНН или названию (ЕГРЮЛ + РДЛ + арбитраж + "
        "Федресурс + Прозрачный бизнес)"
    ),
    description="Запускает проверку контрагента: выписка ЕГРЮЛ/ЕГРИП + сверка директора "
    "с реестром дисквалифицированных лиц и перечнем терроризм/ОМУ (ФедСФМ) + арбитражные "
    "дела + проверка на активное банкротство (Федресурс) + признаки массовой регистрации "
    "(Прозрачный бизнес) + реестр недобросовестных поставщиков (РНП) + движок "
    "жёстких/мягких флагов. `website`, если указан, сохраняется как есть (в этой проверке "
    "не анализируется — см. ссылку в IOC-инструменты в результате). ФССП автоматически не "
    "проверяется (капча на каждом запросе) — см. pending_sources в результате. "
    "Прогресс передаётся через Server-Sent Events.",
)
@limiter.limit("5/minute")
async def scan(request: Request, db: SessionDep, scan_request: ScanRequest):
    queue: asyncio.Queue = asyncio.Queue()
    asyncio.create_task(
        run_scan_task(
            query=scan_request.query,
            force_refresh=scan_request.force_refresh,
            website=scan_request.website,
            queue=queue,
        )
    )
    return sse_response(queue)


@router.post(
    "/history/{search_id}/cancel",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Отменить выполняющуюся проверку",
    responses={404: {"description": "No running search with that ID"}},
)
async def cancel_scan_endpoint(search_id: int) -> None:
    if not await cancel_scan(search_id):
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No running search with that ID",
            error_code="RU_BUSINESS_CHECK_NOT_FOUND",
        )
    logger.info("Cancellation requested for ru_business_check search %s", search_id)


@router.get(
    "/history",
    response_model=list[SearchSummary],
    summary="Список прошлых проверок",
)
async def read_searches(
    db: ReadSessionDep, skip: SkipQuery = 0, limit: LimitQuery = 100
) -> list[SearchSummary]:
    searches = await list_searches(db, skip=skip, limit=limit)
    return [SearchSummary.model_validate(s) for s in searches]


@router.get(
    "/history/{search_id}",
    response_model=SearchDetail,
    summary="Получить прошлую проверку целиком",
    responses={404: {"description": "Search not found"}},
)
async def read_search(search_id: int, db: ReadSessionDep) -> SearchDetail:
    search = await get_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found",
            error_code="RU_BUSINESS_CHECK_NOT_FOUND",
        )
    return SearchDetail.model_validate(search)


@router.get(
    "/history/{search_id}/report",
    summary="Экспортировать проверку в виде отчёта",
    description="Скачать прошлую проверку целиком в виде HTML- или PDF-отчёта — каждый "
    "пункт со ссылкой на источник (на конкретный запрос/запись, где это возможно, "
    "а не просто на сайт источника).",
    responses={404: {"description": "Search not found"}},
)
async def export_search_report(
    search_id: int, db: ReadSessionDep, format: Literal["html", "pdf"] = "html"
) -> Response:
    search = await get_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found",
            error_code="RU_BUSINESS_CHECK_NOT_FOUND",
        )

    content, media_type, filename = generate_ru_business_check_report(search, format)
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.delete(
    "/history/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить прошлую проверку",
    responses={404: {"description": "Search not found"}},
)
async def delete_search_endpoint(search_id: int, db: SessionDep) -> None:
    search = await delete_search(db, search_id)
    if not search:
        raise AppHTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Search not found",
            error_code="RU_BUSINESS_CHECK_NOT_FOUND",
        )
    logger.info("Deleted ru_business_check search %s", search_id)
