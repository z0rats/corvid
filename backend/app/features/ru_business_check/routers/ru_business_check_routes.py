import asyncio
import logging
from typing import Literal

from fastapi import APIRouter, Request, Response, status

from app.core.config.rate_limit_config import limiter
from app.core.dependencies import ReadSessionDep, SessionDep
from app.core.exceptions import AppHTTPException
from app.core.scans.routes import add_run_routes
from app.core.scans.sse import sse_response
from app.features.ru_business_check.crud.ru_business_check_crud import RU_BUSINESS_CHECK_SCANS
from app.features.ru_business_check.schemas.ru_business_check_schemas import (
    ScanRequest,
    SearchDetail,
    SearchSummary,
)
from app.features.ru_business_check.service.report_service import (
    generate_ru_business_check_report,
)
from app.features.ru_business_check.service.ru_business_check_service import (
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
    search = await RU_BUSINESS_CHECK_SCANS.history.get(db, search_id)
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


add_run_routes(
    router,
    RU_BUSINESS_CHECK_SCANS,
    display_name="RU Business Check",
    summary_schema=SearchSummary,
    detail_schema=SearchDetail,
    not_found_code="RU_BUSINESS_CHECK_NOT_FOUND",
)
