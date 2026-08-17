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
