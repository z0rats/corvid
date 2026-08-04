# Corvid Quick Send (MVP)

Minimal Chrome extension: click the toolbar icon to send the selected text on the
current page to your Corvid instance's IOC lookup, prefilled and auto-run. No build
step — plain MV3 files, load unpacked as-is. No API token or CORS changes needed:
it only opens a new tab (`<base_url>/ioc-tools/lookup?q=<selection>`), the app
handles its own auth from the browser's stored token like any other tab.

## Install

1. `chrome://extensions` → enable **Developer mode**.
2. **Load unpacked** → select this `extension/` folder.
3. Click the extension's icon → **Options** (or right-click the toolbar icon →
   **Options**) → set your Corvid base URL (default `http://localhost:4000`).

## Use

Select text on any page → click the Corvid icon in the toolbar → a new tab opens
with that text looked up. No selection → opens the lookup page empty.

## Known limits

Selection reading is blocked on `chrome://` pages, the Chrome Web Store, and a
few other restricted origins (a Chrome policy, not fixable from the extension).
This is intentionally the smallest possible slice of the fuller plan in
`../ROADMAP.md` (Client surfaces) — no context menu, no popup, no token-based
API calls, no options beyond the base URL.
