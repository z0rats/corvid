---
title: Instagram Search
description: Look up a public Instagram profile's metadata by username, and scan its followers, followees, or posts.
sidebar:
  order: 170
---

Looks up a public Instagram profile's metadata by username — display name, bio, external link,
follower/following/post counts, and verified/business/private flags — via
[Instaloader](https://github.com/instaloader/instaloader). A second, separate scan (**New Scan**
tab) walks a profile's followers, followees, or posts, with its own persisted history.

Two modes are available everywhere in this module:

- **Anonymous** (default) — no setup required. Instagram rate-limits anonymous requests
  aggressively, so lookups can fail or get throttled without warning.
- **Session** — optional, configured under Settings → API Keys as `instagram_session`: a JSON
  object with `sessionid`, `csrftoken`, and `ds_user_id` cookies imported from a logged-in
  browser session. Never a password — Instagram ToS forbids automated access regardless of mode,
  so use a disposable account and expect it may get rate-limited or banned either way. Followers
  and followees specifically **require** a session — Instagram only shows either list to a
  logged-in request, regardless of the target profile's own privacy setting.

## Getting a session

Instaloader authenticates the same way a browser does: with the session's cookies, not a
password. To get them:

1. In your browser, log into `instagram.com` with a **disposable/secondary account** — not your
   main one. Automated access violates Instagram's ToS either way, and this account may get
   rate-limited or banned.
2. Open your browser's DevTools (`F12`, or right-click → Inspect) and find the cookies for
   `https://www.instagram.com`:
   - **Chrome/Edge**: Application tab → Storage → Cookies → `https://www.instagram.com`
   - **Firefox**: Storage tab → Cookies → `https://www.instagram.com`
   - A cookie-export extension (e.g. Cookie-Editor) works too, and is often faster than digging
     through DevTools by hand.
3. Copy the **value** of exactly these three cookies: `sessionid`, `csrftoken`, `ds_user_id`.
   Everything else Instagram sets (`mid`, `ig_did`, `rur`, ...) isn't needed — leaving them out
   keeps the pasted value short.
4. Build a small JSON object from them:

   ```json
   {"sessionid": "<value>", "csrftoken": "<value>", "ds_user_id": "<value>"}
   ```

5. In Corvid, go to **Settings → API Keys**, find **Instagram Session**, paste that JSON as the
   key value, save, and make sure it's toggled active.
6. `GET /api/instagram-search/health` (or the module's own health indicator, once you next load
   it) reports whether a well-formed session is currently configured.

The session stays valid until Instagram invalidates it (password change, manual logout, or a
security check) — there's no expiry Corvid can predict, so if lookups that used to return
`mode: "session"` suddenly fall back to anonymous, re-extract the cookies and paste them again.
The value is stored encrypted at rest, the same as every other API key, and is never echoed back
by the API or written to a log.

## Followers / followees / posts scan

The **New Scan** tab runs one of three scans against a username:

- **Followers** / **Followees** — needs a configured session (see above); collects each
  account's `username`/`full_name` only, not its full profile.
- **Posts** — works in both modes; collects each post's shortcode, permalink, publish date,
  video flag, like/comment counts, and a truncated caption. No media is downloaded.

Every scan is capped on item count and wall-clock time — a very large follower list or post
history is sampled, not walked in full, and the result reports `truncated: true` when either cap
was hit before the list was exhausted. A running scan can be cancelled from the UI, which keeps
whatever it collected up to that point. Past scans are listed under the **History** tab, same
lifecycle (SSE-streamed, cancellable, persisted) as Git Recon/Amass/RU Business Check.

A private profile the session doesn't follow still returns the metadata Instagram exposes from
the **Profile** tab's lookup (`is_private: true`), rather than an error. The profile picture is
shown as a link, not an embedded image — embedding it would leak the analyst's IP to Instagram's
CDN.

Pasting a username into the command palette (`/` or `⌘K`/`Ctrl+K`) prefills and runs the
**Profile** tab's lookup directly.
