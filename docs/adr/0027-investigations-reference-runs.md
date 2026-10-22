# An investigation is a saved, named list of references to existing runs

The analyst could export one run of one feature at a time, and nothing tied together the runs of
one inquiry (an IOC lookup, a username scan, an email search on related values). The cross-feature
report and the entity graph both need a set of runs to work on. Every feature already persists
its own runs, keyed by an id that is unique within that feature's table.

## Decision

- `Investigation` (name, notes, `TimestampMixin`) owns `InvestigationItem` rows, each a
  `(feature, run_id)` pair with an optional note, unique per investigation. Results are not
  copied; the item points at the row the feature's history already stores.
- `run_id` is deliberately not a foreign key, since it points into a different table per feature.
  An item whose run was deleted from feature history stays as a tombstone: the UI and the report
  say "run deleted" and keep the item's note. The item stores a `target` snapshot (the username,
  IOC, ...) taken when it was added, so a tombstone still says what it was about.
- A feature can be added once it has a `RunSource` in `app/utils/run_source_registry.py`: how to
  load a run, its target, its report sections and its entity extractor. v1 covers `ioc_lookup`,
  `username_search`, `email_search` and `reddit_search`; every other feature with a history is in
  `RUN_SOURCE_EXEMPT` with a reason, and a gate test fails on a feature in neither.
- The investigation report (`GET /api/investigations/{id}/report`) is one HTML/PDF through
  `core/reports`: a cover, items per feature, each item's own sections, then the most connected
  entities from the graph (`docs/adr/0028-entity-graph-derived-per-investigation.md`).
- Report labels are English; `ioc_lookup` sections follow `locale` like its single export does.

A persisted object is what lets an inquiry span several days and carry the analyst's notes;
pointing at runs instead of copying them keeps one source of truth and no second copy to migrate.

## Accepting

- A deleted run's results are gone from the report; only its target snapshot and note remain.
- A feature without a `RunSource` can't be added until someone writes its renderer and extractor.
- Domain finder has no persisted runs, so it can't be part of an investigation.

## Rejected

- **Select rows in Activity and export, no new table** - cheapest, but no notes, nothing to come
  back to, and no stable scope for the graph.
- **Cascade-deleting the item with its run** - simpler, but silently loses the analyst's note.
- **A real foreign key per feature (one nullable column per table)** - every new feature would
  need a migration on the investigations table.
- **Copying results into the investigation** - a second copy of every result shape to keep in
  step with each feature's schema.
