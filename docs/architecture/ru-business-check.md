# `backend/app/features/ru_business_check/`

Deep-dive referenced from AGENTS.md's Backend architecture section.

Russian-market due-diligence check by ИНН/company name. Orchestrated by
`service/ru_business_check_service.py` (ЕГРЮЛ → РДЛ → арбитраж → Федресурс → Прозрачный бизнес →
ФедСФМ → РНП → `flag_engine.py`) via the shared SSE-scan pattern (`POST /api/ru-business-check/scan`,
see `docs/architecture/scan-lifecycle.md`).

## Sources

**ЕГРЮЛ/ЕГРИП** — extract scraped from `egrul.nalog.ru` (`egrul_service.py`): token-based search,
then PDF-extract download/parse via `pdfplumber`, since director/founders/ОКВЭД/capital only exist
in the official PDF, not the quick JSON summary.

**РДЛ (disqualified persons)** — `disqualified_persons_service.py`, scraping
`service.nalog.ru/disqualified.do`. Always a soft "requires manual review" flag, never automatic:
the registry gives no disambiguating identifier beyond full name, so a same-name false positive
would be a real defamation-shaped risk.

**Арбитраж** — case history from `kad.arbitr.ru` (`arbitration_service.py`) by the resolved ИНН,
soft-only.

**Федресурс** — active-bankruptcy check against `fedresurs.ru`'s own search backend
(`fedresurs_service.py`, keyless, hard flag when found). Movable-property pledges live on a
separate registry (`reestr-zalogov.ru`, Federal Notary Chamber) and remain unbuilt. ФССП
(`fssp.gov.ru`) isn't automated — its official API is dead and its search demands a CAPTCHA on
every query — the UI offers a manual-check deep link instead.

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

`fedsfm.ru` and `zakupki.gov.ru` both scope `verify=False` to themselves for the same
Russian-root-CA TLS gap rather than trusting it container-wide — see
`docs/adr/0007-fedsfm-tls-verify-scoped-bypass.md`.

## Sources considered and not built

`bo.nalog.gov.ru` (ГИР БО, financial statements) remains open, blocked on a live browser network
capture of its `UnifiedClient`-gated search, not otherwise reachable from this environment.
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
`fedresurs_raw`/`pb_nalog_raw`/`fedsfm_raw`/`rnp_raw`) for independent re-verification.

Flag thresholds (fresh-registration age, claim-amount/count) and history TTL are settings-backed
(`core/settings/ru_business_check/`), TTL enforced by a daily sweep
(`ru_business_check_retention_service.py`); repeat lookups for the same query within 24h serve
the cached row instead of re-hitting sources, unless `force_refresh`.

CAPTCHA/rate-limiting from any source is a clean scan failure, never something automated around
— see `docs/adr/0006-ru-business-check-scraping-over-paid-api.md` for the scraping-vs-paid-API
tradeoff and its fssp/pledges re-evaluation.

## i18n

UI/report text is Russian-only, hardcoded (no `core/i18n` namespace) — a deliberate exception,
since the source data is inherently Russian.
