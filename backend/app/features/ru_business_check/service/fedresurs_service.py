"""Client for fedresurs.ru's own search backend - the Unified Federal Register of
Bankruptcy Information (ЕФРСБ), covering both legal-entity and individual bankruptcy.

Fixed host, only the ИНН is user-supplied - never the host - so this intentionally does
NOT go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against live captures - 2026-08-13 (search) and 2026-09-28 (publications), via
this environment's own network access.** Confirmed live: `/backend/companies`/
`/backend/persons` both take a `searchString` query param (an ИНН or name) plus
`limit`/`offset`, respond with `{"pageData": [...], "found": N}`, and require a
`Referer: https://fedresurs.ru/` header (omitting it returns a bare 403 with no body). Each
`pageData` row's `status` field is free-text Russian and is itself the bankruptcy signal -
confirmed against a clean entity (ПАО СБЕРБАНК, ИНН 7707083893 -> `"Действующее"`) and two
live bankrupt entities (one at the "наблюдение" stage, one at "конкурсное производство").
`https://fedresurs.ru/company/<guid>` is a confirmed-live deep link to a found company's
own card; the equivalent for a person (`/person/<guid>`) is assumed by API-path symmetry
with `/backend/persons`, not independently confirmed.

**Publications** (legal entities only): `GET /backend/companies/<guid>/publications?limit=15
&offset=0` -> `{"pageData": [message...], "found": N}`. Each message carries `type`
(free-text Russian), `publicationType` (`SfactMessage` = a "сообщение о факте деятельности";
other values are ЕФРСБ bankruptcy-proceeding messages, already covered by the search row's
`status`), `publisher` (`{guid, name, type}`, sometimes `null`), `participants` (every party
named in the message), `datePublish`, `isAnnulled`, `number`, `guid`. **Role matters**: a
message's `participants` includes its own publisher, so ПАО СБЕРБАНК appears as a
participant of the hundreds of "намерение кредитора" messages it publishes about *other*
companies' debts - reading "company is named in a message" as "company is the subject"
would flag the bank itself. Each message type therefore carries a role rule
(`_MESSAGE_RULES`), captured from live responses, deciding when the searched company is the
message's subject. Only the first page is read: a found-count above it is surfaced as
truncation (what is found is right, absence is not asserted), never as "clean".

Per project decision (`docs/adr/0006-*.md`), a block from fedresurs.ru's anti-bot layer
(Qrator - confirmed live as an HTTP 451 on an overly broad test query) is never worked
around, only surfaced as a clean `FedresursBlocked` error - same policy as
`arbitration_service.py`'s `ArbitrationBlocked`.
"""

import datetime
import json
import logging
import re
from typing import Literal

import httpx

from app.features.ru_business_check.service.source_contract import (
    require_dict,
    require_fields,
    require_list_field,
)

logger = logging.getLogger(__name__)

FEDRESURS_BASE_URL = "https://fedresurs.ru"
REQUEST_TIMEOUT_SECONDS = 20.0
RESULTS_LIMIT = 15
PUBLICATIONS_LIMIT = 15
SOURCE_LABEL = "Федресурс"

# A reorganization announcement is only a live signal while the procedure is plausibly
# still running - an expert choice, not a legal norm. Without a window, a company that
# absorbed another years ago would carry the signal forever.
REORGANIZATION_FRESH_DAYS = 365


class FedresursError(ValueError):
    """The service itself failed/timed out"""


class FedresursBlocked(FedresursError):
    """fedresurs.ru's anti-bot layer (Qrator) rejected the request - confirmed live as an
    HTTP 451 on an overly broad test query. Same policy as `ArbitrationBlocked` - never
    worked around, surfaced as a clean error rather than a raw HTTP status leaking to the
    end user."""


# message `type` -> (signal code, role rule). Rules from live responses (2026-09-26/28):
# a creditor's intent is published by the creditor with the debtor among `participants`;
# a debtor's intent and a liquidation decision are published by the company itself;
# a "недостоверность" notice is published by the ЕГРЮЛ (no guid) naming the company as a
# participant; a reorganization is published by every participating company, with all
# sides in `participants`, and who absorbs whom is not visible in the JSON.
_ROLE_PARTICIPANT_NOT_PUBLISHER = "participant_not_publisher"
_ROLE_PUBLISHER = "publisher"
_ROLE_PARTICIPANT = "participant"
_ROLE_ANY = "any"

_MESSAGE_RULES: dict[str, tuple[str, str]] = {
    "Намерение кредитора обратиться в суд с заявлением о банкротстве": (
        "creditor_bankruptcy_intent",
        _ROLE_PARTICIPANT_NOT_PUBLISHER,
    ),
    "Намерение должника обратиться в суд с заявлением о банкротстве": (
        "debtor_bankruptcy_intent",
        _ROLE_PUBLISHER,
    ),
    "Ликвидация юридического лица": ("liquidation_decision", _ROLE_PUBLISHER),
    "Недостоверность сведений": ("unreliable_information", _ROLE_PARTICIPANT),
    "Реорганизация юридического лица": ("reorganization", _ROLE_ANY),
}

_FRESHNESS_DAYS = {"reorganization": REORGANIZATION_FRESH_DAYS}
_ISO_DATE_PREFIX = re.compile(r"\d{4}-\d{2}-\d{2}")


def _check_response(response: httpx.Response) -> dict:
    if response.status_code in (401, 403, 429, 451):
        raise FedresursBlocked(
            "fedresurs.ru временно ограничил доступ (защита от частых запросов) — попробуйте позже"
        )
    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise FedresursError(
            f"fedresurs.ru вернул ошибку: HTTP {exc.response.status_code}"
        ) from exc
    try:
        data = response.json()
    except ValueError as exc:
        raise FedresursError("fedresurs.ru вернул не-JSON (возможна антибот-страница)") from exc
    return require_dict(data, error=FedresursError, label=SOURCE_LABEL)


async def _get_json(client: httpx.AsyncClient, path: str, params: dict, referer: str) -> dict:
    try:
        response = await client.get(
            f"{FEDRESURS_BASE_URL}{path}", params=params, headers={"Referer": referer}
        )
    except httpx.HTTPError as exc:
        raise FedresursError(f"fedresurs.ru недоступен: {exc}") from exc
    return _check_response(response)


def _pick_exact_match(page_data: list[dict], inn: str) -> dict | None:
    """Pure function: `searchString` is a fuzzy/text search (confirmed live - a short
    query returned unrelated rows), so the result row must be picked by an exact ИНН
    match rather than assuming the first (or only) row is the right one."""
    return next((row for row in page_data if row.get("inn") == inn), None)


_ACTIVE_BANKRUPTCY_KEYWORDS = (
    "несостоятельн",
    "конкурсное производство",
    "наблюдение",
    "внешнее управление",
    "финансовое оздоровление",
    "реструктуризация долгов",
    "реализация имущества",
)
# "завершено"/"прекращено" are ЕФРСБ stage names for a procedure that is over.
_RESOLVED_KEYWORDS = ("прекращ", "заверш")
# Only "Действующее" (a company in no bankruptcy procedure) is a live-observed clean value.
_CLEAN_KEYWORDS = ("действующ",)

StatusKind = Literal["active_bankruptcy", "resolved", "clean", "unrecognized"]


def pick_search_row(data: dict, inn: str) -> dict | None:
    """Pure function: the search payload -> the row for exactly `inn`, or None when the
    register has no such entity. Raises `FedresursError` on drift, and when the exact ИНН
    isn't on a page that is itself incomplete (`found` above the page) - absence can't be
    asserted then."""
    rows = require_list_field(
        data, "pageData", error=FedresursError, label=SOURCE_LABEL, where="поиске"
    )
    for row in rows:
        require_fields(
            row, ("inn",), error=FedresursError, label=SOURCE_LABEL, where="строке поиска"
        )
    match = _pick_exact_match(rows, inn)
    if match is None:
        found_total = data.get("found")
        if not isinstance(found_total, int) or found_total > len(rows):
            raise FedresursError(
                "fedresurs.ru: выдача поиска усечена или без счётчика — точный ИНН не "
                "найден на первой странице, «нет в реестре» утверждать нельзя"
            )
        return None
    return require_fields(
        match, ("guid", "status"), error=FedresursError, label=SOURCE_LABEL, where="строке поиска"
    )


def classify_status(status_text: str | None) -> StatusKind:
    """Pure function: classify fedresurs.ru's free-text `status`. Anything outside the
    live-observed vocabulary is `"unrecognized"` - which `flag_engine` turns into a soft
    "check manually" flag - rather than silently reading as clean."""
    if not status_text:
        return "unrecognized"
    lowered = status_text.lower()
    if any(keyword in lowered for keyword in _RESOLVED_KEYWORDS):
        return "resolved"
    if any(keyword in lowered for keyword in _ACTIVE_BANKRUPTCY_KEYWORDS):
        return "active_bankruptcy"
    if any(keyword in lowered for keyword in _CLEAN_KEYWORDS):
        return "clean"
    return "unrecognized"


def _is_active_bankruptcy(status_text: str | None) -> bool:
    return classify_status(status_text) == "active_bankruptcy"


def _profile_url(guid: str | None, *, is_individual: bool) -> str | None:
    if not guid:
        return None
    kind = "person" if is_individual else "company"
    return f"{FEDRESURS_BASE_URL}/{kind}/{guid}"


def _role_of(message: dict, company_guid: str) -> str | None:
    publisher = message.get("publisher")
    if isinstance(publisher, dict) and publisher.get("guid") == company_guid:
        return "publisher"
    if any(
        isinstance(p, dict) and p.get("guid") == company_guid
        for p in message.get("participants") or []
    ):
        return "participant"
    return None


def _validate_message(message: object) -> dict:
    """Contract for one publication: the fields the role/date logic relies on. A message
    missing one is drift, and reading around it would risk a false signal (or a missed one)."""
    message = require_fields(
        message,
        ("type", "publicationType", "datePublish", "isAnnulled", "guid"),
        error=FedresursError,
        label=SOURCE_LABEL,
        where="сообщении публикации",
    )
    date_publish = message["datePublish"]
    if not isinstance(date_publish, str) or not _ISO_DATE_PREFIX.match(date_publish):
        raise FedresursError(f"{SOURCE_LABEL}: схема ответа изменилась — datePublish не дата")
    if not isinstance(message["isAnnulled"], bool):
        raise FedresursError(f"{SOURCE_LABEL}: схема ответа изменилась — isAnnulled не bool")
    publisher = message.get("publisher")
    participants = message.get("participants")
    if publisher is not None and not isinstance(publisher, dict):
        raise FedresursError(f"{SOURCE_LABEL}: схема ответа изменилась — publisher не объект")
    if participants is not None and (
        not isinstance(participants, list) or not all(isinstance(p, dict) for p in participants)
    ):
        raise FedresursError(f"{SOURCE_LABEL}: схема ответа изменилась — participants не список")
    return message


def _is_subject(rule: str, message: dict, role: str | None) -> bool | None:
    """Whether the company is the message's subject: True/False, or None when it can't be
    told - the company appears nowhere, or the rule depends on who published and the
    publisher has no guid (a creditor's intent can't be proven not to be the company's own;
    a debtor's intent/liquidation naming the company can't be proven to be). None raises no
    signal and is counted in the result's note."""
    if role is None:
        return None
    if rule == _ROLE_ANY:
        return True
    publisher = message.get("publisher") or {}
    if rule == _ROLE_PARTICIPANT_NOT_PUBLISHER:
        if role != "participant":
            return False
        return True if publisher.get("guid") else None
    if rule == _ROLE_PUBLISHER and role == "participant" and not publisher.get("guid"):
        # The company is named, but who published is unknown - it may well be the company.
        return None
    return role == rule


def parse_publications(
    publications: dict, company_guid: str, *, today: datetime.date | None = None
) -> dict:
    """Pure function: `{pageData, found}` publications payload -> `{messages, signals,
    total, truncated, note}`. Raises `FedresursError` on schema drift."""
    today = today or datetime.datetime.now(datetime.UTC).date()
    page = require_list_field(
        publications, "pageData", error=FedresursError, label=SOURCE_LABEL, where="публикациях"
    )
    total = publications.get("found")
    if not isinstance(total, int) or isinstance(total, bool) or total < len(page):
        raise FedresursError(f"{SOURCE_LABEL}: схема ответа изменилась — found публикаций не число")
    truncated = total > len(page)

    messages: list[dict] = []
    signals: list[dict] = []
    unclear_role = 0
    for raw_message in page:
        message = _validate_message(raw_message)
        # ЕФРСБ proceeding messages (other publicationType) are covered by the search
        # row's own `status`; annulled messages don't count.
        if message["publicationType"] != "SfactMessage" or message["isAnnulled"]:
            continue

        date_publish = message["datePublish"][:10]
        role = _role_of(message, company_guid)
        entry = {
            "date": date_publish,
            "type": message["type"],
            "number": message.get("number"),
            "role": role,
            "signal": None,
            "url": f"{FEDRESURS_BASE_URL}/sfactmessages/{message['guid']}",
        }
        rule = _MESSAGE_RULES.get(message["type"])
        if rule:
            code, role_rule = rule
            subject = _is_subject(role_rule, message, role)
            if subject is None:
                unclear_role += 1
            elif subject:
                try:
                    age_days = (today - datetime.date.fromisoformat(date_publish)).days
                except ValueError as exc:
                    raise FedresursError(
                        f"{SOURCE_LABEL}: схема ответа изменилась — datePublish не календарная дата"
                    ) from exc
                if age_days < 0:
                    raise FedresursError(
                        f"{SOURCE_LABEL}: схема ответа изменилась — datePublish из будущего"
                    )
                window = _FRESHNESS_DAYS.get(code)
                if window is None or age_days <= window:
                    entry["signal"] = code
                    signals.append(
                        {
                            "code": code,
                            "date": date_publish,
                            "type": message["type"],
                            "number": message.get("number"),
                            "url": entry["url"],
                        }
                    )
        messages.append(entry)

    notes: list[str] = []
    if truncated:
        notes.append(
            f"Показана первая страница публикаций ({len(page)} из {total}): найденное верно, "
            "отсутствие сообщений не проверено"
        )
    if unclear_role:
        notes.append(
            f"У {unclear_role} сообщ. не удалось определить роль компании — сигнал по ним не поднят"
        )
    return {
        "messages": messages,
        "signals": signals,
        "total": total,
        "truncated": truncated,
        "note": "; ".join(notes) or None,
    }


def is_fully_checked(result: dict, *, is_individual: bool) -> bool:
    """Whether the scan may count Федресурс as checked: the status lookup ran, and - for a
    legal entity that is in the register - its publications were read too. Without them the
    bankruptcy-intent/liquidation signals were never looked at, so a clean-looking verdict
    must not rest on this source. (ИП publications aren't requested by design; a truncated
    feed is a visible note, not a failure - what was read is valid.)"""
    if not result.get("checked"):
        return False
    return is_individual or not result.get("found") or bool(result.get("publications_checked"))


def _empty_result() -> dict:
    return {
        "checked": False,
        "found": False,
        "status_text": None,
        "is_active_bankruptcy": False,
        "status_recognized": True,
        "profile_url": None,
        "publications_checked": False,
        "publications_total": None,
        "publications_truncated": False,
        "publications_note": None,
        "messages": [],
        "signals": [],
    }


async def _fetch_publications(client: httpx.AsyncClient, guid: str) -> dict:
    return await _get_json(
        client,
        f"/backend/companies/{guid}/publications",
        {"limit": PUBLICATIONS_LIMIT, "offset": 0},
        f"{FEDRESURS_BASE_URL}/companies/{guid}",
    )


async def fetch_fedresurs_status(inn: str, *, is_individual: bool) -> tuple[dict, str]:
    """Look up `inn`'s bankruptcy status and message signals, and return `(result,
    raw_payload)`. A resolved entity simply not being in the bankruptcy register (`found:
    False`) is the expected, common case here, not a failure - but an *unreadable* answer
    (schema drift, a truncated result page without the exact ИНН) is a `FedresursError`,
    never a silent "not found". The publications step is best-effort: if it fails, the
    status result is kept and `publications_checked` stays False with the reason."""
    if not inn:
        return _empty_result(), ""

    path = "/backend/persons" if is_individual else "/backend/companies"
    params: dict[str, str | int] = {"limit": RESULTS_LIMIT, "offset": 0, "searchString": inn}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
        data = await _get_json(client, path, params, f"{FEDRESURS_BASE_URL}/")
        match = pick_search_row(data, inn)

        result = _empty_result()
        result["checked"] = True
        raw: dict = {"search": data, "publications": None}
        if match is None:
            return result, json.dumps(raw, ensure_ascii=False, indent=2)

        kind = classify_status(match["status"])
        result.update(
            found=True,
            status_text=match["status"],
            is_active_bankruptcy=kind == "active_bankruptcy",
            status_recognized=kind != "unrecognized",
            profile_url=_profile_url(match["guid"], is_individual=is_individual),
        )

        if is_individual:
            result["publications_note"] = (
                "Сообщения Федресурса для ИП не запрашиваются (поиск физлиц закрыт для "
                "автоматической проверки)"
            )
        else:
            try:
                publications = await _fetch_publications(client, match["guid"])
                raw["publications"] = publications
                parsed = parse_publications(publications, match["guid"])
                result.update(
                    publications_checked=True,
                    publications_total=parsed["total"],
                    publications_truncated=parsed["truncated"],
                    publications_note=parsed["note"],
                    messages=parsed["messages"],
                    signals=parsed["signals"],
                )
            except FedresursError as exc:
                logger.warning("fedresurs publications step failed for %r: %s", inn, exc)
                result["publications_note"] = f"Сообщения Федресурса не проверены: {exc}"

    return result, json.dumps(raw, ensure_ascii=False, indent=2)
