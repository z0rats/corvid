import asyncio
import datetime
import logging
from collections.abc import Awaitable, Callable
from typing import Any

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


def _empty_source_fields() -> dict[str, Any]:
    """The dedicated sources' "not checked" results - what a scan records for a source it
    couldn't query (no ИНН/director, the source failed, or the query was ambiguous)."""
    return {
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
        "rnp_data": {"checked": False, "entries": []},
        "rnp_raw": "",
        "extra_data": {},
        "extra_raw": {},
        "raw_sha256": {},
    }


async def _attempt(
    source: str,
    call: Callable[[], Awaitable[Any]],
    error: type[Exception],
    *,
    default: Any,
    succeeded: list[str],
    subject: str,
) -> Any:
    """Run one source. A failure (its own `error` class - rate-limited, blocked, schema
    drift) is logged and yields `default` without discarding the other sources; only a
    success adds `source` to `succeeded`, so `checked_sources` reflects what really ran."""
    try:
        result = await call()
    except error as exc:
        logger.warning("ru_business_check: %s lookup failed for %r: %s", source, subject, exc)
        return default
    succeeded.append(source)
    return result


def _extra_sources() -> list[tuple[str, Callable[..., Awaitable[tuple[dict, str]]], type]]:
    """Remote sources kept in `extra_data`/`extra_raw` (docs/adr/0014-*.md): `(key, fetcher
    taking (inn, is_individual=), error class)`. Resolved at call time so tests can
    monkeypatch the fetchers by name."""
    return [
        ("gir_bo", fetch_gir_bo_financials, GirBoError),
        ("msp", fetch_msp_status, MspError),
    ]


def _local_lookups() -> list[tuple[str, Callable[..., Awaitable[dict]], type, bool]]:
    """Matches against the locally cached dumps, `(key, lookup taking (db, inn, director),
    error class, applies to an ИП)`. A dump that isn't loaded yet raises its error, so the
    source lands in `pending_sources` rather than reading as "not listed"."""
    return [
        (
            "disqualified_dump",
            lambda db, inn, director: lookup_dump(db, inn, director),
            DisqualifiedDumpError,
            True,
        ),
        # SDN entries carry both 10-digit (entity) and 12-digit (individual) ИНН.
        ("ofac_sdn", lambda db, inn, director: lookup_ofac_list(db, inn), OfacSdnError, True),
        # The ЦБ list carries only legal entities' ИНН.
        ("cbr_warning", lambda db, inn, director: lookup_cbr_list(db, inn), CbrWarningError, False),
    ]


async def cancel_scan(search_id: int) -> bool:
    return await ScanRun.cancel(FEATURE_NAME, search_id)


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
            **_empty_source_fields(),
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


async def _run_live_sources(egrul_data: dict, succeeded: list[str]) -> dict[str, Any]:
    """Query every dedicated live source and return their outcome fields (parsed result +
    raw payload each), appending each success to `succeeded` in order."""
    fields = _empty_source_fields()
    inn = egrul_data.get("inn")
    director = egrul_data.get("director_name")
    is_individual = _entity_type_from_ogrn(egrul_data.get("ogrn")) == INDIVIDUAL

    def attempt(source, call, error, default):
        return _attempt(
            source,
            call,
            error,
            default=(default, ""),
            succeeded=succeeded,
            subject=director if source in ("disqualified_persons", "fedsfm") else inn,
        )

    if director:
        fields["disqualification_result"], fields["disqualification_raw"] = await attempt(
            "disqualified_persons",
            lambda: check_disqualified(director),
            DisqualifiedPersonsError,
            fields["disqualification_result"],
        )
    if inn:
        cases, fields["arbitration_raw"] = await attempt(
            "arbitration",
            lambda: fetch_arbitration_cases(inn),
            ArbitrationError,
            [],
        )
        fields["arbitration_data"] = {"checked": "arbitration" in succeeded, "cases": cases}
        fields["fedresurs_data"], fields["fedresurs_raw"] = await attempt(
            "fedresurs",
            lambda: fetch_fedresurs_status(inn, is_individual=is_individual),
            FedresursError,
            fields["fedresurs_data"],
        )
        if "fedresurs" in succeeded and not is_fully_checked(
            fields["fedresurs_data"], is_individual=is_individual
        ):
            # Status read, publications not: the bankruptcy-intent/liquidation signals were
            # never looked at, so the source doesn't count as checked (-> `incomplete`).
            succeeded.remove("fedresurs")
        fields["pb_nalog_data"], fields["pb_nalog_raw"] = await attempt(
            "pb_nalog",
            lambda: fetch_pb_nalog_profile(inn, is_individual=is_individual),
            PbNalogError,
            fields["pb_nalog_data"],
        )
    if director:
        fields["fedsfm_result"], fields["fedsfm_raw"] = await attempt(
            "fedsfm",
            lambda: check_terrorist_list(director),
            FedsfmError,
            fields["fedsfm_result"],
        )
    if inn:
        entries, fields["rnp_raw"] = await attempt(
            "zakupki_rnp",
            lambda: fetch_rnp_entries(inn),
            ZakupkiRnpError,
            [],
        )
        fields["rnp_data"] = {"checked": "zakupki_rnp" in succeeded, "entries": entries}
    return fields


async def _run_extra_and_local_sources(
    inn: str,
    director: str | None,
    is_individual: bool,
    succeeded: list[str],
    not_applicable: list[str],
) -> tuple[dict, dict]:
    """`extra_data`/`extra_raw` for the remote extra sources, then the local dump lookups
    (which have no remote payload of their own). A lookup that can't apply to this entity
    (the ЦБ list for an ИП) is neither checked nor pending: its key goes to
    `not_applicable` and its explanation to `extra_data`."""
    data: dict = {}
    raw: dict = {}
    for key, fetch, error in _extra_sources():
        result = await _attempt(
            key,
            lambda fetch=fetch: fetch(inn, is_individual=is_individual),
            error,
            default=None,
            succeeded=succeeded,
            subject=inn,
        )
        if result is not None:
            data[key], raw[key] = result
    async with managed_session() as db:
        for key, lookup, error, applies_to_individual in _local_lookups():
            if is_individual and not applies_to_individual:
                not_applicable.append(key)
                data[key] = not_applicable_result()
                continue
            result = await _attempt(
                key,
                lambda lookup=lookup: lookup(db, inn, director),
                error,
                default=None,
                succeeded=succeeded,
                subject=inn,
            )
            if result is not None:
                data[key] = result
    return data, raw


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

    succeeded = ["egrul"]
    not_applicable: list[str] = []
    fields = await _run_live_sources(egrul_data, succeeded)
    inn = egrul_data.get("inn")
    entity_type = _entity_type_from_ogrn(egrul_data.get("ogrn"))
    if inn:
        fields["extra_data"], fields["extra_raw"] = await _run_extra_and_local_sources(
            inn,
            egrul_data.get("director_name"),
            entity_type == INDIVIDUAL,
            succeeded,
            not_applicable,
        )

    extra = fields["extra_data"]
    flags, risk_level = flag_engine.evaluate(
        flag_engine.SourceResults(
            egrul=egrul_data,
            disqualification=fields["disqualification_result"],
            arbitration_cases=fields["arbitration_data"]["cases"],
            fedresurs=fields["fedresurs_data"],
            pb_nalog=fields["pb_nalog_data"],
            fedsfm=fields["fedsfm_result"],
            rnp_entries=fields["rnp_data"]["entries"],
            gir_bo=extra.get("gir_bo"),
            disqualified_dump=extra.get("disqualified_dump"),
            cbr_warning=extra.get("cbr_warning"),
            ofac_sdn=extra.get("ofac_sdn"),
        ),
        thresholds,
        succeeded,
    )
    logger.info("ru_business_check scan for %r: risk=%s, %d flag(s)", query, risk_level, len(flags))

    fields["raw_sha256"] = digest_payloads(
        {
            "egrul": egrul_raw,
            "disqualified_persons": fields["disqualification_raw"],
            "arbitration": fields["arbitration_raw"],
            "fedresurs": fields["fedresurs_raw"],
            "pb_nalog": fields["pb_nalog_raw"],
            "fedsfm": fields["fedsfm_raw"],
            "zakupki_rnp": fields["rnp_raw"],
            **fields["extra_raw"],
        }
    )
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

    await ScanRun.execute(
        FEATURE_NAME,
        RuBusinessCheckSearch,
        run_work_with_timeout,
        on_event,
        columns=SCAN_COLUMNS,
        create_fields={"query": normalized_query},
        started_fields={"query": normalized_query},
        cancellable=cancellable,
        # Every other source's failure is absorbed by `_attempt`; only ЕГРЮЛ (nothing to
        # check without it) and the wall-clock timeout end a scan as an expected failure -
        # anything else is a bug and surfaces as one.
        expected_exceptions=(EgrulError, TimeoutError),
    )
