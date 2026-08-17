import asyncio
import datetime
import logging
import re

from app.core.database import managed_session
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanOutcome, ScanRun
from app.core.scans.sse import queue_sink
from app.core.settings.ru_business_check.crud.ru_business_check_settings_crud import (
    get_ru_business_check_settings,
)
from app.features.ru_business_check.config.ru_business_check_config import (
    AVAILABLE_SOURCES,
    FEATURE_NAME,
    PLANNED_SOURCES,
    WALL_CLOCK_TIMEOUT_SECONDS,
)
from app.features.ru_business_check.crud.ru_business_check_crud import (
    SCAN_COLUMNS,
    find_recent_completed_search_by_query,
)
from app.features.ru_business_check.models.ru_business_check_models import RuBusinessCheckSearch
from app.features.ru_business_check.service import flag_engine
from app.features.ru_business_check.service.arbitration_service import (
    ArbitrationError,
    fetch_arbitration_cases,
)
from app.features.ru_business_check.service.disqualified_persons_service import (
    DisqualifiedPersonsError,
    check_disqualified,
)
from app.features.ru_business_check.service.egrul_service import (
    EgrulAmbiguousMatch,
    EgrulError,
    fetch_egrul_extract,
)
from app.features.ru_business_check.service.fedresurs_service import (
    FedresursError,
    fetch_fedresurs_status,
)
from app.features.ru_business_check.service.fedsfm_service import (
    FedsfmError,
    check_terrorist_list,
)
from app.features.ru_business_check.service.pb_nalog_service import (
    PbNalogError,
    fetch_pb_nalog_profile,
)
from app.features.ru_business_check.service.zakupki_rnp_service import (
    ZakupkiRnpError,
    fetch_rnp_entries,
)

logger = logging.getLogger(__name__)

_INN_RE = re.compile(r"^\d{10}(\d{2})?$")

# History cache TTL is settings-backed (history_retention_days is about deletion; this
# is a separate, shorter "don't re-hit the source" window) - kept as a plain constant for
# Stage 1 rather than another settings field, since it's an implementation detail of the
# cache, not something the guide's methodology calls out as tunable.
CACHE_TTL_HOURS = 24


async def cancel_scan(search_id: int) -> bool:
    return await ScanRun.cancel(FEATURE_NAME, search_id)


def _entity_type_from_ogrn(ogrn: str | None) -> str | None:
    if not ogrn:
        return None
    return "individual_entrepreneur" if len(ogrn) == 15 else "legal_entity"


async def run_scan_task(
    *, query: str, force_refresh: bool, website: str | None = None, queue: asyncio.Queue
) -> None:
    """Run one scan (ЕГРЮЛ -> РДЛ -> арбитраж -> Федресурс -> Прозрачный бизнес -> ФедСФМ
    -> РНП -> flag engine), persisting its result and streaming coarse-grained progress via
    the given queue. `website`, if supplied, is stored as-is and displayed with a link out
    to `domain_finder`'s own WHOIS/DNS/CT analysis - never fetched or analyzed by this
    feature itself. An ambiguous ЕГРЮЛ match (a
    name search returning multiple rows) is a normal completed outcome with `candidates`
    populated, not a failure - see `EgrulAmbiguousMatch` handling below.

    Spawned as a background task by the route handler, same shape as git_recon/
    email_search/username_search - the request returns an SSE stream immediately rather
    than blocking for the scan's full duration.
    """
    on_event = queue_sink(queue)
    normalized_query = query.strip()
    normalized_website = website.strip() if website and website.strip() else None
    cancellable = TaskCancellable(asyncio.current_task())

    async def run_work(search_id: int) -> ScanOutcome:
        async with managed_session() as db:
            settings_row = await get_ru_business_check_settings(db)
            fresh_registration_threshold_days = settings_row.fresh_registration_threshold_days
            small_claim_amount_threshold = settings_row.small_claim_amount_threshold
            large_claim_amount_threshold = settings_row.large_claim_amount_threshold
            multiple_claims_defendant_threshold = settings_row.multiple_claims_defendant_threshold
            mass_address_threshold = settings_row.mass_address_threshold

        if not force_refresh:
            async with managed_session() as db:
                cached = await find_recent_completed_search_by_query(
                    db,
                    normalized_query,
                    max_age=datetime.timedelta(hours=CACHE_TTL_HOURS),
                )
            if cached is not None:
                logger.info(
                    "ru_business_check: serving cached result for query %r", normalized_query
                )
                return ScanOutcome(
                    fields={
                        "resolved_inn": cached.resolved_inn,
                        "entity_type": cached.entity_type,
                        "risk_level": cached.risk_level,
                        "egrul_data": cached.egrul_data,
                        "egrul_raw": cached.egrul_raw,
                        "disqualification_result": cached.disqualification_result,
                        "disqualification_raw": cached.disqualification_raw,
                        "arbitration_data": cached.arbitration_data,
                        "arbitration_raw": cached.arbitration_raw,
                        "fedresurs_data": cached.fedresurs_data,
                        "fedresurs_raw": cached.fedresurs_raw,
                        "pb_nalog_data": cached.pb_nalog_data,
                        "pb_nalog_raw": cached.pb_nalog_raw,
                        "fedsfm_result": cached.fedsfm_result,
                        "fedsfm_raw": cached.fedsfm_raw,
                        "website": cached.website,
                        "rnp_data": cached.rnp_data,
                        "rnp_raw": cached.rnp_raw,
                        "flags": cached.flags,
                        "checked_sources": cached.checked_sources,
                        "pending_sources": cached.pending_sources,
                        "candidates": cached.candidates,
                    }
                )

        try:
            egrul_data, egrul_raw = await fetch_egrul_extract(normalized_query)
        except EgrulAmbiguousMatch as exc:
            logger.info(
                "ru_business_check: %d ambiguous ЕГРЮЛ match(es) for %r",
                len(exc.candidates),
                normalized_query,
            )
            return ScanOutcome(
                fields={
                    "resolved_inn": None,
                    "entity_type": None,
                    "risk_level": None,
                    "egrul_data": None,
                    "egrul_raw": str(exc),
                    "disqualification_result": {
                        "checked": False,
                        "matched": False,
                        "requires_manual_review": False,
                        "matches": [],
                    },
                    "disqualification_raw": "",
                    "arbitration_data": {"checked": False, "cases": []},
                    "arbitration_raw": "",
                    "fedresurs_data": {
                        "checked": False,
                        "found": False,
                        "status_text": None,
                        "is_active_bankruptcy": False,
                        "profile_url": None,
                    },
                    "fedresurs_raw": "",
                    "pb_nalog_data": {
                        "checked": False,
                        "found": False,
                        "mass_address_count": 0,
                        "mass_address_companies": [],
                        "profile_url": None,
                    },
                    "pb_nalog_raw": "",
                    "fedsfm_result": {
                        "checked": False,
                        "matched": False,
                        "requires_manual_review": False,
                        "matches": [],
                    },
                    "fedsfm_raw": "",
                    "website": normalized_website,
                    "rnp_data": {"checked": False, "entries": []},
                    "rnp_raw": "",
                    "flags": [],
                    "checked_sources": [],
                    "pending_sources": list(AVAILABLE_SOURCES) + list(PLANNED_SOURCES),
                    "candidates": exc.candidates,
                }
            )

        # A single source failing (rate-limited, blocked, timed out) must not discard
        # the sources that already succeeded - each is wrapped in its own try/except and
        # `checked_sources` is built from what actually completed, not assumed
        # unconditionally from AVAILABLE_SOURCES like an earlier version of this did.
        succeeded_sources = ["egrul"]

        disqualification_result: dict = {
            "checked": False,
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }
        disqualification_raw = ""
        director_name = egrul_data.get("director_name")
        if director_name:
            try:
                disqualification_result, disqualification_raw = await check_disqualified(
                    director_name
                )
                succeeded_sources.append("disqualified_persons")
            except DisqualifiedPersonsError as exc:
                logger.warning("ru_business_check: РДЛ check failed for %r: %s", director_name, exc)

        resolved_inn = egrul_data.get("inn")
        entity_type = _entity_type_from_ogrn(egrul_data.get("ogrn"))

        arbitration_cases: list[dict] = []
        arbitration_raw = ""
        if resolved_inn:
            try:
                arbitration_cases, arbitration_raw = await fetch_arbitration_cases(resolved_inn)
                succeeded_sources.append("arbitration")
            except ArbitrationError as exc:
                logger.warning(
                    "ru_business_check: arbitration lookup failed for %r: %s", resolved_inn, exc
                )
        arbitration_data = {
            "checked": "arbitration" in succeeded_sources,
            "cases": arbitration_cases,
        }

        fedresurs_result: dict = {
            "checked": False,
            "found": False,
            "status_text": None,
            "is_active_bankruptcy": False,
            "profile_url": None,
        }
        fedresurs_raw = ""
        if resolved_inn:
            try:
                fedresurs_result, fedresurs_raw = await fetch_fedresurs_status(
                    resolved_inn, is_individual=(entity_type == "individual_entrepreneur")
                )
                succeeded_sources.append("fedresurs")
            except FedresursError as exc:
                logger.warning(
                    "ru_business_check: Федресурс lookup failed for %r: %s", resolved_inn, exc
                )

        pb_nalog_result: dict = {
            "checked": False,
            "found": False,
            "mass_address_count": 0,
            "mass_address_companies": [],
            "profile_url": None,
        }
        pb_nalog_raw = ""
        if resolved_inn:
            try:
                pb_nalog_result, pb_nalog_raw = await fetch_pb_nalog_profile(
                    resolved_inn, is_individual=(entity_type == "individual_entrepreneur")
                )
                succeeded_sources.append("pb_nalog")
            except PbNalogError as exc:
                logger.warning(
                    "ru_business_check: Прозрачный бизнес lookup failed for %r: %s",
                    resolved_inn,
                    exc,
                )

        fedsfm_result: dict = {
            "checked": False,
            "matched": False,
            "requires_manual_review": False,
            "matches": [],
        }
        fedsfm_raw = ""
        if director_name:
            try:
                fedsfm_result, fedsfm_raw = await check_terrorist_list(director_name)
                succeeded_sources.append("fedsfm")
            except FedsfmError as exc:
                logger.warning(
                    "ru_business_check: ФедСФМ check failed for %r: %s", director_name, exc
                )

        rnp_entries: list[dict] = []
        rnp_raw = ""
        if resolved_inn:
            try:
                rnp_entries, rnp_raw = await fetch_rnp_entries(resolved_inn)
                succeeded_sources.append("zakupki_rnp")
            except ZakupkiRnpError as exc:
                logger.warning("ru_business_check: РНП lookup failed for %r: %s", resolved_inn, exc)
        rnp_data = {
            "checked": "zakupki_rnp" in succeeded_sources,
            "entries": rnp_entries,
        }

        flags, risk_level = flag_engine.evaluate(
            egrul_data,
            disqualification_result,
            arbitration_cases,
            fedresurs_result,
            pb_nalog_result,
            fedsfm_result,
            rnp_entries,
            fresh_registration_threshold_days=fresh_registration_threshold_days,
            small_claim_amount_threshold=small_claim_amount_threshold,
            large_claim_amount_threshold=large_claim_amount_threshold,
            multiple_claims_defendant_threshold=multiple_claims_defendant_threshold,
            mass_address_threshold=mass_address_threshold,
        )

        logger.info(
            "ru_business_check scan for %r: risk=%s, %d flag(s)",
            normalized_query,
            risk_level,
            len(flags),
        )

        return ScanOutcome(
            fields={
                "resolved_inn": resolved_inn,
                "entity_type": entity_type,
                "risk_level": risk_level,
                "egrul_data": egrul_data,
                "egrul_raw": egrul_raw,
                "disqualification_result": disqualification_result,
                "disqualification_raw": disqualification_raw,
                "arbitration_data": arbitration_data,
                "arbitration_raw": arbitration_raw,
                "fedresurs_data": fedresurs_result,
                "fedresurs_raw": fedresurs_raw,
                "pb_nalog_data": pb_nalog_result,
                "pb_nalog_raw": pb_nalog_raw,
                "fedsfm_result": fedsfm_result,
                "fedsfm_raw": fedsfm_raw,
                "website": normalized_website,
                "rnp_data": rnp_data,
                "rnp_raw": rnp_raw,
                "flags": flags,
                "checked_sources": succeeded_sources,
                "pending_sources": [s for s in AVAILABLE_SOURCES if s not in succeeded_sources]
                + list(PLANNED_SOURCES),
                "candidates": [],
            }
        )

    async def run_work_with_timeout(search_id: int) -> ScanOutcome:
        try:
            return await asyncio.wait_for(run_work(search_id), timeout=WALL_CLOCK_TIMEOUT_SECONDS)
        except TimeoutError:
            raise TimeoutError("Проверка заняла слишком много времени и была прервана") from None

    await ScanRun.execute(
        FEATURE_NAME,
        RuBusinessCheckSearch,
        run_work_with_timeout,
        on_event,
        columns=SCAN_COLUMNS,
        create_fields={"query": normalized_query},
        started_fields={"query": normalized_query},
        cancellable=cancellable,
        expected_exceptions=(
            EgrulError,
            DisqualifiedPersonsError,
            ArbitrationError,
            FedresursError,
            PbNalogError,
            FedsfmError,
            ZakupkiRnpError,
            ValueError,
            TimeoutError,
        ),
    )
