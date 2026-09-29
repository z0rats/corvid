# `backend/app/features/ru_business_check/`

Deep-dive referenced from AGENTS.md's Backend architecture section.

Russian-market due-diligence check by ИНН/company name. Orchestrated by
`service/ru_business_check_service.py` (ЕГРЮЛ → РДЛ → арбитраж → Федресурс → Прозрачный бизнес →
ФедСФМ → РНП → the `extra_data` sources → `flag_engine.py`) via the shared SSE-scan pattern
(`POST /api/ru-business-check/scan`, see `docs/architecture/scan-lifecycle.md`). Decisions behind
the verdict semantics, `extra_data` and the local dumps: `docs/adr/0014-*.md`.

## Result semantics (read before adding a source)

- **A failed source is "not checked", never "empty".** Every client validates the shape it relies
  on (`service/source_contract.py`) and raises its own error class on drift; `run_scan_task`
  then leaves the source out of `checked_sources`. `tests/.../test_source_contract.py` fails until a
  new `AVAILABLE_SOURCES` entry has a drift case.
- **`risk_level` can be `incomplete`**: no hard flag, but a `REQUIRED_SOURCES` member (ЕГРЮЛ,
  Федресурс, РНП) didn't run. `high` (a hard flag) is unaffected. Федресурс counts only if its
  publications were read as well (`fedresurs_service.is_fully_checked`). `SearchDetail`'s
  computed `missing_required_sources` names what's missing (the UI and export list it); an
  `incomplete` scan is never served from the 24h cache.
- **Thresholds/results**: `flag_engine.evaluate(SourceResults, Thresholds, checked_sources)`;
  `Thresholds` field names are the settings columns (`Thresholds.from_settings`).
- **"3+ soft flags → high" counts sources**, each at most once.
- **`extra_data`/`extra_raw`** (JSON keyed by source id) hold ГИР БО, МСП and the dump lookups;
  register a remote fetcher in `ru_business_check_service._extra_sources()`, a local-dump lookup
  in `_local_lookups()`. Every source call goes through `_attempt` (failure -> default + not
  checked). `raw_sha256` fingerprints
  each captured payload at scan time.
- **Canaries**: `tests/canary/` (`pytest -m canary -o addopts=`, weekly `.github/workflows/canary.yml`)
  calls the real sites; only "didn't answer us" (network, anti-bot, captcha, 401/403/429/451/5xx)
  skips - drift, a JSON endpoint answering HTML, and unexpected empty answers fail
  (`tests/canary/policy.py`, pinned in `test_source_contract.py`). `kad.arbitr.ru` answers 451 to non-RU networks, so it is normally
  skipped.

## Sources

**ЕГРЮЛ/ЕГРИП** — extract scraped from `egrul.nalog.ru` (`egrul_service.py`): token-based search,
then PDF-extract download/parse via `pdfplumber`, since director/founders/ОКВЭД/capital only exist
in the official PDF, not the quick JSON summary.

**РДЛ (disqualified persons)** — `disqualified_persons_service.py`, `service.nalog.ru/disqualified.do`
whose form posts to `disqualified-proc.json`, answering JSON (`{"data": [...], "rowCount"}`; the
parser once read only an HTML table, which read every lookup as "no match"). Online it's always a
soft "requires manual review" flag: search is by ФИО only and the ЕГРЮЛ extract carries no birth
date, so a same-name false positive would be a real defamation-shaped risk; the registry's birth
date is shown to help the analyst.

**Арбитраж** — case history from `kad.arbitr.ru` (`arbitration_service.py`) by the resolved ИНН,
soft-only.

**Федресурс** — `fedresurs_service.py`, keyless. The search row's `status` gives the bankruptcy
verdict (active stage → hard flag; only "Действующее" is a known-clean value; anything else is a
soft "unrecognized status" flag; a truncated result page without the exact ИНН is an error, not
"not found"). For legal entities the first 15 publications
(`/backend/companies/<guid>/publications`) yield soft signals — creditor's/debtor's bankruptcy
intent, liquidation decision, "недостоверность сведений", reorganization (last 365 days) — by
per-type **role rules**: a message's `participants` includes its own publisher, so ПАО СБЕРБАНК
appears in hundreds of "creditor intent" messages about *other* companies, and only the debtor
side counts. A found-count above the page is surfaced as truncation, not as absence. Movable-property
pledges live on a separate registry (`reestr-zalogov.ru`, Federal Notary Chamber) and remain
unbuilt. ФССП (`fssp.gov.ru`) isn't automated — its official API is dead and its search demands a
CAPTCHA on every query — the UI offers a manual-check deep link instead.

**Прозрачный бизнес** — `pb.nalog.ru` (`pb_nalog_service.py`), a two-step async
search-then-detail flow surfacing one soft flag, `mass_registration_address` (other entities
sharing the same registered address, settings-backed threshold). A second candidate flag based on
the response's `is_p_ruk` field was investigated and dropped: manual re-verification against
pb.nalog.ru's own UI found nothing corresponding to it — don't re-attempt without new evidence
the field means something else.

**ФедСФМ** — `fedsfm.ru` (Росфинмониторинг terrorism/WMD-financing list, `fedsfm_service.py`),
same soft-only, name-only-match policy as РДЛ, checked against the resolved director's name.

**РНП** — `zakupki.gov.ru`'s Реестр недобросовестных поставщиков (`zakupki_rnp_service.py`).
Unlike РДЛ/ФедСФМ this *is* a hard flag (`rnp_confirmed`), since ИНН is a precise identifier with
no name-collision ambiguity. Parses the site's own RSS feed
(`/epz/dishonestsupplier/search/rss`) rather than scraping HTML, gated behind a session cookie
(minted by a plain GET) plus a browser User-Agent header (neither is a CAPTCHA).

**ГИР БО** — `gir_bo_service.py` (`bo.nalog.gov.ru`, keyless; the library-default `python-httpx` UA is
refused, so an identifying one is sent). Search (`inn` comes back HTML-wrapped in `<strong>`) →
`/nbo/organizations/<id>/bfo/` → `/nbo/bfo/<id>/details` for the 3 newest periods; amounts are
thousand rubles as reported. Banks, insurers, ИП and non-publishers are simply absent (a normal,
explained result). Three soft flags, thresholds in settings: equity ratio (1300/1600), current
ratio (1200/1500), year-over-year revenue drop.

**МСП** — `msp_service.py` (`rmsp.nalog.ru`): a fact panel (category, in-register status), no flag.

**Local registry dumps** (`disqualified_dump_service.py`, `cbr_warning_service.py`,
`ofac_sdn_service.py`, shared plumbing in `registry_dump_common.py`) — full lists downloaded on a
schedule (`registry_dump_scheduler_service.py`; startup catch-up re-derives staleness from the DB),
matched by exact ИНН locally. Shared download/replace/freshness plumbing and the per-source
refresh lock (held through the commit, enforced by `replace_dump`; a concurrent refresh is
skipped) live in `registry_dump_common.py`. The ФНС dump's flags count as their own source in
the soft-flag escalation, separately from the online РДЛ search:
- **ФНС disqualified dump** (`data.nalog.ru`, weekly): ФИО **and** the record's organization ИНН
  (present on ~36% of rows) matching this company, in force today → the hard
  `disqualified_confirmed` (replaces the online name-only soft flag); other in-force records with the
  company's ИНН, in force or expired → soft `company_disqualified_officer` with the records' dates. Birth date/place, judge, CSV aren't stored.
- **ЦБ warning list** (`cbr.ru`, every 2 days; ~11% of entries carry an ИНН): soft
  `cbr_warning_list`, worded as the regulator's statement; "clone" entries (the ИНН owner is the
  impersonated party) are shown but never flagged; for an ИП not looked up and listed as neither
  checked nor pending (the list has no 12-digit ИНН), the panel/report say why.
- **OFAC SDN** (`treasury.gov` → `sanctionslistservice…` → signed storage URL, every redirect hop
  checked; every 2 days): hard `ofac_sdn_listed` on an exact ИНН match against the entries'
  `Tax ID No. … (Russia)` remarks (3.7k entries). **A miss proves nothing** — ПАО Сбербанк is on the
  list without an ИНН in its record; the panel/report say so. EU list isn't included (checked 2026-09-28: the CSV export is 25 MB and answers 403
  without a token; none of its 43 891 rows carries a 10/12-digit identification number, so it could
  only be matched by name).
A dump that hasn't been downloaded yet is "not checked" (pending), and a refresh that looks truncated
or has lost its identifying field is refused, keeping the old data.

`fedsfm.ru` and `zakupki.gov.ru` both scope `verify=False` to themselves for the same
Russian-root-CA TLS gap rather than trusting it container-wide — see
`docs/adr/0007-fedsfm-tls-verify-scoped-bypass.md`.

## Sources considered and not built

ФедСФМ by *company name*: the list's organization entries are "объединение, членами которого
являются: …" member lists, not official names, so a name search is noise (director-by-ФИО stays).
Ruled out entirely: `rusprofile.ru` (redundant with `pb.nalog.ru`'s own signal),
`opensanctions.org` (CC BY-NC licensing risk), ГАС «Правосудие» (no viable API).

A dedicated in-app "Источники" tab (`components/Sources.jsx`) lists every source considered,
automated or not, each linked to the real site with its status.

## Website / domain

`ScanRequest.website` (optional) is stored as-is and displayed with a link into `domain_finder`'s
own richer WHOIS/DNS/CT analysis (see `docs/architecture/ioc-tools.md`) — this feature doesn't
fetch or analyze the domain itself, no `AVAILABLE_SOURCES` key of its own.

## "Check it yourself" links

РДЛ/ФедСФМ/РНП results each carry a link to the real source: РНП's reproduces the exact search
query (its search reads the URL directly, confirmed live); РДЛ/ФедСФМ can only link to the real
search page itself (both POST/JS-driven, confirmed live to not read any URL param), with the
searched name spelled out for manual re-entry.

## Export

A completed scan can be exported as an HTML/PDF report (`service/report_service.py`,
`GET .../history/{id}/report`) — see `docs/architecture/core-cross-cutting.md`'s `reports/`
section for the shared renderer and its per-source `href` support.

## Result tracking, caching, failure handling

Result rows track `checked_sources`/`pending_sources` (snapshotted at scan time) so a verdict
never implies more methodology coverage than what actually ran; each source's raw payload is
persisted alongside its parsed fields (`egrul_raw`/`disqualification_raw`/`arbitration_raw`/
`fedresurs_raw`/`pb_nalog_raw`/`fedsfm_raw`/`rnp_raw`, and `extra_raw[source]`) for independent
re-verification, with `raw_sha256[source]` recorded at capture time (shown in the raw panel and the
exported report).

Flag thresholds (fresh-registration age, claim-amount/count, ГИР БО ratios) and history TTL are settings-backed
(`core/settings/ru_business_check/`), TTL enforced by a daily sweep
(`ru_business_check_retention_service.py`); repeat lookups for the same query within 24h serve
the cached row instead of re-hitting sources, unless `force_refresh`.

CAPTCHA/rate-limiting from any source is a clean scan failure, never something automated around
— see `docs/adr/0006-ru-business-check-scraping-over-paid-api.md` for the scraping-vs-paid-API
tradeoff and its fssp/pledges re-evaluation.

## i18n

UI/report text is Russian-only, hardcoded (no `core/i18n` namespace) — a deliberate exception,
since the source data is inherently Russian.
