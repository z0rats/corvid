# Sanctions Search uses OpenSanctions' cleaned CSV, its own table, and in-house name matching

Sanctions Search (free-text person/organization/vessel/aircraft name search against the OFAC SDN
list) was inspired by a third-party OSINT dashboard's equivalent module, reimplemented from
scratch in Python — no code was ported, since the runtime differs and the source was third-party
TypeScript of unclear license. Four decisions were made before writing any code.

## OpenSanctions' cleaned CSV over Treasury's raw SDN export

`ru_business_check`'s existing OFAC consumer (`ofac_sdn_service.py`) already parses Treasury's own
`sdn.csv` — but that's a legacy, header-less, 12-column format with one row per sanctions
*program* rather than per entity, no alias list (aliases are folded into free-text remarks), and no
clean country/schema fields. Re-deriving per-entity aliases/countries from that shape would mean
rebuilding normalization OpenSanctions already publishes. OpenSanctions' `us_ofac_sdn` dataset
(`targets.simple.csv`, CC-BY 4.0) is Treasury's same SDN list, re-published as one row per entity
with pre-split `aliases`/`countries`/`program_ids` columns — the right shape for a name/alias
search feature, at the cost of depending on a second-party republisher rather than Treasury
directly (mitigated by OpenSanctions being a widely-used, actively maintained open sanctions-data
project, and by `download_text`'s existing size cap and floor-check machinery still applying here).

## A separate table from `ru_business_check`'s OFAC consumer, not a shared one

`ofac_sdn_service.py` matches by **exact Russian ИНН** against a ~3.7k-entry subset of the list
(only entries whose remarks carry a `Tax ID No. ... (Russia)` marker) — a deliberate, narrower
design so a company can be matched exactly, by design, with the ИНН never leaving the process (see
that module's own docstring). Sanctions Search matches the **full list** (~20k entities, every
schema OpenSanctions carries: Person, Organization, Vessel, Airplane, Company, Security,
LegalEntity, CryptoWallet) by **free-text name/alias**. These are different match keys over
different subsets of the same underlying sanctions program, serving different call sites (one
signal inside `ru_business_check`'s larger due-diligence flag engine vs. a standalone lookup) —
collapsing them into one table would mean every future consumer of either inherits both filters.

## In-house substring/alias matching, and an in-memory index over a DB-side one

No fuzzy-matching dependency is used, per this project's general preference for implementing
small, non-cryptographic algorithms in-house rather than reaching for a library: normalization
(lowercase, strip accents/punctuation, collapse whitespace) plus ranked exact-name / exact-alias /
substring-name / substring-alias buckets is enough to make partial/aliased matches findable while
staying auditable — an analyst can see *why* a result matched, which an opaque fuzzy score would
not offer.

The search index itself is built in Python and cached in-process (`core/utils/ttl_cache.py`'s
`TtlCache`, invalidated event-drivenly right after each refresh commits) rather than pushed into a
database-side full-text mechanism such as SQLite's FTS5. A linear scan over ~20k short normalized
strings is sub-50ms, cheap enough that a second search mechanism isn't worth the added moving part
— and per [ADR 0004](0004-sqlite-only-postgres-unsupported.md), SQLite is only the actually
supported backend today, not an architectural guarantee; keeping the matching logic in Python
rather than a SQLite-only feature avoids a latent portability trap if that ever changes.

## The registry-dump plumbing was promoted to `core/`, not reused from `ru_business_check`

The only existing "periodic dump + provenance + staleness-driven refresh" machinery
(`registry_dump_common.py`, its `RegistryDump` provenance table, and the scheduler wrapper around
it) lived inside `ru_business_check`, written for its own three consumers. Reusing it as-is from an
unrelated feature would mean Sanctions Search depends on `ru_business_check`'s internals and stores
its provenance row in a table literally named `ru_business_check_registry_dumps` — a permanent,
visible misnomer once a second, unrelated feature writes rows there. This project already has a
precedent for promoting this shape of infrastructure to `core/` once a second consumer needs it
(`core/scans/run.py`'s `ScanRun`, shared lifecycle plumbing for every scan-style feature rather
than living inside whichever feature used it first), so the same move was made here: the plumbing
now lives at `app/core/registry_dumps/` and `app/core/models/registry_dump.py`, the table is
`registry_dumps`, and each of the now-four consumers (`ru_business_check`'s three dumps, plus this
one) keeps its own thin `dump_jobs()`/`register_*_scheduler()` wrapper naming its own jobs against
that shared engine, rather than reimplementing the no-overlap/lock-spans-commit/stale-on-restart
logic per feature.

As a related but explicitly deferred follow-up: CISA KEV and OpenPhish's caching
(`ioc_lookup/single_lookup/service/external_api_clients.py`) each hand-roll an identical
`dict + asyncio.Lock + time.monotonic()` TTL cache with no stale-on-error fallback — the same shape
`TtlCache` now formalizes. Migrating them onto `TtlCache` was left out of this change to keep it
scoped to Sanctions Search; it's a natural, low-risk future cleanup now that the shared helper
exists.
