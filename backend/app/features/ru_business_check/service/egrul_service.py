"""Scraper for egrul.nalog.ru - the official (keyless, no-API) ЕГРЮЛ/ЕГРИП registry
extract service.

Fixed host, only the query value (ИНН or company/IP name) is user-supplied - never the
host - so this intentionally does NOT go through app.core.security.ssrf_guard.safe_get
(see backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against live captures for both a legal entity (ООО) and an individual
entrepreneur (ИП, both an active and a terminated record) - 2026-08-13, via the running
backend container's own network access.** Confirmed: the search-row field names (`n`/
`i`/`o`/`r`/`rn`/`k`/`g` etc., see `_row_to_candidate` - `k` is `"ul"` for a legal entity,
`"fl"` for an individual, not `"ip"` as an earlier version of this docstring assumed);
the PDF-readiness check (poll `vyp-download` directly, not `vyp-request` - that endpoint
never changes its response regardless of readiness); and the выписка PDF's numbered-
table layout for both ЕГРЮЛ and ЕГРИП (see `parse_pdf_text` and the label constants
above it - ИП uses a materially different label set, documented inline).

Per project decision: a CAPTCHA challenge from egrul.nalog.ru is never solved or worked
around - it's surfaced as a clean, user-facing `EgrulCaptchaRequired` error.
"""

import asyncio
import io
import logging
import re
from datetime import datetime

import httpx
import pdfplumber

logger = logging.getLogger(__name__)

EGRUL_BASE_URL = "https://egrul.nalog.ru"
REQUEST_TIMEOUT_SECONDS = 20.0

SEARCH_POLL_INTERVAL_SECONDS = 1.5
SEARCH_POLL_MAX_ATTEMPTS = 8

PDF_POLL_INTERVAL_SECONDS = 2.0
PDF_POLL_MAX_ATTEMPTS = 20


class EgrulError(ValueError):
    """Bad input, no match, an ambiguous match, or egrul.nalog.ru itself failing/timing out"""


class EgrulCaptchaRequired(EgrulError):
    """egrul.nalog.ru is asking for a CAPTCHA solve - never bypassed, always a clean error"""


class EgrulAmbiguousMatch(EgrulError):
    """Multiple entities matched the query - not a dead-end failure, since a name search
    genuinely returning several hits is expected, not exceptional. Carries brief
    per-candidate info (see `_row_to_candidate`) so the caller can offer a disambiguation
    list instead of just erroring out."""

    def __init__(self, candidates: list[dict]):
        super().__init__(
            f"Найдено {len(candidates)} совпадений — уточните запрос "
            "(используйте ИНН вместо названия)"
        )
        self.candidates = candidates


async def _poll_json(
    client: httpx.AsyncClient, url: str, *, interval: float, max_attempts: int, ready
) -> dict:
    for _attempt in range(max_attempts):
        response = await client.get(url)
        response.raise_for_status()
        payload = response.json()
        if ready(payload):
            return payload
        await asyncio.sleep(interval)
    raise EgrulError(f"Тайм-аут ожидания ответа от egrul.nalog.ru ({url})")


async def _search(client: httpx.AsyncClient, query: str) -> dict:
    """POST the search form, then poll the token it returns until results are ready."""
    response = await client.post(
        f"{EGRUL_BASE_URL}/",
        data={
            "vyp3CaptchaToken": "",
            "query": query,
            "region": "",
            "PreventChromeAutocomplete": "",
        },
    )
    response.raise_for_status()
    payload = response.json()

    if payload.get("captchaRequired") or payload.get("captcha"):
        raise EgrulCaptchaRequired(
            "egrul.nalog.ru запросил капчу — автоматическая проверка недоступна, попробуйте позже"
        )
    token = payload.get("t")
    if not token:
        raise EgrulError(f"egrul.nalog.ru не вернул токен поиска: {payload}")

    return await _poll_json(
        client,
        f"{EGRUL_BASE_URL}/search-result/{token}",
        interval=SEARCH_POLL_INTERVAL_SECONDS,
        max_attempts=SEARCH_POLL_MAX_ATTEMPTS,
        ready=lambda p: p.get("rows") is not None,
    )


def _row_to_candidate(row: dict) -> dict:
    """Brief info for a disambiguation list, from a search-result row. Field names
    confirmed live: `n` full name, `i` ИНН, `o` ОГРН, `rn` region name (only a partial
    address - the full one only exists in the PDF, not worth fetching N PDFs just for a
    disambiguation list), `k` entity kind (`"ul"` legal entity, `"fl"` individual/ИП - not
    used here, `entity_type` is derived elsewhere from ОГРН length instead). No status
    field is present in a search row at all (only in the PDF, see `_STATUS_LABEL`) -
    `status` stays None here; `s`/`status`/`st` are kept as fallback guesses in case a
    future capture shows one after all."""

    def first(*keys):
        for key in keys:
            value = row.get(key)
            if value:
                return value
        return None

    return {
        "name": first("n", "nm", "name", "c", "caption"),
        "inn": first("i", "inn"),
        "ogrn": first("o", "ogrn"),
        "address": first("rn", "a", "ad", "addr", "address"),
        "status": first("s", "status", "st"),
    }


def _select_row(search_result: dict) -> dict:
    rows = search_result.get("rows") or []
    if not rows:
        raise EgrulError("Ничего не найдено в ЕГРЮЛ/ЕГРИП по этому запросу")
    if len(rows) > 1:
        raise EgrulAmbiguousMatch([_row_to_candidate(r) for r in rows])
    return rows[0]


async def _request_pdf(client: httpx.AsyncClient, row_token: str, search_token: str) -> bytes:
    """Ask egrul.nalog.ru to generate the official PDF extract for one matched row, then
    poll until it's ready and download it.

    `GET /vyp-request/<token>` only ever acknowledges the request (`{"t": ..., "captchaRequired":
    false}`, confirmed live) - it never reflects generation progress, so readiness has to
    be checked by polling `/vyp-download/<token>` itself and looking at what comes back:
    real PDF bytes (`%PDF` magic / `application/pdf` content-type) once ready, versus a
    small JSON/HTML placeholder while still generating. In the one live case tested, the
    PDF was ready on the very first `vyp-download` attempt - this loop is a safety net for
    slower-to-generate records, not the expected path.
    """
    kickoff = await client.get(
        f"{EGRUL_BASE_URL}/vyp-request/{row_token}", params={"key": search_token}
    )
    kickoff.raise_for_status()
    if kickoff.headers.get("content-type", "").startswith("application/json"):
        payload = kickoff.json()
        if payload.get("captchaRequired") or payload.get("captcha"):
            raise EgrulCaptchaRequired(
                "egrul.nalog.ru запросил капчу — автоматическая проверка недоступна, "
                "попробуйте позже"
            )

    for attempt in range(PDF_POLL_MAX_ATTEMPTS):
        download = await client.get(f"{EGRUL_BASE_URL}/vyp-download/{row_token}")
        # A non-2xx here (confirmed live: a plain 500) means "still generating," not a
        # real failure - egrul.nalog.ru gives no graceful "not ready yet" placeholder on
        # this endpoint, just an error status until the PDF exists. Only a real PDF
        # response ends the loop early; everything else retries until the attempt budget
        # is spent.
        if download.status_code == 200:
            content_type = download.headers.get("content-type", "")
            if content_type.startswith("application/pdf") or download.content[:4] == b"%PDF":
                return download.content
        if attempt < PDF_POLL_MAX_ATTEMPTS - 1:
            await asyncio.sleep(PDF_POLL_INTERVAL_SECONDS)

    raise EgrulError(f"Тайм-аут ожидания PDF-выписки от egrul.nalog.ru ({row_token})")


def _extract_pdf_text(pdf_bytes: bytes) -> str:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


# --- PDF text field extraction -------------------------------------------------------
# The official выписка renders as a numbered table ("№ | Наименование показателя |
# Значение показателя"), each row as "<row_number> <label> <value>" with the value
# wrapping onto following (unnumbered) lines for longer content - confirmed against a
# real ООО's PDF (see module docstring). Labels are stable, government-form field names,
# not something a company can customize, so exact-prefix matching on them is reliable -
# unlike the old colon-based "Метка: значение" guess this replaced, which never matched
# the real layout at all.

_PAGE_NOISE_RE = re.compile(
    r"^Выписка из ЕГРЮЛ$|^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2} ОГРН \S+ Страница \d+ из \d+$"
)
# A new row starts with its number followed by *horizontal* whitespace - not \s, which
# would also match a newline and let this bleed across into an unrelated following line
# (e.g. a standalone sub-item counter like "1" right before "86 Причина ...").
_ROW_START_RE = re.compile(r"^(\d+)[ \t]+(\S.*)$", re.MULTILINE)

_FULL_NAME_LABEL = "Полное наименование на русском языке"
_SHORT_NAME_LABEL = "Сокращенное наименование на русском языке"
_ADDRESS_LABEL = "Адрес юридического лица"
_OGRN_LABEL = "ОГРН"
_REG_DATE_LABEL = "Дата регистрации"
_INN_LABEL = "ИНН юридического лица"
_KPP_LABEL = "КПП юридического лица"
_CAPITAL_LABEL = "Размер (в рублях)"
_OKVED_LABEL = "Код и наименование вида деятельности"
_POSITION_LABEL = "Должность"
_SHARE_PERCENT_LABEL = "Размер доли (в процентах)"

# ЕГРИП (individual entrepreneur) uses a materially different label set from ЕГРЮЛ -
# confirmed live against both an active and a terminated ИП record. No separate
# "director" concept exists (the person *is* the business, so the generic Фамилия/Имя/
# Отчество block below - normally the director - naturally resolves to them instead);
# no legal-entity name, address, КПП, or capital fields exist at all for an ИП, so those
# stay None rather than being force-fit to something. `_STATUS_LABEL` is confirmed only
# for ИП (a "Состояние" section appears only once activity has stopped - an active
# record has no such section at all, so `registry_status` is None precisely when the
# absence itself means "active"); whether ЕГРЮЛ uses the same label for a liquidated
# company is an untested but reasonable guess given both share the same ФНС template
# family - if wrong, it just degrades to None like today, no worse than before.
_INN_PERSON_LABEL_FRAGMENT = "Идентификационный номер"
_STATUS_LABEL = "Состояние"

# ФИО is split across three sub-lines within one row's block ("Фамилия ... Имя ...
# Отчество ..."), not its own separate label+value pair. Matches on \s+ (not a literal
# newline) since `_extract_rows` below collapses each row's internal whitespace,
# including the original line breaks, to single spaces.
_NAME_BLOCK_RE = re.compile(
    r"Фамилия\s+(?P<last>.+?)\s+Имя\s+(?P<first>.+?)\s+Отчество\s+(?P<middle>.+)"
)

# How many rows past a "Фамилия" block to look for an associated field (Должность for
# the director, Размер доли for a founder) - generous enough to cover the handful of
# ГРН/date/Пол/Гражданство rows the template always interleaves in between.
_ASSOCIATED_FIELD_WINDOW = 10


def _extract_rows(text: str) -> dict[int, str]:
    """Split the выписка's numbered-table body into {row_number: text} - each spanning
    from that row's own label+value start to just before the next row starts (or end of
    document), with page header/footer noise stripped first so it can't leak into a
    wrapped value. Each row's internal whitespace (including the original line breaks a
    wrapped label or value spans) is collapsed to single spaces at this point, so every
    downstream lookup only ever has to match a single-line string - a label that itself
    wraps across two lines (e.g. ИП's "Идентификационный номер\nналогоплательщика (ИНН)")
    is exactly as matchable as one that doesn't."""
    clean_lines = [line for line in text.splitlines() if not _PAGE_NOISE_RE.match(line.strip())]
    clean_text = "\n".join(clean_lines)

    matches = list(_ROW_START_RE.finditer(clean_text))
    rows: dict[int, str] = {}
    for idx, m in enumerate(matches):
        row_num = int(m.group(1))
        start = m.start(2)
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(clean_text)
        rows[row_num] = re.sub(r"\s+", " ", clean_text[start:end]).strip()
    return rows


def _match_label(content: str, label: str) -> str | None:
    """`content` with `label` stripped, iff `label` is a whole-word prefix of it (followed
    by whitespace or nothing) - not just any prefix. Plain `str.startswith` would let
    "ОГРН" wrongly match the start of "ОГРНИП" (a *different* field, ИП's own registration
    number) and silently return "ИП 123..." as if it were the ОГРН value - confirmed live
    against a real ИП record."""
    if content == label:
        return None
    if content.startswith(label + " "):
        return content[len(label) :].strip() or None
    return None


def _row_value(rows: dict[int, str], label: str) -> str | None:
    """First row (in row-number order) whose content starts with `label`."""
    for row_num in sorted(rows):
        value = _match_label(rows[row_num], label)
        if value is not None:
            return value
    return None


def _all_row_values(rows: dict[int, str], label: str) -> list[tuple[int, str]]:
    result = []
    for row_num in sorted(rows):
        value = _match_label(rows[row_num], label)
        if value is not None:
            result.append((row_num, value))
    return result


def _full_name_from_block(block: str) -> str | None:
    m = _NAME_BLOCK_RE.search(block)
    if not m:
        return None
    parts = [m.group("last").strip(), m.group("first").strip(), m.group("middle").strip()]
    return " ".join(p for p in parts if p) or None


def _nearest_following(rows: dict[int, str], after_row: int, label: str) -> str | None:
    for row_num in sorted(n for n in rows if after_row < n <= after_row + _ASSOCIATED_FIELD_WINDOW):
        value = _match_label(rows[row_num], label)
        if value is not None:
            return value
    return None


def _extract_shape(rows: dict[int, str], label_fragment: str, pattern: re.Pattern) -> str | None:
    """First row containing `label_fragment` anywhere (not necessarily as a strict
    prefix), with `pattern` searched for within that row's content rather than trusting
    everything after the label to *be* the value - two real, unrelated layout quirks
    both need this: (1) a short value with no section header of its own gets the *next*
    row's section-header line folded into its span (confirmed live: "Дата регистрации
    05.08.2019 Сведения о регистрирующем органе..."), and (2) ИП's own ИНН label wraps
    *around* its value rather than before it ("Идентификационный номер 710506005859
    налогоплательщика (ИНН)") - a strict prefix match on the full label text can't work
    for that case at all, only a fragment-anywhere + shape search can."""
    for row_num in sorted(rows):
        if label_fragment in rows[row_num]:
            m = pattern.search(rows[row_num])
            if m:
                return m.group(0)
    return None


_DATE_SHAPE_RE = re.compile(r"\d{2}\.\d{2}\.\d{4}")
_OGRN_SHAPE_RE = re.compile(r"\d{13,15}")  # 13 digits (ОГРН) or 15 (ОГРНИП)
_PERSON_INN_SHAPE_RE = re.compile(r"\d{12}")  # a natural person's own ИНН is always 12 digits


def _parse_registration_date(rows: dict[int, str]) -> str | None:
    raw = _extract_shape(rows, _REG_DATE_LABEL, _DATE_SHAPE_RE)
    if not raw:
        return None
    try:
        return datetime.strptime(raw, "%d.%m.%Y").date().isoformat()
    except ValueError:
        logger.warning("Could not parse ЕГРЮЛ registration date %r", raw)
        return None


def _parse_director_and_founders(rows: dict[int, str]) -> tuple[str | None, str | None, list[dict]]:
    """Директор and учредители share the same "Фамилия/Имя/Отчество" block shape - the
    template's fixed section order (руководитель always before учредители) is what lets
    "first block = director, later blocks = founders" be a safe assumption rather than a
    guess. A founder that's itself a legal entity (not a person) has no such block at
    all - not handled here, falls out of `founders` silently rather than raising."""
    name_rows = sorted(n for n in rows if rows[n].startswith("Фамилия"))
    if not name_rows:
        return None, None, []

    director_name = _full_name_from_block(rows[name_rows[0]])
    director_position = _nearest_following(rows, name_rows[0], _POSITION_LABEL)

    founders = []
    for row_num in name_rows[1:]:
        founder_name = _full_name_from_block(rows[row_num])
        share = _nearest_following(rows, row_num, _SHARE_PERCENT_LABEL)
        founders.append({"name": founder_name, "share": f"{share}%" if share else None})

    return director_name, director_position, founders


def parse_pdf_text(text: str) -> dict:
    """Pure function: extract structured ЕГРЮЛ/ЕГРИП fields from the выписка's plain
    text. Kept separate from the network code above so it's independently unit-testable.
    """
    rows = _extract_rows(text)

    director_name, director_position, founders = _parse_director_and_founders(rows)

    okved_hits = _all_row_values(rows, _OKVED_LABEL)  # first hit is always the основной one

    full_name = _row_value(rows, _FULL_NAME_LABEL)
    if full_name is None and director_name:
        # ЕГРИП has no separate legal-entity name at all - the entrepreneur's own name
        # *is* the record's identity, confirmed live. director_name already resolves to
        # them (see _parse_director_and_founders's docstring), so reuse it here rather
        # than leaving full_name empty for every ИП query.
        full_name = f"ИП {director_name}"

    return {
        "full_name": full_name,
        "short_name": _row_value(rows, _SHORT_NAME_LABEL),
        # "ОГРН" is deliberately a substring match (via _extract_shape), not the strict
        # prefix _row_value uses elsewhere - it's a substring of ИП's own "ОГРНИП" label
        # too, so one fragment search covers both entity types' registration number.
        "ogrn": _extract_shape(rows, _OGRN_LABEL, _OGRN_SHAPE_RE),
        "inn": _row_value(rows, _INN_LABEL)
        or _extract_shape(rows, _INN_PERSON_LABEL_FRAGMENT, _PERSON_INN_SHAPE_RE),
        "kpp": _row_value(rows, _KPP_LABEL),
        "registration_date": _parse_registration_date(rows),
        "address": _row_value(rows, _ADDRESS_LABEL),
        "director_name": director_name,
        "director_position": director_position,
        "founders": founders,
        "okved_main": okved_hits[0][1] if okved_hits else None,
        "okved_additional": [value for _, value in okved_hits[1:]],
        "capital": _row_value(rows, _CAPITAL_LABEL),
        "registry_status": _row_value(rows, _STATUS_LABEL),
    }


async def fetch_egrul_extract(query: str) -> tuple[dict, str]:
    """Look up `query` (ИНН or name) in ЕГРЮЛ/ЕГРИП and return `(parsed_fields, raw_payload)`.

    `raw_payload` is the verbatim search-result JSON plus the extracted PDF text,
    concatenated - stored alongside the parsed fields so a past report can always be
    re-verified against what egrul.nalog.ru actually returned (see decision on raw-data
    retention in the Stage 1 plan).
    """
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS, follow_redirects=False) as client:
        search_result = await _search(client, query)
        row = _select_row(search_result)
        row_token = row.get("t")
        search_token = search_result.get("t") or ""
        if not row_token:
            raise EgrulError(f"Строка результата поиска не содержит токена: {row}")

        pdf_bytes = await _request_pdf(client, row_token, search_token)

    pdf_text = _extract_pdf_text(pdf_bytes)
    parsed = parse_pdf_text(pdf_text)

    import json

    raw_payload = (
        json.dumps(search_result, ensure_ascii=False, indent=2)
        + "\n\n--- PDF TEXT ---\n\n"
        + pdf_text
    )
    return parsed, raw_payload
