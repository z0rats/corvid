# Command palette and cross-feature navigation

Deep-dive referenced from AGENTS.md's Frontend architecture section. Full UX spec in
`docs/command-palette-plan.md` — this covers implementation internals only.

## Core pieces

- `core/utils/commandParser.js` — framework-free parser for the search grammar (`#tag`,
  `type:kind`, `>action`, `value tool` pivot, `defang`/`fang`, playbooks).
- `core/utils/iocTypeDetection.js` — a JS port of `ioc_utils.py`'s `determine_ioc_type()`, kept
  in sync via the shared fixture `testdata/ioc-type-detection-cases.json` (consumed by both
  `test_ioc_type_detection.py` and the JS test).
- `core/hooks/useCommandPalette.js` — owns all palette state (open/close, recording,
  breadcrumbs), instantiated once in `CommandPalette.jsx` (mounted in `Layout.jsx`, inside the
  `AccessGate` subtree). Other components open it by dispatching the
  `OPEN_COMMAND_PALETTE_EVENT` window event rather than lifting state.
- Playbooks (recorded tool-ID chains) and pinned/recent tools live in `localStorage` via
  `core/utils/commandPaletteStorage.js`.

## Start screen

The `/` route renders `StartScreen.jsx` (a lighter, non-modal subset of the same grammar) unless
Settings → Command Palette's `start_screen` is set to `newsfeed` — three `GeneralSettings`
columns (`auto_open_on_single_match`, `start_screen`, `always_tiles`) back that settings tab.

## YouTube URL / Steam profile special-cases

`IOC_TYPES.YOUTUBE_VIDEO_URL` and `IOC_TYPES.STEAM_PROFILE` are both deliberately excluded from
`detectIocType`'s own priority chain (a YouTube or steamcommunity.com link is still typed plain
`URL` there, so `ioc_lookup`'s provider routing for either is unaffected) — `commandParser.ts`'s
`parseQuery` injects the matching module's match itself, layered on top of the normal `URL`
match rather than replacing it, via `isYoutubeVideoUrl()`/`isSteamProfileTarget()`. Steam's case
additionally has a second injection point: a bare SteamID64/SteamID3/SteamID2 (no URL wrapper)
matches nothing in `detectIocType`'s chain at all, so `isSteamProfileTarget()` is checked a
second time as a primary classification once `detectIocType` returns `UNKNOWN` - otherwise it
would fall through to the generic identity-tool fallback and lose its dedicated match.
`isSteamProfileTarget()` deliberately excludes a bare vanity name (too ambiguous for global
detection - it's still typeable directly into Steam Recon's own form, just not auto-detected).

## Cross-feature "send to X"

E.g. `email_search`'s found email → `ioc_lookup`, `ioc_lookup`'s domain result → `domain_finder`.
The value passes via a `?q=` query param (`core/utils/crossFeatureNav.js`'s `buildPrefillUrl`);
the target feature reads and clears it on mount via `core/hooks/usePrefillFromQuery.js`.
`core/components/ui/ChainActionButton.jsx` is the reusable trigger.

## Palette pivot gotcha

A palette pivot (`value tool`, e.g. `john_doe reddit`) uses the same mechanism. Any single-value
"identity" lookup wired for it (`reddit-search`, `username-search`, `email-search`,
`git-recon`'s nickname mode) needs **two** things or the value silently never arrives despite a
successful navigation:

1. Its root component's `index` → `"new"` redirect must be
   `<Navigate to={{ pathname: 'new', search: location.search }} replace />`, **not** a bare
   `to="new"` (which drops the query string).
2. The `"new"` tab must call `usePrefillFromQuery()` to both fill the form (`|| ''`, not a
   default param — the hook yields `null`, not `undefined`) and trigger the search itself.

`{Reddit,Username,Email,GitRecon}Search.test.jsx` regression-test this pattern; a new
identity-style feature should add its own copy of the test.
