# `backend/app/features/ioc_tools/`

Deep-dive referenced from AGENTS.md's Backend architecture section.

## `ioc_lookup`

Single + bulk lookups against AbuseIPDB, AlienVault, VirusTotal, Shodan, etc.

- Single-lookup searches auto-save to history once every queried service responds:
  `POST/GET/DELETE /api/ioc-lookup/history`, persisted as `SingleLookupSearch`/`SingleLookupResult`.
- `GET /api/ioc/newsfeed-mentions` cross-references a looked-up IOC against `newsfeed`'s
  already-extracted article IOCs. `newsfeed_crud.get_articles_mentioning_ioc` matches by raw
  value via a case-insensitive JSON-text `LIKE` against `NewsArticle.iocs` rather than by type,
  since the two features' IOC-type vocabularies don't line up.
- A `blacklist` provider (EVM/Bitcoin addresses only) resolves instantly from a local table
  refreshed daily from three free, keyless feeds — OFAC SDN digital-currency addresses,
  ScamSniffer's phishing-address list, and OpenSanctions' `il_mod_crypto` Israel
  counter-terror-financing export — rather than a per-lookup external call. See
  `blacklist_refresh_service.py`.

## `ioc_extractor`, `ioc_defanger`

Straightforward, no notable internals beyond what their names describe.

## `domain_finder`

URLScan.io-based typosquat/phishing domain discovery, `/api/domain/lookup`.

Sibling panels on the same page, all keyless:
- WHOIS/RDAP via `rdap.org`'s bootstrap redirector.
- DNS records via dnspython, plus reverse-DNS for resolved IPs.
- Certificate Transparency subdomain enumeration via crt.sh's public JSON mirror.

A fourth panel, DNSDumpster (`/api/domain/dnsdumpster`), enriches with ASN/geo/PTR/HTTP(S)
banner data per host but needs its own free-tier API key from `dnsdumpster.com`, configured
under Settings → API Keys like any other provider. Capped at 50 records/lookup; no domain-map
image or pagination (those are DNSDumpster's paid-tier features, not integrated here).

Further panels have been added since (HackerTarget/RapidDNS/subfinder subdomain enumeration,
WebCheck's SSL/security-headers/DNSSEC/blocklist checks, Wayback Machine history, Temporal
Analysis) - `docs/specs/README.md` lists what's implemented and what was deliberately not integrated.

Backend: every third-party provider panel (crt.sh, RapidDNS, HackerTarget, Wayback, URLScan,
DNSDumpster) calls its provider through `service/provider_http.py`'s `provider_get(Provider,
path, parse=..., check=...)`, which owns the client, headers, timeout and the one error mapping
(`<CODE>_TIMEOUT`/`_CONNECTION_ERROR`/`_API_ERROR`/`_INVALID_RESPONSE`/`_UNEXPECTED_ERROR`); a
provider module keeps only its `parse` and provider-specific statuses. `provider_get` only
requests a `Provider`'s hardcoded `base_url`, which is why it's the single allowlisted raw
client in `test_ssrf_guard_coverage.py`; RDAP (redirect-followed through `safe_get`) reuses only
`provider_errors`.
Each panel's `POST /api/domain/<path>` + `GET /api/domain/<path>/{domain}` pair is mounted by
`routers/domain_routes.py`'s `_add_panel_routes` (request/response models, service, rate limit);
only Wayback and the site crawler, whose GET takes extra query parameters, are hand-written.
The factory renames each endpoint before `limiter.limit` wraps it - slowapi keys rate-limit
counters by function name, so closures would otherwise share one counter (pinned by a test).

Frontend: every panel's request lifecycle is one hook, `hooks/useDomainPanel.ts`
(`useDomainPanel(path, domain, {auto, params, notConfiguredCode})` → `GET
/api/domain/<path>/<domain>`, wildcard patterns reported as `unsupported`, stale responses
dropped, `auto: false` + `run()` for the click-triggered panels). An auto panel's
loading/error/empty rendering is `components/ui/panelStatusView.jsx`. A new panel is its
`*Panel.jsx` plus an entry in `DomainMonitoring.jsx` - no per-panel api/hook files.
subfinder and httpx are the two Go binaries in this list, both compiled from source (pinned
tags, not `@latest`) in one shared `go-tools-builder` Dockerfile stage and shelled out to via
`asyncio.create_subprocess_exec` (`subfinder_service.py`/`host_probe_service.py`; version/
availability read through the shared `core/utils/cli_tool_version.py` helper, same
"-version"-flag-parsing pattern for both). subfinder: no provider-config.yaml is shipped, so
only its keyless sources contribute results. httpx (Host Probe panel): detects which of
http/https is live for a domain plus title/tech/favicon-hash/TLS-cert - unlike every other
domain_finder check it never goes through `ssrf_guard.safe_get` (it's an external binary doing
its own DNS resolution), so it's gated by two independent layers instead: `resolve_validated_ip`
before the subprocess is spawned, and httpx's own `-exclude private-ips` flag (denies the same
private/loopback/link-local/cloud-metadata ranges on every connection it makes, including
redirects - catches what a one-time pre-check can't). Its compiled binary is installed as
`httpx-probe`, not `httpx`: the Python `httpx` package (already a dependency) registers its own
`httpx` console-script earlier on `PATH`, and installing the Go binary under the same name was
confirmed, by actually running it, to silently invoke the wrong tool. Both panels are
click-triggered rather than automatic, like the site crawler below (a run can take up to a
minute for subfinder, or make several outbound requests for httpx). The site crawler
(`/api/domain/site-crawl`, `site_crawler_service.py`) is the odd one out: unlike every other
panel here it isn't keyless-and-automatic - it makes many outbound requests per invocation (a
bounded same-host BFS over `<a href>`/`<script src>`, default 15 pages/depth 2, hard-capped at
30/3), so the frontend only runs it on an explicit "Start crawl" click, not on every domain
search. Each fetched page is run through `ioc_extractor`'s regex engine and the results
aggregated into one `ExtractionResponse` - it's a thin orchestration layer over that extractor
and `ssrf_guard.safe_get`, not a new IOC-detection engine of its own.
