# One contract for third-party response shapes: "changed shape" is not "empty"

Three parallel error vocabularies grew up around external sources: `ServiceError` for
`ioc_lookup`, `Provider.error`/`provider_errors` for `domain_finder`, and per-source `*Error`
classes plus `source_contract.py` for `ru_business_check`. Only the last one guarded against a
source silently changing its response shape. Elsewhere a renamed field read as an *empty* result
(`.get(...) or []`): crt.sh returned `response.json()` unchecked, any Wayback answer shorter than
two rows meant "no captures", any HackerTarget line starting with `error` meant "no hosts", and
`ioc_lookup` handed raw provider JSON to the frontend, which rendered an empty card.

## Decision

A shared, language-neutral contract in `backend/app/core/external_sources/`:

- `contract.py`: `SourceDriftError(ValueError)` and `require_dict` / `require_list_field` /
  `require_fields` (an empty list or a present-but-null field is data; a missing key or wrong type
  is drift). Features with their own error class and message language pass `error=` / `messages=`;
  `ru_business_check/service/source_contract.py` is now a thin Russian-language adapter, so its
  messages and tests are unchanged.
- `outcome.py`: `SourceOutcome` (`OK`, `EMPTY`, `UNREACHABLE`, `BLOCKED`, `AUTH`, `DRIFT`) and
  `classify(exc)`, mapping each family's exceptions onto it. The live canaries
  (`tests/canary/policy.py`) skip on `UNREACHABLE`/`BLOCKED` and fail on everything else, so a
  runtime drift and a canary failure always agree.

Applied to:

- **domain_finder**: `provider_errors` maps `SourceDriftError` to `<CODE>_SCHEMA_DRIFT` (HTTP 502),
  distinct from `<CODE>_INVALID_RESPONSE` (body didn't parse). crt.sh, Wayback, HackerTarget,
  RapidDNS, RDAP and URLScan validate the shape their consumers read. Legitimately empty answers
  stay `[]`: crt.sh `[]`, Wayback `[]` or header-only (CDX answers `[]` for an unarchived target),
  HackerTarget's `error invalid host` (the one empty message verified live), RapidDNS's results
  table with an empty `<tbody>`. Gate: `tests/features/ioc_tools/test_domain_provider_contract.py`
  - every `Provider` has drifted/empty cases or a reasoned exemption.
- **ioc_lookup**: `ProviderSpec.expects` lists the top-level result fields the frontend reads;
  `ioc_lookup_engine` raises `ServiceDriftError` (a `ServiceError` with status 502 and a
  `SourceDriftError`) when one is missing and reports `LookupStatus.ERROR` with "`<name>` changed
  its response format (missing: ...)". The frontend already renders a provider error's message in
  the row summary and detail, so no UI change was needed. Providers that build their own result
  (CISA KEV, Library of Leaks, OpenPhish) validate the raw source inside the client instead.
  Gate: `tests/features/ioc_tools/test_provider_expects_gate.py` - every provider declares
  `expects` or has an exemption reason.

## Alternatives rejected

- **Keep three taxonomies.** Cheap, but drift stays invisible in two of them and the canaries need
  a regex per family to guess what an error means.
- **One shared HTTP client for every source.** Would unify errors by construction, but touches
  every fetch path (SSRF-guarded, pinned-IP, SSE, subprocess) for a problem that lives in
  response parsing. Rejected as too invasive.
- **Typed response models (pydantic) per source.** Stricter than needed: they would reject
  harmless extra or reshuffled fields the UI never reads. `expects` / `require_*` check only what
  is consumed.

## Migration status

Migrated: `ru_business_check` (all sources, via the adapter), `domain_finder` (crt.sh, Wayback,
HackerTarget, RapidDNS, RDAP, URLScan), `ioc_lookup` keyless providers (FFraud IP/email, FIRST
EPSS, URLScan.io via `expects`; CISA KEV, Library of Leaks, OpenPhish in-client).

Not migrated, with reason:

- `ioc_lookup` keyed providers - exempt until their canaries exist (`04-keyed-canaries`).
- Hudson Rock - its shape differs per IOC type (`stealers[]` vs `data{}`), so a flat `expects`
  cannot express it.
- DNSDumpster - keyed.
- `ioc_lookup` `blacklist` - local table, no external response.

Follow-ups (not started): Reddit archives (Arctic Shift / PullPush), Steam Web API, the YouTube
page-meta scrape, `domain_finder`'s other fetchers (SSL, headers, crawler), and the
username/email/phone scan sources.
