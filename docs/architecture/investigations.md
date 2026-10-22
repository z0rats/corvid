# Investigations

Deep-dive referenced from CLAUDE.md. User-facing description:
`website/src/content/docs/features/investigations.md`. Decisions:
`docs/adr/0027-investigations-reference-runs.md` (model, tombstones, report) and
`docs/adr/0028-entity-graph-derived-per-investigation.md` (graph storage, normalization, library).

## Model

`features/investigations/models/`: `Investigation` (name, notes, `TimestampMixin`) owns
`InvestigationItem` rows `(feature, run_id, target, note, added_at)`, unique on
`(investigation_id, feature, run_id)`. `run_id` is not a foreign key; `target` is a snapshot taken
when the item is added, so a tombstone (run deleted from history) still says what it was about.
Item changes call `crud.touch()` to bump the investigation's `updated_at` (the list sorts by it),
since `onupdate` only fires when the investigation row itself changes.

## RunSource: one per feature

`core/run_sources/source.py`'s `RunSource` is the whole contract a feature fulfils to be
investigable: `model` (the run table), `load(db, run_id)` (the run with its results, or None),
`target(run)`,
`build_sections(run, locale)` (report sections, `core/reports` types) and `extract(run)` (the
entity extractor). Each lives in the feature's own `service/run_source.py`; `ioc_lookup` reuses its
single-export `build_sections`. Only the report and the graph call `load`; the detail view and
note/notes saves use `missing_item_ids` (one `id IN (...)` query per feature on `model`), and
adding an item reads just the run row for its target, so a 10k-comment Reddit run is never
loaded to show a tombstone flag. `app/utils/run_source_registry.py` is the only place that knows
them all (`RUN_SOURCES`), plus `RUN_SOURCE_EXEMPT` with a reason per feature not yet covered.
`tests/core/test_run_source_coverage.py` fails on a feature in `activity_feature_names()` (every
feature the activity feed lists) that is in neither.

To add a feature: write its `service/run_source.py`, register it, drop its exemption, add a case
to `tests/features/investigations/test_run_sources.py`, pass `runRef` to its
`HistoryDetailHeader`, and update the table on the website page.

## Entities and graph

`core/entities/model.py`: an `Entity` is `(type, normalized value)` with a display-only `label`
and `raw` (the value as the source gave it, returned as `raw_value` - links and pivots use it,
since normalizing lowercases account URLs);
`entity()` normalizes, `Extraction.link()` records a link (self-links are dropped), and
`link_local_part()` adds the email → local-part username link both `ioc_lookup` and
`email_search`'s user_scanner runs use. `ENTITY_TYPES` is what the API advertises and what the
frontend colours (`features/investigations/constants/entityTypes.js`).

`core/entities/graph.py`: `merge()` dedupes nodes by id and links by `(source, target,
relation)`, keeping a `RunRef` set on each for provenance; `filter_types()` then `cap()` (roots
first, then degree, ties by id, `MAX_GRAPH_NODES = 300`); `top_connected()` feeds the report.
`merge()` also records `type_counts` before any filter or cap, which the UI's type chips use, so
a type the cap dropped entirely still has a chip.
Nothing is persisted: `GET /api/investigations/{id}/graph` resolves the items and runs the
extractors on every request.

The `ioc_lookup` extractor reads stored provider `data` for six providers (`ip_geo`, `ip_rdap`,
`internetdb`, `gravatar`, `haveibeenpwned`, `leakcheck`), only when the stored result's `status`
is `found`. A provider whose response shape changes simply stops contributing nodes; the
provider's own drift checks (`ProviderSpec.expects`) are what catch the change.

## API

`routers/investigation_routes.py`, prefix `/api/investigations`: list/create/get/patch/delete,
`POST|PATCH|DELETE .../{id}/items[/{item_id}]` (422 `INVESTIGATION_FEATURE_UNSUPPORTED` or
`INVESTIGATION_RUN_NOT_FOUND`, 409 `INVESTIGATION_ITEM_EXISTS`), `GET .../{id}/report?format=&locale=`,
`GET .../{id}/graph?types=`, plus `GET /features` (registry labels) and
`GET /memberships?feature=&run_id=` (which investigations hold a run, for the add menu). The
duplicate-add 409 comes from `find_item` or, for two concurrent adds, from the unique
constraint's `IntegrityError`.

## Frontend

`core/services/api/investigationsService.js` and `core/components/AddToInvestigationButton.jsx`
live in core because `HistoryDetailHeader` renders the button when given `runRef`. The page is
`features/investigations/` (list, detail with notes and items, `EntityGraph` on cytoscape.js with
the `cose` layout, `NodePanel` with provenance links and `?q=` pivots - an account node pivots
through its linked username). The report downloads through `core/components/ui/ApiDownloadButtons`,
since a plain `<a href>` can't carry the bearer token.
