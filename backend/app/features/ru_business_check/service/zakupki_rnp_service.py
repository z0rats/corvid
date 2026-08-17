"""Client for zakupki.gov.ru's Реестр недобросовестных поставщиков (РНП) - the unified
registry (spanning 44-ФЗ, 223-ФЗ, and ПП РФ 615) of suppliers/contractors barred from
government procurement for a confirmed breach of contract.

Fixed host, only the ИНН is user-supplied - never the host - so this intentionally does
NOT go through app.core.security.ssrf_guard.safe_get (see
backend/tests/core/test_ssrf_guard_coverage.py's ALLOWLISTED_FIXED_HOST_FILES).

**Verified against live captures - 2026-08-13, via this environment's own network
access.** Two things gate every parameterized request (confirmed live, each in
isolation): a session cookie (`Set-Cookie: session-cookie=...`, minted by a plain GET
against the search page, no params needed) and a browser-shaped `User-Agent` header -
*any* query string sent without both returns a bare nginx 404 (not a 403/CAPTCHA - a
disguised block page). Neither is a CAPTCHA or a real anti-bot puzzle, so this isn't the
kind of thing `docs/adr/0006-*.md`'s never-bypass-CAPTCHA policy rules out - it's the same
category as `fedsfm_service.py`'s WAF-needs-a-User-Agent gate, just with a cookie added.

The site's own **RSS feed** (`/epz/dishonestsupplier/search/rss`) turned out to be a far
better integration target than the HTML results page originally planned: it returns the
exact same search results as clean, fully-labelled Russian key/value text inside each
`<item>`'s `<description>` (registry number, law, name, ИНН, dates, status, ЕРУЗ number) -
no table-scraping needed at all, just unescaping and a small regex over a fixed,
predictable `<strong>Label: </strong>Value<br/>` shape (`_parse_description`).

**Confirmed live request/response shape:**
```
GET https://zakupki.gov.ru/epz/dishonestsupplier/search/results.html   (seeds the cookie)
GET https://zakupki.gov.ru/epz/dishonestsupplier/search/rss
    ?searchString=<ИНН>&fz94=on&fz223=on&ppRf615=on&dsStatuses=0
    &sortBy=UPDATE_DATE&pageNumber=1&sortDirection=false&recordsPerPage=_10
-> <rss><channel><item><title>.../<link>.../<description>...</item>...</channel></rss>
```
`fz94`/`fz223`/`ppRf615` (which of the three underlying registries to search) are all
checked by default on the live page - confirmed via each checkbox's own `checked`
attribute - so all three are always sent. `dsStatuses=0` selects only "Размещено"
(currently active) entries - confirmed live via the page's own JS
(`dsStatuses_0`/`dsStatuses_1` map to hidden-field values `"0"`/`"1"`) - since an
"Исключено" (expired/removed) entry is no longer a current red flag, mirroring how
`fedresurs_service.py` only flags an *active* bankruptcy, not a resolved one.

`searchString` does its own fuzzy/substring matching server-side (confirmed live: an ИНН
search matched cleanly, but a name-fragment search returned many partial matches), so
`_pick_exact_matches` re-filters the parsed entries by an exact ИНН match before this
module ever hands anything back - same defensive pattern as
`fedresurs_service.py`'s `_pick_exact_match`.

Per project decision, unlike РДЛ/ФедСФМ's name-only matching, a РНП match *is* treated as
a confirmed hard flag (`flag_engine.py`'s `_zakupki_rnp_flags`) rather than
`requires_manual_review` - ИНН is a precise identifier here, with no name-collision
ambiguity to hedge against.

**TLS**: zakupki.gov.ru serves a certificate chained to the same Russian national root CA
as `fedsfm.ru` (confirmed live) - this client scopes `verify=False` to itself for the same
reason; see `docs/adr/0007-*.md` (the reasoning there isn't specific to fedsfm.ru).
"""

import html
import logging
import re

import httpx

logger = logging.getLogger(__name__)

ZAKUPKI_BASE_URL = "https://zakupki.gov.ru"
RNP_SEARCH_PAGE_URL = f"{ZAKUPKI_BASE_URL}/epz/dishonestsupplier/search/results.html"
RNP_RSS_URL = f"{ZAKUPKI_BASE_URL}/epz/dishonestsupplier/search/rss"
REQUEST_TIMEOUT_SECONDS = 20.0

# Fixed search parameters, all confirmed live against the site's own default form state -
# see module docstring. Only `searchString` varies per call.
_FIXED_PARAMS: dict[str, str] = {
    "fz94": "on",
    "fz223": "on",
    "ppRf615": "on",
    "dsStatuses": "0",  # Размещено (active) only
    "sortBy": "UPDATE_DATE",
    "pageNumber": "1",
    "sortDirection": "false",
    "recordsPerPage": "_10",  # plenty for a due-diligence check on one ИНН
}

# A browser-shaped User-Agent is required on the RSS request - confirmed live that a
# cookie alone isn't enough, the site's WAF 404s the request regardless without one too.
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

_LABEL_MAP = {
    "Реестровый номер": "registry_number",
    "Относится к": "law",
    "Наименование(ФИО) недобросовестного поставщика": "name",
    "ИНН (аналог ИНН)": "inn",
    "Включено": "included_date",
    "Обновлено": "updated_date",
    "Планируемая дата исключения": "planned_exclusion_date",
    "Статус записи": "status",
    "Номер реестровой записи ЕРУЗ": "eruz_number",
}

_DESCRIPTION_FIELD_RE = re.compile(r"<strong>([^<]+):\s*</strong>\s*([^<]*)<br\s*/?>")
_ITEM_RE = re.compile(r"<item>(.*?)</item>", re.DOTALL)
_LINK_RE = re.compile(r"<link>(.*?)</link>")
_DESCRIPTION_RE = re.compile(r"<description>(.*?)</description>", re.DOTALL)


class ZakupkiRnpError(ValueError):
    """The service itself failed/timed out"""


def _parse_description(description_html: str) -> dict[str, str]:
    """Pure function: extract the `{Русская метка: значение}` pairs out of one RSS
    item's `<description>` fragment (already XML-unescaped by the caller's XML parsing -
    see module docstring for the fixed shape), mapped to English field names via
    `_LABEL_MAP`. Kept separate from the network/XML code so it's independently
    unit-testable."""
    fields: dict[str, str] = {}
    for label, value in _DESCRIPTION_FIELD_RE.findall(description_html):
        key = _LABEL_MAP.get(label.strip())
        if key:
            fields[key] = value.strip()
    return fields


def parse_rss_entries(xml_text: str) -> list[dict]:
    """Pure function: extract РНП entries from the raw RSS response text. Deliberately
    regex-based rather than a full XML parser (`xml.etree.ElementTree`) - the feed embeds
    HTML markup inside `<description>` that a strict XML parser would happily unescape
    for us, but the surrounding `<item>`/`<link>` extraction is simple and fixed enough
    that a second dependency (or `ElementTree` plus a follow-up HTML unescape pass) isn't
    worth it for a well-known, narrow shape."""
    entries: list[dict] = []
    for item_xml in _ITEM_RE.findall(xml_text):
        link_match = _LINK_RE.search(item_xml)
        description_match = _DESCRIPTION_RE.search(item_xml)
        if not description_match:
            continue

        description_html = html.unescape(description_match.group(1))
        fields: dict[str, str | None] = dict(_parse_description(description_html))
        if not fields.get("inn"):
            continue

        detail_path = html.unescape(link_match.group(1)) if link_match else None
        fields["detail_url"] = f"{ZAKUPKI_BASE_URL}{detail_path}" if detail_path else None
        entries.append(fields)

    return entries


def _pick_exact_matches(entries: list[dict], inn: str) -> list[dict]:
    """Pure function: `searchString` does its own fuzzy/substring matching server-side
    (confirmed live), so entries must be re-filtered by an exact ИНН match rather than
    trusting every row the search returned - same defensive pattern as
    `fedresurs_service.py`'s `_pick_exact_match`."""
    return [e for e in entries if e.get("inn") == inn]


async def fetch_rnp_entries(inn: str) -> tuple[list[dict], str]:
    """Search the РНП for `inn` and return `(entries, raw_payload)`, where `entries` is a
    list of `{registry_number, law, name, inn, included_date, updated_date,
    planned_exclusion_date, status, eruz_number, detail_url}` (only active/"Размещено"
    entries - see module docstring) and `raw_payload` is the verbatim RSS response text.
    An empty `entries` list (the company simply isn't in the registry) is the expected,
    common case here, not a failure.
    """
    if not inn:
        return [], ""

    async with httpx.AsyncClient(
        timeout=REQUEST_TIMEOUT_SECONDS,
        follow_redirects=False,
        verify=False,
        headers={"User-Agent": _USER_AGENT},
    ) as client:
        try:
            seed = await client.get(RNP_SEARCH_PAGE_URL)
            seed.raise_for_status()
            response = await client.get(RNP_RSS_URL, params={**_FIXED_PARAMS, "searchString": inn})
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ZakupkiRnpError(
                f"zakupki.gov.ru вернул ошибку: HTTP {exc.response.status_code}"
            ) from exc
        except httpx.HTTPError as exc:
            raise ZakupkiRnpError(f"zakupki.gov.ru недоступен: {exc}") from exc

    entries = _pick_exact_matches(parse_rss_entries(response.text), inn)
    return entries, response.text
