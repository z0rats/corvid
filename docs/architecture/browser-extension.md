# `extension/` — browser extension

Deep-dive referenced from AGENTS.md. Setup and troubleshooting: `extension/README.md`.

`extension/` is a minimal MV3 Chrome extension ("Quick Send") built around IOC-type detection
(`ioc-type-detection.js`, shared by all three surfaces below) gating three ways in to
`<base_url>/ioc-tools/lookup?q=...` — the only Corvid backend/token interaction anywhere in the
extension.

## Content script

`content.js`, `matches: <all_urls>` — the one broad, install-time permission this extension asks
for: a DeepL-style floating popup next to a text selection, shown only on an unambiguous type
match; click messages the background script (content scripts can't call `chrome.tabs` directly).

## Right-click menu

"Corvid", one flat parent — no nested submenus, items scoped by click context: IOC lookup on a
selection (title updated live via `chrome.contextMenus.onShown`), reverse image search (Google
Lens/Yandex/Bing/TinEye, list hand-kept in sync with `frontend`'s `imageConstants.js`), and an
EXIF metadata viewer (`exif-parser.js`, hand-rolled TIFF/EXIF/GPS parser covering
JPEG/PNG/WebP/TIFF, shared via `importScripts()` in the service worker and a `<script>` tag in
`sidepanel.html`; reading image bytes cross-origin needs a `http(s)://*/*` host permission
requested at runtime on first use — narrower and opt-in, unlike the content script's install-time
grant).

## Side panel

`sidepanel.html`/`.js`, opened on the current tab via
`chrome.sidePanel.setPanelBehavior({openPanelOnActionClick: true})` when the toolbar icon is
clicked — mutually exclusive with `chrome.action.onClicked`, so there's no listener for it: one
document, two tabs — **Home** (search box, a few hand-picked quick links, and the base-URL
setting — same `chrome.storage.local` key `options.html`/`options.js` still read/write as a
fallback settings entry point) and **EXIF** (the viewer above), auto-switching to EXIF only when
a right-click just triggered it (a `storage.session` write newer than 5s) so a plain toolbar-icon
open always lands on Home.

## Other notes

No build step, load unpacked. Separate from `frontend/`, not part of any build/test pipeline, with
one exception: `generated-ioc-patterns.js` — loaded before `ioc-type-detection.js` everywhere the
latter is (`manifest.json`'s `content_scripts`, `sidepanel.html`, `background.js`'s
`importScripts`) — is regenerated from `frontend/src/core/utils/iocTypeDetection.ts`'s
`IOC_TYPE_PATTERNS` by `frontend/scripts/generate-extension-ioc-patterns.js` (via
`ts.transpileModule`, no bundler needed since that source has no imports of its own). A pre-commit
hook regenerates it automatically when `iocTypeDetection.ts` changes; CI fails if the committed
file is stale. `ioc-type-detection.js` itself stays hand-written on top of that generated table —
it adds a `Phone` type spliced into the priority chain and trailing-punctuation stripping, neither
of which the frontend's own `detectIocType` needs — and is cross-checked against the shared
`testdata/ioc-type-detection-cases.json` fixture the same way `frontend`'s copy is (see
`frontend/src/core/utils/extensionIocPatterns.test.js`). The reverse-search engine list is still
hand-duplicated (not shared code) from `frontend`'s `imageConstants.js` — re-check by hand when
that changes. See `extension/README.md` for setup (including where to look when the EXIF panel
silently fails — its own service-worker console, not the page's).
