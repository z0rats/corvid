# ru_business_check: a verdict can be "incomplete", new sources are stored in `extra_data`, and some sources are local dumps

Three decisions made together, because each follows from the same review of the module against
a comparable open-source project (inn-check-ru), whose main lesson was that a scraper reading
an undocumented site with `.get(...) or []` turns every silent change of that site into a
false "checked, nothing found".

## 1. A verdict cannot look clean when a source that could rule out a hard flag didn't run

`flag_engine.evaluate` takes the list of sources that actually completed. If no hard flag was
found but a member of `REQUIRED_SOURCES` (Федресурс, РНП, ЕГРЮЛ - the ИНН-precise sources
that can raise a hard flag) is missing, the risk level is **`incomplete`**, not `low` or
`medium`. A hard flag still yields `high`: it is true regardless of what else failed. The
soft-only sources (arbitration, РДЛ, ФедСФМ, Прозрачный бизнес, ГИР БО, МСП, ЦБ) are not
required - their failure shows in `pending_sources` but doesn't invalidate a verdict that
only ever moves on hard flags.

Alternative considered: keep returning `low` and leave the caveat to callers via
`pending_sources` (the previous behaviour, documented in `flag_engine`'s module docstring).
Rejected: a UI or export that forgets the caveat presents a false all-clear, and "callers are
responsible" is exactly the kind of convention nothing enforces. `evaluate`'s
`checked_sources` argument defaults to `None` ("caller asserts all required sources ran") only
so single-source unit tests stay short; the scan (`_scan`) always passes the real list and a test
pins that a failed required source never yields `low`.

Федресурс counts as checked only when its publications were read too (for a legal entity in
the register): the status alone can't rule out a creditor's/debtor's bankruptcy intent or a
liquidation decision. A truncated publications feed is shown as a note, not a failure - what
was read is valid, and requiring the full feed would make every large company `incomplete`.
An `incomplete` scan is never served from the 24h cache, so a transient outage doesn't stick.

Locally cached dumps (below) can raise a hard flag but aren't required either: they are
populated in the background after first start, so making them required would make every
verdict `incomplete` until the first download finished. They show as pending instead.

Every source parser also validates the shape it depends on (`service/source_contract.py`) and
raises its own error class on drift, so a changed site becomes "not checked" instead of an
empty result. `tests/features/ru_business_check/test_source_contract.py` fails until each new
`AVAILABLE_SOURCES` entry has a drift case; `tests/canary/` (weekly workflow) checks the real
sites' shapes, skipping what the CI runner's network can't reach.

## 2. The "3 soft flags -> high" escalation counts sources, not flags

Each source contributes at most once. New sources emit several related soft flags (Федресурс
signals, three ГИР БО ratios); counted per flag, one source could reach `high` alone. The
previous rule already let arbitration reach 2 flags on its own - this changes that too.

## 3. Sources added from now on live in `extra_data` / `extra_raw` (JSON, keyed by source id)

The original sources each cost two columns on `ru_business_check_searches` plus a migration.
With more than a handful of new sources coming, `extra_data` (parsed result) and `extra_raw`
(verbatim payload) hold them by key: ГИР БО, МСП, the local-dump lookups. Existing sources keep
their columns (moving them is churn without a benefit). `raw_sha256` records each payload's
SHA-256 at capture time, so a stored payload - or an export of it - can be checked later.

Trade-off: JSON keys aren't queryable/indexed the way columns are. Nothing queries by these
today; if a source ever needs that, it gets a real column then.

## 4. Registry dumps are downloaded and matched locally

`disqualified_dump_service` (ФНС open data), `cbr_warning_service` (Банк России warning
list) and `ofac_sdn_service` (US Treasury SDN) download the full published list on a schedule,
keep the matchable part in a table, replace it in one transaction, refuse a list that looks
truncated or has lost the field that makes it matchable (a list without ИНН would make every
lookup a false "no match"), and match by exact ИНН (РДЛ: ФИО + ИНН of the organization).
Reasons: the checked ИНН isn't sent to a third party; the checks work when the site is down
or slow; and the dumps carry identifiers the online search lacks (the ФНС register's
organization ИНН turns "same ФИО" into "same person for this company", the only case the
disqualification flag is hard).

Personal data: the ФНС dump's birth date/place, judge and raw CSV are not stored. Sanctions and
regulator lists are worded as statements of those lists, and each panel says what a *miss*
does not mean (OFAC records carry an ИНН for only part of their Russian entries - a large
bank is listed without one).

A refresh runs under a per-source lock that also covers the commit
(`registry_dump_common.refresh_lock`, taken in `registry_dump_scheduler_service.run_refresh`):
two overlapping "delete all + insert" transactions would duplicate rows or collide on the
provenance row; a refresh that finds one already running is skipped. Staleness follows the scheduler convention in `AGENTS.md`: the recurring job's countdown is
in memory, so `refresh_dumps_if_stale` re-derives it from the DB at every startup.
