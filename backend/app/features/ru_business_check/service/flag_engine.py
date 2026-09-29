"""Risk-flag engine: hard/soft flags from whichever sources a scan checked, and one risk
level (`evaluate`).

Sources that aren't automated (ФССП, movable-property pledges, ...) are never stubbed out as
false negatives. The verdict can't look clean when a source able to rule out a hard flag
didn't run - that is `incomplete` (see `REQUIRED_SOURCES`, `docs/adr/0014-*.md`); the other
unchecked sources are listed in the scan's `pending_sources`.
"""

import datetime
from collections.abc import Collection, Mapping
from dataclasses import dataclass, fields
from typing import Any, Literal

from app.core.settings.ru_business_check.models import ru_business_check_settings_models as defaults
from app.features.ru_business_check.config.ru_business_check_config import REQUIRED_SOURCES

# "incomplete": no hard flag was found, but a source that could have raised one was not
# checked (see `REQUIRED_SOURCES`) - the absence of flags means nothing there.
RiskLevel = Literal["low", "medium", "high", "incomplete"]

_RESOLVED_STATUS_KEYWORDS = ("заверш", "прекращ")


@dataclass(frozen=True)
class Thresholds:
    """The tunable flag thresholds - field names match the `RuBusinessCheckSettings`
    columns, defaults match that model's defaults."""

    fresh_registration_threshold_days: int = defaults.FRESH_REGISTRATION_THRESHOLD_DAYS_DEFAULT
    small_claim_amount_threshold: int = defaults.SMALL_CLAIM_AMOUNT_THRESHOLD_DEFAULT
    large_claim_amount_threshold: int = defaults.LARGE_CLAIM_AMOUNT_THRESHOLD_DEFAULT
    multiple_claims_defendant_threshold: int = defaults.MULTIPLE_CLAIMS_DEFENDANT_THRESHOLD_DEFAULT
    mass_address_threshold: int = defaults.MASS_ADDRESS_THRESHOLD_DEFAULT
    equity_ratio_threshold: float = defaults.EQUITY_RATIO_THRESHOLD_DEFAULT
    current_ratio_threshold: float = defaults.CURRENT_RATIO_THRESHOLD_DEFAULT
    revenue_drop_threshold: float = defaults.REVENUE_DROP_THRESHOLD_DEFAULT

    @classmethod
    def from_settings(cls, settings_row: object) -> Thresholds:
        return cls(**{f.name: getattr(settings_row, f.name) for f in fields(cls)})


DEFAULT_THRESHOLDS = Thresholds()


@dataclass(frozen=True)
class SourceResults:
    """One scan's parsed source results. `None` = the source wasn't queried (its flags are
    skipped, never assumed clean); whether it *completed* is `evaluate`'s
    `checked_sources`."""

    egrul: dict
    disqualification: dict
    arbitration_cases: list[dict] | None = None
    fedresurs: dict | None = None
    pb_nalog: dict | None = None
    fedsfm: dict | None = None
    rnp_entries: list[dict] | None = None
    gir_bo: dict | None = None
    disqualified_dump: dict | None = None
    cbr_warning: dict | None = None
    ofac_sdn: dict | None = None

    @classmethod
    def from_source_data(cls, egrul: dict, data: Mapping[str, Any]) -> SourceResults:
        """`data` is `{source key: recorded result}` (`source_runner.SourceResult.data`) -
        the one place that knows which source key feeds which flag input."""
        arbitration = data.get("arbitration")
        rnp = data.get("zakupki_rnp")
        return cls(
            egrul=egrul,
            disqualification=data["disqualified_persons"],
            arbitration_cases=arbitration["cases"] if arbitration is not None else None,
            fedresurs=data.get("fedresurs"),
            pb_nalog=data.get("pb_nalog"),
            fedsfm=data.get("fedsfm"),
            rnp_entries=rnp["entries"] if rnp is not None else None,
            gir_bo=data.get("gir_bo"),
            disqualified_dump=data.get("disqualified_dump"),
            cbr_warning=data.get("cbr_warning"),
            ofac_sdn=data.get("ofac_sdn"),
        )


def _fresh_registration_flag(
    egrul_data: dict, *, fresh_registration_threshold_days: int
) -> dict | None:
    reg_date_str = egrul_data.get("registration_date")
    if not reg_date_str:
        return None
    try:
        reg_date = datetime.date.fromisoformat(reg_date_str)
    except ValueError:
        return None

    age_days = (datetime.date.today() - reg_date).days
    if age_days < 0 or age_days >= fresh_registration_threshold_days:
        return None

    return {
        "code": "fresh_registration",
        "severity": "soft",
        "title": "Свежая регистрация",
        "detail": (
            f"Компания/ИП зарегистрирована {age_days} дн. назад "
            f"(порог: {fresh_registration_threshold_days} дн.)"
        ),
    }


def _disqualification_flags(disqualification_result: dict) -> list[dict]:
    if not disqualification_result.get("matched"):
        return []

    matches = disqualification_result.get("matches") or []
    names = ", ".join(m.get("full_name", "") for m in matches) or "директор"

    if disqualification_result.get("requires_manual_review"):
        return [
            {
                "code": "disqualified_possible_match",
                "severity": "soft",
                "title": "Возможное совпадение в реестре дисквалифицированных лиц",
                "detail": (
                    f"Найдено совпадение по ФИО ({names}) в РДЛ, но реестр не даёт "
                    "дополнительного идентификатора для однозначной сверки — требуется "
                    "ручная проверка, прежде чем считать это подтверждённым фактом"
                ),
            }
        ]

    return [
        {
            "code": "disqualified_confirmed",
            "severity": "hard",
            "title": "Директор дисквалифицирован",
            "detail": f"Подтверждено совпадение в реестре дисквалифицированных лиц: {names}",
        }
    ]


def _disqualified_dump_flags(dump_result: dict) -> list[dict]:
    """Flags from the local ФНС dump (`disqualified_dump_service.lookup_dump`). Unlike the
    online search's name-only hit, a dump record carries the organization's ИНН, so a record
    that matches the director's ФИО **and** this company's ИНН and is in force today
    identifies the person well enough for a hard flag. Any other record carrying the
    company's ИНН - in force or expired - is a soft "look at this" signal with its dates
    (the person may be a former officer). Third parties' names stay in the panel, not in the
    flag text."""
    if not dump_result.get("checked"):
        return []

    if dump_result.get("director_confirmed"):
        # `lookup_dump` lists the confirming records first, so this is one of them.
        record = (dump_result.get("director_records") or [{}])[0]
        return [
            {
                "code": "disqualified_confirmed",
                "severity": "hard",
                "title": "Директор дисквалифицирован",
                "detail": (
                    f"В реестре дисквалифицированных лиц (выгрузка ФНС от "
                    f"{dump_result.get('dump_date')}) есть действующая запись "
                    f"№{record.get('record_number')} на {record.get('full_name')} — совпали ФИО "
                    f"и ИНН организации; срок {record.get('start_date')} — {record.get('end_date')}"
                ),
            }
        ]

    company_records = dump_result.get("company_records") or []
    if not company_records:
        return []
    active = sum(1 for r in company_records if r.get("active"))
    listed = "; ".join(
        f"запись №{r.get('record_number')}, {r.get('start_date')} — {r.get('end_date')} "
        f"({'действует' if r.get('active') else 'истекла'})"
        for r in company_records
    )
    return [
        {
            "code": "company_disqualified_officer",
            "severity": "soft",
            "title": (
                "У компании есть дисквалифицированное должностное лицо"
                if active
                else "У компании были дисквалифицированные должностные лица"
            ),
            "detail": (
                f"В реестре дисквалифицированных лиц записи с ИНН этой организации: {listed}. "
                "Это могут быть бывшие руководители — проверьте, не занимает ли лицо "
                "должность сейчас"
            ),
        }
    ]


def _cbr_warning_flags(cbr_result: dict) -> list[dict]:
    """Soft, and worded as the regulator's *statement* - the list gives "signs" (of a
    pyramid, illegal lending, ...), not a court finding. A "clone" entry (the note says it
    misuses a legitimate participant's data) means the ИНН owner is the impersonated party,
    so it raises nothing against them."""
    if not cbr_result.get("checked"):
        return []
    records = [r for r in cbr_result.get("records") or [] if not r.get("is_clone")]
    if not records:
        return []
    signs = "; ".join(sorted({r.get("sign") or "признаки не указаны" for r in records}))
    since = min((r["listed_at"] for r in records if r.get("listed_at")), default=None)
    return [
        {
            "code": "cbr_warning_list",
            "severity": "soft",
            "title": "Банк России включил компанию в список признаков нелегальной деятельности",
            "detail": (
                f"Банк России сообщает о признаках: {signs}"
                + (f"; в списке с {since}" if since else "")
                + ". Это заявление регулятора, а не решение суда — сверьте карточку на cbr.ru"
            ),
        }
    ]


def _ofac_sdn_flags(ofac_result: dict) -> list[dict]:
    """Hard: an exact-ИНН match on a published sanctions list is a fact about that list
    (worded as such - it is a US designation, not a Russian-law prohibition). Only a match is
    reported; the list's coverage of ИНН is partial, so *no* match says nothing."""
    if not ofac_result.get("checked"):
        return []
    records = ofac_result.get("records") or []
    if not records:
        return []
    listed = "; ".join(
        f"{r.get('name')} ({r.get('programs') or 'программа не указана'})" for r in records
    )
    return [
        {
            "code": "ofac_sdn_listed",
            "severity": "hard",
            "title": "Включена в санкционный список OFAC SDN (США)",
            "detail": (
                f"Точное совпадение по ИНН с записью списка OFAC SDN: {listed}. Это статус в "
                "американском перечне (со стороны США), не запрет по российскому праву"
            ),
        }
    ]


def _fedsfm_flags(fedsfm_result: dict) -> list[dict]:
    """Same treatment as `_disqualification_flags`'s soft branch - fedsfm.ru's list gives
    no disambiguating identifier beyond full name, so a match is never a confirmed hard
    flag, only `requires_manual_review` (see `fedsfm_service.py`'s module docstring)."""
    if not fedsfm_result.get("matched"):
        return []

    matches = fedsfm_result.get("matches") or []
    names = ", ".join(m.get("full_name", "") for m in matches) or "директор"

    return [
        {
            "code": "fedsfm_possible_match",
            "severity": "soft",
            "title": "Возможное совпадение в перечне Росфинмониторинга",
            "detail": (
                f"Найдено совпадение по ФИО ({names}) в перечне организаций и физических "
                "лиц, причастных к терроризму/финансированию распространения оружия "
                "массового уничтожения (fedsfm.ru), но перечень не даёт дополнительного "
                "идентификатора для однозначной сверки — требуется ручная проверка, "
                "прежде чем считать это подтверждённым фактом"
            ),
        }
    ]


def _zakupki_rnp_flags(rnp_entries: list[dict]) -> list[dict]:
    """Unlike РДЛ/ФедСФМ's name-only matching, a РНП match *is* a confirmed hard flag -
    `zakupki_rnp_service.py` already re-filters to an exact ИНН match server-side, so
    there's no name-collision ambiguity to hedge against here."""
    if not rnp_entries:
        return []

    laws = sorted({e.get("law") for e in rnp_entries if e.get("law")})
    names = ", ".join(sorted({e.get("name", "") for e in rnp_entries if e.get("name")}))

    return [
        {
            "code": "rnp_confirmed",
            "severity": "hard",
            "title": "Запись в реестре недобросовестных поставщиков",
            "detail": (
                f"Найдено {len(rnp_entries)} действующ(ая/их) запис(ь/и) в РНП"
                + (f" ({', '.join(laws)})" if laws else "")
                + (f": {names}" if names else "")
            ),
        }
    ]


def _is_resolved_status(status: str | None) -> bool:
    if not status:
        return False
    lowered = status.lower()
    return any(keyword in lowered for keyword in _RESOLVED_STATUS_KEYWORDS)


def _arbitration_flags(
    cases: list[dict],
    *,
    small_claim_amount_threshold: int,
    large_claim_amount_threshold: int,
    multiple_claims_defendant_threshold: int,
) -> list[dict]:
    """The guide's formal жёсткие/мягкие list never puts arbitration in the hard-flag
    tier by itself (unlike disqualification/bankruptcy) - only "единичный мелкий иск как
    ответчик, разрешённый" is named, as soft. A "вал исков на крупные суммы" is called out
    as a red flag in the guide's step-by-step checklist but given no formal severity, so
    it's treated here as soft too - the existing 3+-soft-flags-escalates-to-high
    aggregation (see `_compute_risk_level`) already lets enough of these accumulate into
    a high verdict without inventing a new hard-flag category not in the methodology.
    """
    defendant_cases = [c for c in cases if c.get("role") == "defendant"]
    if not defendant_cases:
        return []

    flags: list[dict] = []

    if len(defendant_cases) == 1:
        case = defendant_cases[0]
        amount = case.get("claim_amount")
        is_small = amount is None or amount < small_claim_amount_threshold
        if _is_resolved_status(case.get("status")) and is_small:
            flags.append(
                {
                    "code": "single_small_resolved_claim",
                    "severity": "soft",
                    "title": "Единичный небольшой иск как ответчик",
                    "detail": (
                        f"Одно разрешённое дело в качестве ответчика: {case.get('case_number')}"
                    ),
                }
            )

    is_multiple = len(defendant_cases) >= multiple_claims_defendant_threshold
    has_large_claim = any(
        (c.get("claim_amount") or 0) >= large_claim_amount_threshold for c in defendant_cases
    )
    if is_multiple or has_large_claim:
        flags.append(
            {
                "code": "significant_or_multiple_claims_as_defendant",
                "severity": "soft",
                "title": "Существенные или многочисленные иски как ответчик",
                "detail": (
                    f"{len(defendant_cases)} дел(о) в качестве ответчика"
                    + (", включая иск(и) на крупную сумму" if has_large_claim else "")
                ),
            }
        )

    return flags


_FEDRESURS_SIGNAL_TITLES = {
    "creditor_bankruptcy_intent": "Кредитор намерен обратиться в суд с заявлением о банкротстве",
    "debtor_bankruptcy_intent": "Компания намерена обратиться в суд с заявлением о банкротстве",
    "liquidation_decision": "Опубликовано решение о ликвидации",
    "unreliable_information": "Сообщение о недостоверности сведений в ЕГРЮЛ",
    "reorganization": "Сообщение о реорганизации (за последний год)",
}


def _fedresurs_flags(fedresurs_result: dict) -> list[dict]:
    """Active bankruptcy is a hard flag - the guide's methodology puts it in the same
    tier as confirmed disqualification, not the softer arbitration treatment. A resolved/
    absent bankruptcy record (`is_active_bankruptcy: False`) produces no flag.

    Everything softer is a *signal*: an unrecognized `status` text (never silently read as
    clean) and the publication-message signals `fedresurs_service.parse_publications`
    already role-checked (a message only becomes a signal when the searched company is its
    subject, not merely a participant of someone else's)."""
    flags: list[dict] = []

    if fedresurs_result.get("is_active_bankruptcy"):
        flags.append(
            {
                "code": "active_bankruptcy",
                "severity": "hard",
                "title": "Активное дело о банкротстве",
                "detail": fedresurs_result.get("status_text")
                or "Найдено активное дело о банкротстве на Федресурсе",
            }
        )
    elif fedresurs_result.get("found") and fedresurs_result.get("status_recognized") is False:
        flags.append(
            {
                "code": "fedresurs_status_unrecognized",
                "severity": "soft",
                "title": "Нераспознанный статус на Федресурсе",
                "detail": (
                    f"Федресурс вернул статус «{fedresurs_result.get('status_text') or '—'}», "
                    "которого нет среди известных — требуется ручная проверка карточки"
                ),
            }
        )

    by_code: dict[str, list[dict]] = {}
    for signal in fedresurs_result.get("signals") or []:
        by_code.setdefault(signal["code"], []).append(signal)
    for code, title in _FEDRESURS_SIGNAL_TITLES.items():
        signals = by_code.get(code)
        if not signals:
            continue
        dates = ", ".join(sorted({s["date"] for s in signals}, reverse=True)[:3])
        flags.append(
            {
                "code": code,
                "severity": "soft",
                "title": title,
                "detail": f"Сообщений на Федресурсе: {len(signals)} (последние даты: {dates})",
            }
        )

    return flags


def _pb_nalog_flags(pb_nalog_result: dict, *, mass_address_threshold: int) -> list[dict]:
    """Soft and deliberately cautious: `mass_address_count` alone doesn't distinguish a
    shell-company address mill from a large legitimate group sharing one HQ address with
    its own subsidiaries (confirmed live against a real large bank - 16 other entities at
    the same address, all its own group companies) - the threshold only screens for "worth
    a human look", not a confirmed red flag.

    pb.nalog.ru's `is_p_ruk` field was tried here too as a second soft flag, but dropped
    after manual re-verification found nothing in pb.nalog.ru's own UI corresponding to it
    - see `pb_nalog_service.py`'s module docstring."""
    flags: list[dict] = []

    mass_address_count = pb_nalog_result.get("mass_address_count") or 0
    if mass_address_count >= mass_address_threshold:
        flags.append(
            {
                "code": "mass_registration_address",
                "severity": "soft",
                "title": "Признаки адреса массовой регистрации",
                "detail": (
                    f"По данным Прозрачного бизнеса, по этому адресу зарегистрировано "
                    f"ещё {mass_address_count} юр. лиц(а) — может быть как признаком "
                    f"«адреса массовой регистрации», так и обычным адресом группы "
                    f"компаний; требуется ручная проверка"
                ),
            }
        )

    return flags


def _gir_bo_flags(
    gir_bo_result: dict,
    *,
    equity_ratio_threshold: float,
    current_ratio_threshold: float,
    revenue_drop_threshold: float,
) -> list[dict]:
    """Soft flags from the latest filed statements (`years`, newest first). Ratios are
    scale-free, so ГИР БО's thousand-rubles unit doesn't matter. A ratio is only computed
    when both its lines are present and the denominator is positive - a missing line is
    "not assessed", never a pass or a fail. The revenue comparison needs the two
    consecutive years (a gap in filings isn't a year-over-year drop)."""
    years = gir_bo_result.get("years") or []
    if not (gir_bo_result.get("checked") and years):
        return []

    latest = years[0]
    year = latest.get("year")
    flags: list[dict] = []

    equity, assets = latest.get("equity"), latest.get("assets")
    if equity is not None and assets is not None and assets > 0:
        ratio = equity / assets
        if ratio < equity_ratio_threshold:
            flags.append(
                {
                    "code": "low_equity_ratio",
                    "severity": "soft",
                    "title": "Низкая доля собственного капитала",
                    "detail": (
                        f"Капитал и резервы / итог баланса = {ratio:.2f} "
                        f"(порог {equity_ratio_threshold:g}) по отчётности за {year} г."
                        + (" Капитал отрицательный." if equity < 0 else "")
                    ),
                }
            )

    current_assets, current_liabilities = (
        latest.get("current_assets"),
        latest.get("current_liabilities"),
    )
    if current_assets is not None and current_liabilities is not None and current_liabilities > 0:
        ratio = current_assets / current_liabilities
        if ratio < current_ratio_threshold:
            flags.append(
                {
                    "code": "low_current_liquidity",
                    "severity": "soft",
                    "title": "Низкая текущая ликвидность",
                    "detail": (
                        f"Оборотные активы / краткосрочные обязательства = {ratio:.2f} "
                        f"(порог {current_ratio_threshold:g}) по отчётности за {year} г."
                    ),
                }
            )

    previous = years[1] if len(years) > 1 else None
    if previous is not None and previous.get("year") == (year or 0) - 1:
        cur_revenue, prev_revenue = latest.get("revenue"), previous.get("revenue")
        if cur_revenue is not None and prev_revenue is not None and prev_revenue > 0:
            drop = (prev_revenue - cur_revenue) / prev_revenue
            if drop > revenue_drop_threshold:
                flags.append(
                    {
                        "code": "revenue_drop",
                        "severity": "soft",
                        "title": "Резкое падение выручки",
                        "detail": (
                            f"Выручка упала на {drop:.0%} за {year} г. по сравнению с "
                            f"{previous['year']} г. (порог {revenue_drop_threshold:.0%})"
                        ),
                    }
                )

    return flags


def _compute_risk_level(
    flags_by_source: dict[str, list[dict]], checked_sources: Collection[str] | None
) -> RiskLevel:
    """`checked_sources=None` means the caller asserts every required source ran (only
    unit tests of a single source's flags do this) - the scan (`_scan`) always passes the
    real list, so a failed required source can never yield a clean-looking verdict."""
    all_flags = [f for source_flags in flags_by_source.values() for f in source_flags]
    if any(f["severity"] == "hard" for f in all_flags):
        return "high"

    # Each source counts at most once toward the "3+ soft flags -> high" escalation: one
    # source with several related signals (or a new source emitting many) must not
    # single-handedly reach "high" - it takes independent sources agreeing.
    soft_sources = sum(
        1
        for source_flags in flags_by_source.values()
        if any(f["severity"] == "soft" for f in source_flags)
    )
    if soft_sources >= 3:
        return "high"

    if checked_sources is not None and not REQUIRED_SOURCES.issubset(checked_sources):
        return "incomplete"

    if soft_sources >= 1:
        return "medium"
    return "low"


def evaluate(
    results: SourceResults,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    checked_sources: Collection[str] | None = None,
) -> tuple[list[dict], RiskLevel]:
    """Pure function: flags from every queried source plus one risk level. `checked_sources`
    (the source keys that actually completed) keeps `low`/`medium` from being reported when
    a `REQUIRED_SOURCES` member is missing - see `_compute_risk_level`."""
    flags_by_source: dict[str, list[dict]] = {}

    fresh = _fresh_registration_flag(
        results.egrul,
        fresh_registration_threshold_days=thresholds.fresh_registration_threshold_days,
    )
    if fresh:
        flags_by_source["egrul"] = [fresh]

    online_flags = _disqualification_flags(results.disqualification)
    if results.disqualified_dump is not None:
        dump_flags = _disqualified_dump_flags(results.disqualified_dump)
        if any(f["code"] == "disqualified_confirmed" for f in dump_flags):
            # The dump's ФИО+ИНН match supersedes the online search's name-only hit.
            online_flags = [
                f
                for f in online_flags
                if f["code"] not in ("disqualified_possible_match", "disqualified_confirmed")
            ]
        flags_by_source["disqualified_dump"] = dump_flags
    flags_by_source["disqualified_persons"] = online_flags

    if results.arbitration_cases is not None:
        flags_by_source["arbitration"] = _arbitration_flags(
            results.arbitration_cases,
            small_claim_amount_threshold=thresholds.small_claim_amount_threshold,
            large_claim_amount_threshold=thresholds.large_claim_amount_threshold,
            multiple_claims_defendant_threshold=thresholds.multiple_claims_defendant_threshold,
        )
    if results.fedresurs is not None:
        flags_by_source["fedresurs"] = _fedresurs_flags(results.fedresurs)
    if results.pb_nalog is not None:
        flags_by_source["pb_nalog"] = _pb_nalog_flags(
            results.pb_nalog, mass_address_threshold=thresholds.mass_address_threshold
        )
    if results.fedsfm is not None:
        flags_by_source["fedsfm"] = _fedsfm_flags(results.fedsfm)
    if results.rnp_entries is not None:
        flags_by_source["zakupki_rnp"] = _zakupki_rnp_flags(results.rnp_entries)
    if results.ofac_sdn is not None:
        flags_by_source["ofac_sdn"] = _ofac_sdn_flags(results.ofac_sdn)
    if results.cbr_warning is not None:
        flags_by_source["cbr_warning"] = _cbr_warning_flags(results.cbr_warning)
    if results.gir_bo is not None:
        flags_by_source["gir_bo"] = _gir_bo_flags(
            results.gir_bo,
            equity_ratio_threshold=thresholds.equity_ratio_threshold,
            current_ratio_threshold=thresholds.current_ratio_threshold,
            revenue_drop_threshold=thresholds.revenue_drop_threshold,
        )

    flags = [f for source_flags in flags_by_source.values() for f in source_flags]
    return flags, _compute_risk_level(flags_by_source, checked_sources)
