import asyncio
import datetime
import json
import logging
from collections.abc import Awaitable, Callable
from typing import Any

import httpx

from app.core.database import managed_session
from app.core.scans.cancellable import TaskCancellable
from app.core.scans.run import ScanOutcome
from app.core.scans.sse import queue_sink
from app.core.settings.ru_business_check.crud.ru_business_check_settings_crud import (
    get_ru_business_check_settings,
)
from app.features.ru_business_check.config.ru_business_check_config import (
    AVAILABLE_SOURCES,
    PLANNED_SOURCES,
    WALL_CLOCK_TIMEOUT_SECONDS,
)
from app.features.ru_business_check.crud.ru_business_check_crud import (
    RU_BUSINESS_CHECK_SCANS,
    find_recent_completed_search_by_query,
)
from app.features.ru_business_check.service import flag_engine
from app.features.ru_business_check.service.arbitration_service import (
    ArbitrationError,
    fetch_arbitration_cases,
)
from app.features.ru_business_check.service.cbr_warning_service import (
    CbrWarningError,
    not_applicable_result,
)
from app.features.ru_business_check.service.cbr_warning_service import (
    lookup_list as lookup_cbr_list,
)
from app.features.ru_business_check.service.disqualified_dump_service import (
    DisqualifiedDumpError,
    lookup_dump,
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
    is_fully_checked,
)
from app.features.ru_business_check.service.fedsfm_service import (
    FedsfmError,
    check_terrorist_list,
)
from app.features.ru_business_check.service.gir_bo_service import (
    GirBoError,
    fetch_gir_bo_financials,
)
from app.features.ru_business_check.service.msp_service import MspError, fetch_msp_status
from app.features.ru_business_check.service.ofac_sdn_service import OfacSdnError
from app.features.ru_business_check.service.ofac_sdn_service import lookup_list as lookup_ofac_list
from app.features.ru_business_check.service.pb_nalog_service import (
    PbNalogError,
    fetch_pb_nalog_profile,
)
from app.features.ru_business_check.service.raw_digest import digest_payloads
from app.features.ru_business_check.service.source_runner import (
    Source,
    SourceContext,
    empty_fields,
    run_source,
    store_results,
)
from app.features.ru_business_check.service.zakupki_rnp_service import (
    ZakupkiRnpError,
    fetch_rnp_entries,
)

logger = logging.getLogger(__name__)

# The "don't re-hit the sources" window for a repeated query - an implementation detail of
# the cache, separate from the settings-backed `history_retention_days` (deletion).
CACHE_TTL_HOURS = 24
INDIVIDUAL = "individual_entrepreneur"

# Every outcome field a cached search row carries over as-is.
_CACHED_FIELDS = (
    "resolved_inn",
    "entity_type",
    "risk_level",
    "egrul_data",
    "egrul_raw",
    "disqualification_result",
    "disqualification_raw",
    "arbitration_data",
    "arbitration_raw",
    "fedresurs_data",
    "fedresurs_raw",
    "pb_nalog_data",
    "pb_nalog_raw",
    "fedsfm_result",
    "fedsfm_raw",
    "website",
    "rnp_data",
    "rnp_raw",
    "extra_data",
    "extra_raw",
    "raw_sha256",
    "flags",
    "checked_sources",
    "pending_sources",
    "candidates",
)


def _checked_list(key: str) -> dict:
    return {"checked": False, key: []}


def _not_checked_match() -> dict:
    return {"checked": False, "matched": False, "requires_manual_review": False, "matches": []}


def _with_list(fetch: Callable[[], Awaitable[tuple[list, str]]], key: str):
    """Arbitration/РНП fetchers return a bare list; stored as `{checked, <key>}`."""

    async def call() -> tuple[dict, str]:
        items, raw = await fetch()
        return {"checked": True, key: items}, raw

    return call()


async def _local(lookup: Callable[[Any], Awaitable[dict]]) -> tuple[dict, None]:
    """A local dump lookup in its own session - it has no remote payload."""
    async with managed_session() as db:
        return await lookup(db), None


def _sources() -> list[Source]:
    """Every source after ЕГРЮЛ, in `AVAILABLE_SOURCES` order. Fetchers are resolved at call
    time through this module's globals so tests can monkeypatch them by name."""
    return [
        Source(
            "disqualified_persons",
            lambda director, ctx: check_disqualified(director),
            DisqualifiedPersonsError,
            needs="director",
            data_column="disqualification_result",
            raw_column="disqualification_raw",
            empty=_not_checked_match,
        ),
        Source(
            "arbitration",
            lambda inn, ctx: _with_list(lambda: fetch_arbitration_cases(inn), "cases"),
            ArbitrationError,
            data_column="arbitration_data",
            raw_column="arbitration_raw",
            empty=lambda: _checked_list("cases"),
        ),
        Source(
            "fedresurs",
            lambda inn, ctx: fetch_fedresurs_status(inn, is_individual=ctx.is_individual),
            FedresursError,
            data_column="fedresurs_data",
            raw_column="fedresurs_raw",
            empty=lambda: {
                "checked": False,
                "found": False,
                "status_text": None,
                "is_active_bankruptcy": False,
                "profile_url": None,
            },
            # Status read, publications not: the bankruptcy-intent/liquidation signals were
            # never looked at, so the source doesn't count as checked (-> `incomplete`).
            is_complete=lambda data, ctx: is_fully_checked(data, is_individual=ctx.is_individual),
        ),
        Source(
            "pb_nalog",
            lambda inn, ctx: fetch_pb_nalog_profile(inn, is_individual=ctx.is_individual),
            PbNalogError,
            data_column="pb_nalog_data",
            raw_column="pb_nalog_raw",
            empty=lambda: {
                "checked": False,
                "found": False,
                "mass_address_count": 0,
                "mass_address_companies": [],
                "profile_url": None,
            },
        ),
        Source(
            "fedsfm",
            lambda director, ctx: check_terrorist_list(director),
            FedsfmError,
            needs="director",
            data_column="fedsfm_result",
            raw_column="fedsfm_raw",
            empty=_not_checked_match,
        ),
        Source(
            "zakupki_rnp",
            lambda inn, ctx: _with_list(lambda: fetch_rnp_entries(inn), "entries"),
            ZakupkiRnpError,
            data_column="rnp_data",
            raw_column="rnp_raw",
            empty=lambda: _checked_list("entries"),
        ),
        # Remote sources kept in `extra_data`/`extra_raw` (docs/adr/0014-*.md).
        Source(
            "gir_bo",
            lambda inn, ctx: fetch_gir_bo_financials(inn, is_individual=ctx.is_individual),
            GirBoError,
        ),
        Source(
            "msp",
            lambda inn, ctx: fetch_msp_status(inn, is_individual=ctx.is_individual),
            MspError,
        ),
        # Local dumps. One that isn't loaded yet raises its error, so the source lands in
        # `pending_sources` rather than reading as "not listed".
        Source(
            "disqualified_dump",
            lambda inn, ctx: _local(lambda db: lookup_dump(db, inn, ctx.director)),
            DisqualifiedDumpError,
        ),
        # SDN entries carry both 10-digit (entity) and 12-digit (individual) ИНН.
        Source(
            "ofac_sdn", lambda inn, ctx: _local(lambda db: lookup_ofac_list(db, inn)), OfacSdnError
        ),
        # The ЦБ list carries only legal entities' ИНН.
        Source(
            "cbr_warning",
            lambda inn, ctx: _local(lambda db: lookup_cbr_list(db, inn)),
            CbrWarningError,
            not_applicable_to_individual=not_applicable_result,
        ),
    ]


def _entity_type_from_ogrn(ogrn: str | None) -> str | None:
    if not ogrn:
        return None
    return INDIVIDUAL if len(ogrn) == 15 else "legal_entity"


async def _load_thresholds() -> flag_engine.Thresholds:
    async with managed_session() as db:
        return flag_engine.Thresholds.from_settings(await get_ru_business_check_settings(db))


async def _cached_outcome(query: str, website: str | None) -> ScanOutcome | None:
    """A completed scan of the same query within `CACHE_TTL_HOURS` (see
    `find_recent_completed_search_by_query` for which rows qualify). `website` isn't a
    scanned source, so the new request's own value wins over the cached row's."""
    async with managed_session() as db:
        cached = await find_recent_completed_search_by_query(
            db, query, max_age=datetime.timedelta(hours=CACHE_TTL_HOURS)
        )
    if cached is None:
        return None
    logger.info("ru_business_check: serving cached result for query %r", query)
    fields = {name: getattr(cached, name) for name in _CACHED_FIELDS}
    if website:
        fields["website"] = website
    return ScanOutcome(fields=fields)


def _ambiguous_outcome(exc: EgrulAmbiguousMatch, website: str | None) -> ScanOutcome:
    """A name query matching several ЕГРЮЛ rows is a normal completed outcome with
    `candidates` populated (the UI offers a disambiguation list), not a failure."""
    return ScanOutcome(
        fields={
            **empty_fields(_sources()),
            "resolved_inn": None,
            "entity_type": None,
            "risk_level": None,
            "egrul_data": None,
            "egrul_raw": str(exc),
            "website": website,
            "flags": [],
            "checked_sources": [],
            "pending_sources": list(AVAILABLE_SOURCES) + list(PLANNED_SOURCES),
            "candidates": exc.candidates,
        }
    )


async def _scan(query: str, website: str | None) -> ScanOutcome:
    """One uncached scan: ЕГРЮЛ -> the live sources -> the extra and local sources -> flag
    engine."""
    thresholds = await _load_thresholds()
    try:
        egrul_data, egrul_raw = await fetch_egrul_extract(query)
    except EgrulAmbiguousMatch as exc:
        logger.info(
            "ru_business_check: %d ambiguous ЕГРЮЛ match(es) for %r", len(exc.candidates), query
        )
        return _ambiguous_outcome(exc, website)
    except (httpx.HTTPError, json.JSONDecodeError) as exc:
        # Without ЕГРЮЛ there is nothing to check - an expected failure, not a bug.
        raise EgrulError(f"ЕГРЮЛ недоступен: {exc}") from exc

    inn = egrul_data.get("inn")
    entity_type = _entity_type_from_ogrn(egrul_data.get("ogrn"))
    ctx = SourceContext(
        inn=inn,
        director=egrul_data.get("director_name"),
        is_individual=entity_type == INDIVIDUAL,
    )
    sources = _sources()
    results = [await run_source(source, ctx) for source in sources]
    succeeded = ["egrul"] + [r.key for r in results if r.checked]
    not_applicable = [r.key for r in results if r.status == "not_applicable"]
    fields = store_results(sources, results)

    flags, risk_level = flag_engine.evaluate(
        flag_engine.SourceResults.from_source_data(egrul_data, {r.key: r.data for r in results}),
        thresholds,
        succeeded,
    )
    logger.info("ru_business_check scan for %r: risk=%s, %d flag(s)", query, risk_level, len(flags))

    fields["raw_sha256"] = digest_payloads({"egrul": egrul_raw, **{r.key: r.raw for r in results}})
    return ScanOutcome(
        fields={
            **fields,
            "resolved_inn": inn,
            "entity_type": entity_type,
            "risk_level": risk_level,
            "egrul_data": egrul_data,
            "egrul_raw": egrul_raw,
            "website": website,
            "flags": flags,
            "checked_sources": succeeded,
            "pending_sources": [
                s for s in AVAILABLE_SOURCES if s not in succeeded and s not in not_applicable
            ]
            + list(PLANNED_SOURCES),
            "candidates": [],
        }
    )


async def run_scan_task(
    *, query: str, force_refresh: bool, website: str | None = None, queue: asyncio.Queue
) -> None:
    """Run one scan (see `_scan`), persisting its result and streaming coarse-grained
    progress via the given queue. A repeated query within `CACHE_TTL_HOURS` is served from
    history unless `force_refresh`. `website`, if supplied, is stored as-is and displayed
    with a link out to `domain_finder`'s own WHOIS/DNS/CT analysis - never fetched or
    analyzed by this feature itself.

    Spawned as a background task by the route handler, same shape as git_recon/
    email_search/username_search - the request returns an SSE stream immediately rather
    than blocking for the scan's full duration.
    """
    on_event = queue_sink(queue)
    normalized_query = query.strip()
    normalized_website = website.strip() if website and website.strip() else None
    cancellable = TaskCancellable(asyncio.current_task())

    async def run_work(search_id: int) -> ScanOutcome:
        if not force_refresh:
            cached = await _cached_outcome(normalized_query, normalized_website)
            if cached is not None:
                return cached
        return await _scan(normalized_query, normalized_website)

    async def run_work_with_timeout(search_id: int) -> ScanOutcome:
        try:
            return await asyncio.wait_for(run_work(search_id), timeout=WALL_CLOCK_TIMEOUT_SECONDS)
        except TimeoutError:
            raise TimeoutError("Проверка заняла слишком много времени и была прервана") from None

    await RU_BUSINESS_CHECK_SCANS.execute(
        run_work_with_timeout,
        on_event,
        create_fields={"query": normalized_query},
        started_fields={"query": normalized_query},
        cancellable=cancellable,
        # Every other source's failure is absorbed by `run_source`; only ЕГРЮЛ (nothing to
        # check without it) and the wall-clock timeout end a scan as an expected failure -
        # anything else is a bug and surfaces as one.
        expected_exceptions=(EgrulError, TimeoutError),
    )
