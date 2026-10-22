# The entity graph is derived on request per investigation and drawn with cytoscape.js

Corvid's features each find things (accounts, mailboxes, breaches, ASNs, subreddits) but nothing
showed how the results of different runs connect. A graph over everything ever searched gets
noisy fast and would need its own tables kept in step with every feature's history; the
investigation (`docs/adr/0027-investigations-reference-runs.md`) already gives a small, deliberate
scope. Drawing a graph (layout, hit-testing, zoom, PNG export) is genuinely non-trivial, so this
is a place where a frontend dependency is justified.

## Decision

- Scope is one investigation: `GET /api/investigations/{id}/graph`. There is no global graph.
- Nothing is stored. Each `RunSource` has a pure extractor (run → entities + links); the endpoint
  loads the investigation's runs, runs the extractors and merges the result on every request.
- An entity is `(type, normalized value)`; the same normalized value from two features is one
  node (`username:jdoe` from Reddit and from maigret meet). Normalization lowercases (account
  URLs included, since tools disagree on a profile URL's case; plain URL paths keep theirs),
  strips a trailing dot from domains and IDNA-encodes them, and strips `@`/`u/` from usernames.
  Normalization is for matching only: each node also carries the value as found, which links
  and pivots use.
- Account nodes come only from positive results (a maigret/social-analyzer claimed site, a
  user_scanner registration, a Gravatar verified account); unknown or errored checks make none.
- Past 300 nodes the response keeps the most connected ones and says it was truncated; the UI
  shows that and offers the entity-type filter (`types=`), with per-type counts taken before the
  cap, instead of drawing everything.
- The frontend draws it with cytoscape.js (MIT, no runtime dependencies) and its built-in `cose`
  layout, styles per entity type, and `cy.png()` for export.

On request is always consistent with history (a deleted run simply drops out) and costs nothing
at the size of one investigation; cytoscape covers layout, styling, events and PNG export in one
package at a node count where canvas rendering is enough.

## Accepting

- No cross-investigation view: a link between two investigations is only found by adding the
  runs to one of them.
- Every graph request re-reads and re-extracts every run in the investigation.
- cytoscape.js adds roughly 400 KB minified to the Investigations page's lazy chunk.

## Revisit

- If investigations routinely hold hundreds of runs and the graph endpoint becomes slow, or a
  global graph is wanted: that is when materialized `entities`/`links` tables pay for their
  backfill and reconciliation.

## Rejected

- **Materialized `entities`/`links` tables written on run completion** - fast across all
  history, but needs a backfill, cleanup when a run is deleted and a write hook in every feature,
  for a scope that is small anyway.
- **A global graph over all history** - noisy, and it is what forces materialization.
- **sigma.js + graphology** - WebGL for tens of thousands of nodes we cap at 300; two packages,
  with layouts and PNG export as more add-ons.
- **vis-network** - what MiniOSINT uses; heavier and slower-moving for the same feature set.
- **react-force-graph** - force layout only, and pulls in d3 plus three.js for its 3D mode.
