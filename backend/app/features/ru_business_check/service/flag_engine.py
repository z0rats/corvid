"""Risk-flag engine: hard/soft flags computable from ЕГРЮЛ + РДЛ + арбитраж +
банкротство/Федресурс + Прозрачный бизнес + ФедСФМ + РНП alone.

Everything else in the full methodology (ФССП debts, movable-property pledges, sanctions,
blocked accounts, missing financial filings, ...) needs sources that don't exist yet - this
deliberately does not stub those out as false negatives. Per project decision, `risk_level`
must never be read as a full-methodology verdict while `pending_sources` is non-empty;
callers are responsible for surfacing that alongside it.
"""

import datetime
from typing import Literal

RiskLevel = Literal["low", "medium", "high"]

_RESOLVED_STATUS_KEYWORDS = ("заверш", "прекращ")


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


def _fedresurs_flags(fedresurs_result: dict) -> list[dict]:
    """Active bankruptcy is a hard flag - the guide's methodology puts it in the same
    tier as confirmed disqualification, not the softer arbitration treatment. A resolved/
    absent bankruptcy record (`is_active_bankruptcy: False`) produces no flag."""
    if not fedresurs_result.get("is_active_bankruptcy"):
        return []

    return [
        {
            "code": "active_bankruptcy",
            "severity": "hard",
            "title": "Активное дело о банкротстве",
            "detail": fedresurs_result.get("status_text")
            or "Найдено активное дело о банкротстве на Федресурсе",
        }
    ]


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


def _compute_risk_level(flags: list[dict]) -> RiskLevel:
    if any(f["severity"] == "hard" for f in flags):
        return "high"
    soft_count = sum(1 for f in flags if f["severity"] == "soft")
    if soft_count >= 3:
        return "high"
    if soft_count >= 1:
        return "medium"
    return "low"


def evaluate(
    egrul_data: dict,
    disqualification_result: dict,
    arbitration_cases: list[dict] | None = None,
    fedresurs_result: dict | None = None,
    pb_nalog_result: dict | None = None,
    fedsfm_result: dict | None = None,
    rnp_entries: list[dict] | None = None,
    *,
    fresh_registration_threshold_days: int,
    small_claim_amount_threshold: int = 100_000,
    large_claim_amount_threshold: int = 1_000_000,
    multiple_claims_defendant_threshold: int = 3,
    mass_address_threshold: int = 10,
) -> tuple[list[dict], RiskLevel]:
    """Pure function: combine ЕГРЮЛ + РДЛ + арбитраж + Федресурс + Прозрачный бизнес +
    ФедСФМ + РНП results into a flag list and a risk level. `risk_level` reflects only
    what the passed-in sources can see - a caller that doesn't have a given source's data
    yet simply omits that parameter (defaults to none checked, not a false "clean"
    result)."""
    flags: list[dict] = []

    fresh = _fresh_registration_flag(
        egrul_data, fresh_registration_threshold_days=fresh_registration_threshold_days
    )
    if fresh:
        flags.append(fresh)

    flags.extend(_disqualification_flags(disqualification_result))

    if arbitration_cases is not None:
        flags.extend(
            _arbitration_flags(
                arbitration_cases,
                small_claim_amount_threshold=small_claim_amount_threshold,
                large_claim_amount_threshold=large_claim_amount_threshold,
                multiple_claims_defendant_threshold=multiple_claims_defendant_threshold,
            )
        )

    if fedresurs_result is not None:
        flags.extend(_fedresurs_flags(fedresurs_result))

    if pb_nalog_result is not None:
        flags.extend(
            _pb_nalog_flags(pb_nalog_result, mass_address_threshold=mass_address_threshold)
        )

    if fedsfm_result is not None:
        flags.extend(_fedsfm_flags(fedsfm_result))

    if rnp_entries is not None:
        flags.extend(_zakupki_rnp_flags(rnp_entries))

    return flags, _compute_risk_level(flags)
