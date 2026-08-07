---
title: Browser Extension
description: Minimal Chrome extension with a side panel, an inline selection popup, and a flat right-click menu for IOC lookup, reverse image search, and EXIF metadata.
---

`extension/` is a minimal MV3 Chrome extension ("Corvid Quick Send"). No build step (load
unpacked as-is). It runs a content script on every page, so Chrome shows a broad "read and
change all your data on all the websites you visit" permission at install — that's for the
inline selection popup below; it's the extension watching text selections client-side, not it
sending anything anywhere on its own (see "Known limits" for exactly what does/doesn't talk to
your Corvid instance).

## Side panel

Click the toolbar icon → opens a side panel on the current tab — no new tab, no tab switch.
**Home** has a search box (paste any value, see its detected type live, open it in
`ioc-tools/lookup`), a few quick links (IOC Lookup, Domain Finder, Username Search, Image Tools),
and the Corvid base URL setting. **EXIF** shows the metadata viewer below, switched to
automatically right after a right-click "Show EXIF metadata" — a plain toolbar-icon click always
opens on Home regardless of what was shown there before.

## IOC lookup on selected text

Select text that unambiguously matches a supported IOC type (IPv4/IPv6, domain, URL, email,
MD5/SHA1/SHA256, CVE, phone) and a small 🔎 popup appears right next to the selection,
DeepL-style. It never appears for plain text — no match, no popup. Click it (or use the
equivalent right-click menu item: **Corvid** → **Search `<type>` in Corvid: `<value>`**, label
updated live, or the side panel's search box) to open `<base_url>/ioc-tools/lookup?q=<selection>`
in a new tab; the app handles its own auth from the browser's stored token like any other tab.
This is the only feature that talks to your Corvid instance — reverse search and EXIF below
don't, and work with no instance running.

## Reverse image search

Right-click any image → **Corvid** → **Reverse search: All (Google, Yandex, Bing)** opens all
three in new tabs at once, or pick a single engine (Google Lens / Yandex Images / Bing Visual
Search / TinEye) to open just that one. TinEye is excluded from "All" — only reachable via its own
item. Only works for images with a real `http(s)` source (not `data:`/`blob:` placeholders), since
these engines fetch the image server-side.

## EXIF metadata viewer

Right-click any image → **Corvid** → **Show EXIF metadata** → opens the side panel's **EXIF** tab
with whatever it can read: dimensions, camera make/model/lens, shot settings, timestamps, and GPS
coordinates (with a one-click Google Maps link) when present. Supports JPEG, PNG, WebP, and
standalone TIFF — no XMP/IPTC/maker-notes — and social networks/CDNs commonly strip EXIF on
upload entirely, in which case the panel says so. Parsing is done by a small hand-rolled parser
bundled with the extension, not a third-party library.

The first use asks Chrome for a one-time permission to read image bytes across sites (needed
because the image can live on any domain); it's requested at that point, not at install, and
covers every domain from then on. If the panel opens but shows nothing, check the extension's
own service-worker console (`chrome://extensions` → Corvid Quick Send → **Inspect views: service
worker**) rather than the page's — the failure logs there, not in the page you right-clicked on.

## Install

1. Go to `chrome://extensions` and enable **Developer mode**.
2. Click **Load unpacked** and select the repository's `extension/` folder.
3. Click the extension's icon → the side panel's **Settings** section → set your Corvid base URL
   (default `http://localhost:4000`). Right-click the toolbar icon → **Options** opens the same
   setting on its own page too, kept as a fallback entry point.

## Known limits

The IOC lookup feature is intentionally the smallest possible slice of a fuller planned
extension (token-based API calls) — see the "Chrome extension as a thin client" entry in the
project's `ROADMAP.md`. Quick links in the side panel are a handful of hand-picked routes, not a
full nav mirror. Reverse search and EXIF metadata are self-contained and never touch the Corvid
backend or token. IOC-type detection is a hand-rolled port of `frontend`'s
`iocTypeDetection.js` (plus a phone-number heuristic Corvid's own IOC vocabulary doesn't have a
lookup for), shared between the content script, the right-click menu, and the side panel's search
box — it only decides whether/how to surface a match, the actual search still goes through
whatever `ioc-tools/lookup` itself supports. The content script only reads the page's current
text selection and, on a click it triggered, relays the matched value to the background script —
it doesn't read page content otherwise or fetch anything itself.
