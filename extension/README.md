# Corvid Quick Send

Minimal Chrome extension: a side panel (search, quick links, settings) opened from the toolbar
icon, an inline popup and a flat right-click menu ("Corvid") for searching selected text as an
IOC, reverse-image-searching, and reading EXIF metadata. No build step — plain MV3 files, load
unpacked as-is.

Runs a content script on every page (needed for the inline selection popup below), so Chrome
shows a "Read and change all your data on all the websites you visit" permission at install —
that's this extension watching text selections client-side, not it sending anything anywhere on
its own; see "Known limits" for exactly what does/doesn't talk to your Corvid instance.

## Install

1. `chrome://extensions` → enable **Developer mode**.
2. **Load unpacked** → select this `extension/` folder.
3. Click the extension's icon → opens the side panel → **Settings** section → set your Corvid
   base URL (default `http://localhost:4000`). Right-click the toolbar icon → **Options** opens
   the same setting on its own page too, kept as a fallback entry point.

## Use

Click the toolbar icon → opens a side panel on the current tab (no new tab, no tab switch):
- **Search** — paste any value, see its detected type live, click **Search in Corvid** to open
  `<base_url>/ioc-tools/lookup?q=<value>` in a new tab.
- **Quick links** — IOC Lookup, Domain Finder, Username Search, Image Tools.
- **Settings** — the Corvid base URL, same storage key as the Options page.

The same panel also shows EXIF results (see below) under its own **EXIF** tab, switched to
automatically right after a right-click "Show EXIF metadata" — the toolbar icon always opens on
**Home** regardless of what was last shown there.

Select text that unambiguously matches a supported IOC type (IPv4/IPv6, domain, URL, email,
MD5/SHA1/SHA256, CVE, phone) → a small 🔎 popup appears right next to the selection, DeepL-style.
Click it to open `<base_url>/ioc-tools/lookup?q=<selection>` in a new tab. It never appears for
plain text — no match, no popup, nothing injected into the page beyond the (invisible until
triggered) listener itself.

The same search is also in the right-click menu: select text → right-click → **Corvid** →
**Search `<type>` in Corvid: `<value>`**, with the label updating live to the detected type. Use
whichever is more convenient — all three (popup, menu, panel search box) go through the same
`openIocLookup` code path in the background script.

Right-click any image → **Corvid** → **Reverse search: All (Google, Yandex, Bing)** opens all
three in new tabs at once, or pick a single engine (Google Lens / Yandex Images / Bing Visual
Search / TinEye) to open just that one. TinEye is excluded from "All" — only reachable via its
own item. Only works for images with a real `http(s)` source (not `data:`/`blob:` placeholders)
— these engines fetch the image server-side, so it has to be a public URL they can reach.

Right-click any image → **Corvid** → **Show EXIF metadata** → opens the side panel's **EXIF** tab
with whatever it can read from the image: dimensions, camera make/model/lens, shot settings,
timestamps, and GPS coordinates (with a one-click Google Maps link) when present. Supports JPEG,
PNG (`eXIf` chunk), WebP (`EXIF` chunk — only present in the extended/VP8X container, so a plain
lossy/lossless WebP never has one), and standalone TIFF — no XMP/IPTC/maker-notes, and social
networks/CDNs commonly strip EXIF on upload entirely, in which case the panel says so. The first
time you use it, Chrome asks for a one-time permission to read image bytes across sites (needed
because these images can live on any domain); after that it never asks again.

### If EXIF shows nothing

The side panel opening is separate from the page you right-clicked on — if it silently fails,
nothing shows and nothing logs to that page's own console. Check the extension's own console
instead: `chrome://extensions` → Corvid Quick Send → **Inspect views: service worker**. Every
failure path (side panel open, permission request, fetch) is wrapped and logged there.

## Known limits

This is intentionally close to the smallest possible slice of the fuller plan in
`../ROADMAP.md` (Client surfaces) — no token-based API calls, quick links are a handful of
hand-picked routes rather than a full nav mirror. Reverse search and EXIF metadata are
self-contained — they never touch the Corvid backend or token, and work even with no Corvid
instance running. IOC-type detection (`ioc-type-detection.js`, shared by the content script,
background script, and side panel) is a hand-rolled port of `frontend`'s `iocTypeDetection.js`
(plus a phone-number heuristic Corvid's own IOC vocabulary doesn't have a lookup for) — it only
decides whether/how to label a match, the actual search still goes through whatever
`ioc-tools/lookup` itself supports. `content.js` only reads `window.getSelection()` and, on a
click it triggered, relays the matched text to the background script via
`chrome.runtime.sendMessage` — it never reads page content otherwise, never fetches anything
itself, and injects nothing visible unless a qualifying selection is made.
