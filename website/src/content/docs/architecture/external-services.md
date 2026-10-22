---
title: External Services
description: Every third-party host Corvid's backend (or, for a couple of client-side-only cases, its frontend) talks to, feature by feature.
sidebar:
  order: 60
---

A single reference for every external service Corvid integrates with, across every feature — not
just [IOC Lookup](/corvid/features/ioc-tools/)'s 32 providers. For AI/LLM providers specifically,
see [AI / LLM Providers](/corvid/architecture/ai-providers/) instead — this page only lists them
by name. Unless noted otherwise, a fetch to a user-supplied or externally-sourced URL (RSS feeds,
article pages, WHOIS/RDAP redirects) is validated by Corvid's own SSRF guard first; a fixed host
below (VirusTotal, crt.sh, etc.) never needs that, since only the query value is user-supplied,
never the host.

## When a source changes its response format

Corvid distinguishes a source that found nothing from one that now answers in a different shape.
For the Domain Finder panels (crt.sh, Cert Spotter, Wayback Machine, HackerTarget, RapidDNS, RDAP,
URLScan.io)
a changed format is reported as a `SCHEMA_DRIFT` error instead of an empty result, and for the
keyless IOC Lookup providers (FFraud, FIRST.org EPSS, URLScan.io, CISA KEV, Library of Leaks,
OpenPhish, Shodan InternetDB, LeakCheck, IP Geolocation, IP RDAP, Gravatar), as well as Censys,
the row shows "changed its response format" instead of an empty card. If you see
that, the provider changed its API; please open an issue.

## IOC Lookup

Auto-routed by IOC type; see [IOC Tools → Integrated services](/corvid/features/ioc-tools/) for
which provider handles which type.

- **Needs an API key** (Settings → API Keys): AbuseIPDB, AlienVault OTX, CheckPhish, CrowdSec,
  CrowdStrike, EmailRep.io, GitHub (optional — raises an otherwise-anonymous rate limit, not
  required), Have I Been Pwned, Hunter.io, IPQualityScore, LeakIX, Maltiverse, MalwareBazaar, Mandiant, NIST NVD,
  Pulsedive, Reddit, Google Safe Browsing, Shodan, ThreatFox, Twitter/X, URLhaus, VirusTotal.
  ThreatFox, URLhaus and MalwareBazaar all take the same free abuse.ch Auth-Key (get one at
  [auth.abuse.ch](https://auth.abuse.ch/)) — paste it into each service's field.
- **Fully keyless**: Address Blacklist (resolved locally, see below), CISA KEV, FFraud, FIRST.org
  EPSS, Hudson Rock, Library of Leaks, OpenPhish, URLScan.io.
- **Address Blacklist** resolves instantly from a local table, refreshed daily rather than called
  per lookup, from three free keyless feeds: OFAC's `sanctionslistservice.ofac.treas.gov` (SDN
  digital-currency addresses), ScamSniffer's GitHub-hosted phishing-address database, and
  OpenSanctions' `data.opensanctions.org` (Israel counter-terror-financing crypto export).
- **CISA KEV** (`cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json`) — the
  full catalog (no per-CVE endpoint exists) is fetched and kept in an in-process cache for up to
  an hour, rather than re-downloaded on every CVE lookup.
- **OpenPhish** (its GitHub-hosted `openphish/public_feed` `feed.txt`) — the free community feed is a flat list of active
  phishing URLs with no per-URL lookup endpoint, so it's cached the same way as CISA KEV: fetched
  in full and kept in-process for up to an hour rather than re-downloaded per lookup.

## Domain Finder

- **crt.sh** — Certificate Transparency log search, also used for subdomain enumeration via SAN
  entries. Keyless.
- **Cert Spotter** (`api.certspotter.com`) — SSLMate's Certificate Transparency issuances API,
  queried alongside crt.sh for the same subdomain panel. Keyless; the unauthenticated tier allows
  only a few queries an hour, so one page is read per lookup.
- **rdap.org** — RDAP bootstrap redirector for WHOIS-style domain registration data. Keyless.
- **DNSDumpster** (`api.dnsdumpster.com`) — DNS/ASN/geo/PTR/HTTP-banner enrichment. Needs its own
  free-tier key (capped at 50 records/lookup); configured under Settings → API Keys.
- **URLScan.io** public search (`urlscan.io/api/v1/search/`) — prior scan results for a domain.
  Keyless — a separate, unauthenticated endpoint from the keyed URLScan.io provider used in IOC
  Lookup.
- DNS record lookups (A/AAAA/MX/TXT/NS/CNAME, reverse PTR) go over the DNS protocol via the host's
  own system resolver, not an HTTP API.

## Username Search

- **Hudson Rock** (`cavalier.hudsonrock.com`) — infostealer/malware-log exposure by username.
  Keyless; a separate, trimmed client from IOC Lookup's Hudson Rock provider.
- **threatactorusernames.com** — prebuilt index of usernames scraped from cybercrime forums.
  Keyless.
- Maigret and social-analyzer scan against their own bundled, locally-stored site databases
  (hundreds of entries each) — each scan then makes one request per candidate site in that local
  list, which isn't a fixed, enumerable "provider" the way the rest of this page is. Maigret's
  site database itself auto-updates from its GitHub-hosted release, keyless.

## Email Search

- **mailcat-osint**'s 26 built-in checkers (Gmail, Yandex, Proton, Mail.ru, Fastmail, and 21
  others) — checks whether an email/username is registered with each provider, via SMTP RCPT
  probe, provider API, or headless-Chromium page check depending on the provider. All keyless.
  SMTP-based checkers (Gmail, Yandex, mail.de) and headless-Chromium checkers (Fastmail, int.pl,
  onet.pl) are off by default — see [Email Search](/corvid/features/email-search/).

## Reddit Search

- **Arctic Shift** (`arctic-shift.photon-reddit.com`) and **PullPush** (`api.pullpush.io`) — two
  independent archive APIs queried in parallel and merged/deduped, so moderator-removed and
  author-deleted content is still findable. Both keyless.

## Git Recon

- **GitHub API** (`api.github.com`) — profile, repos, GPG keys, and commit-author search, via the
  `gitcolombo` library. Unauthenticated calls cap at 60/hour; an optional PAT (same
  `github_pat` key as IOC Lookup's GitHub provider) raises that.
- Repo cloning is a `git clone` subprocess, not an HTTP call — restricted to
  `https://github.com/<owner>/<repo>` by an argv allowlist rather than the SSRF guard, since a
  subprocess is outside the guard's reach.

## YouTube

- **oEmbed** (`youtube.com/oembed`) — baseline title/author/thumbnail. Keyless.
- Page scrape of the video's own watch page — description/duration/publish date/tags oEmbed
  doesn't expose. Keyless, unofficial (degrades silently if YouTube's markup changes).
- **YouTube Data API v3** (`googleapis.com/youtube/v3`) — view/like/comment counts, tags,
  category, and comment search. Needs its own key, configured under Settings → API Keys.
- Thumbnail URLs (`i.ytimg.com`) are constructed directly, not fetched server-side at all — the
  browser loads them.

## Instagram Search

- **Instagram** (`instagram.com`, via the `instaloader` library) — public profile metadata
  (bio, links, counters, verified/business/private flags) by username. Keyless by default;
  Instagram rate-limits anonymous requests aggressively. An optional imported browser-session
  cookie (`instagram_session` key, a JSON object, never a password) unlocks data anonymous
  lookups can't reach. Automated access violates Instagram's ToS either way.

## Newsfeed

- RSS feeds and full-article text are fetched from whatever feed/article URLs are configured —
  arbitrary, SSRF-guarded hosts, not a fixed provider list. 14 default feeds ship out of the box
  (BleepingComputer, Krebs on Security, The Hacker News, and others).
- Favicon fetching follows the same SSRF-guarded pattern, per configured feed's own site.
- MITRE ATT&CK technique/group/software enrichment is **not** fetched from any external MITRE
  dataset — it's inferred by the configured LLM from the article text itself.

## RU Business Check

Keyless, fixed hosts only (just the ИНН/name query is user-supplied). Live lookups:
`egrul.nalog.ru` (ЕГРЮЛ/ЕГРИП), `service.nalog.ru` (РДЛ), `kad.arbitr.ru` (arbitration cases),
`fedresurs.ru` (bankruptcy and company publications), `pb.nalog.ru` (mass-registration address),
`fedsfm.ru` (terrorism/WMD-financing list), `zakupki.gov.ru` (barred suppliers), `bo.nalog.gov.ru`
(ГИР БО statements), `rmsp.nalog.ru` (МСП register). Downloaded on a schedule and matched locally
by exact ИНН: the ФНС disqualified-persons open-data set (`data.nalog.ru`), the Банк России
warning list (`cbr.ru`) and the US Treasury OFAC SDN list (`treasury.gov`, following its redirect to
OFAC's published-file storage). See [RU Business Check](/corvid/features/ru-business-check/) for what
each source contributes to a verdict.

## Image Tools

- **Nominatim** (`nominatim.openstreetmap.org`) — reverse-geocodes a photo's EXIF GPS coordinates
  to a human-readable address. Keyless.
- Reverse image search (Google Lens, Yandex, TinEye, Bing) is client-side only — the browser
  builds a deep link straight to each engine; Corvid's backend never fetches or proxies these.
- When GPS coordinates are present, the same client-side pattern deep-links ShadowMap,
  Flightradar24, Open Infrastructure Map, and MapChecking, all keyless.
- **Google Maps Embed API** (`google.com/maps/embed`) — an optional embedded Street View panorama
  centered on the photo's coordinates. The only key in Corvid whose raw value reaches the
  frontend rather than staying server-side, since the browser loads the iframe directly; see
  [ADR 0008](https://github.com/z0rats/corvid/blob/main/docs/adr/0008-google-maps-key-exposed-to-frontend.md).
- **ChronoVerify** (`chronoverify.com`) — capture-time/C2PA-provenance and pixel-forensics
  verdict. Opt-in only: unlike every other entry on this page, the image is sent only when the
  user explicitly clicks "Check with ChronoVerify" in the Image Tools UI, not on every upload.
  Works keyless (free, rate-limited per IP); an optional key raises the limit.

## Dork Runner

- **DuckDuckGo** (`html.duckduckgo.com`, the default engine), **Google**, and **Bing** — scraped
  HTML search results for parameterized dork queries. All keyless, no API involved; Google/Bing
  are best-effort since both actively block scripted queries.

## Operational checks (not user data)

A few background checks that send no investigation data anywhere — purely "is there a newer
version" pings:

- `api.github.com/repos/z0rats/corvid/releases/latest` — is a newer Corvid release available
  (About page).
- `pypi.org/pypi/{package}/json` — is a newer version of a vendored tool (Maigret, social-analyzer,
  mailcat-osint) available; a container rebuild is still needed to actually install it.
- VirusTotal, Shodan, and Hunter.io's own quota endpoints, using the already-configured key — the
  live quota panel under Settings → API Keys.

## Source health checks

A weekly CI job (not part of a running Corvid instance) calls the keyless sources above with
fixed reference queries and fails when one changes its response shape, moves, or starts demanding
a key; sources that simply don't answer the CI runner (rate limits, geo blocks, server errors) are
skipped, with the reason shown in the run summary. Checked today: the keyless IOC lookup providers
(CISA KEV, FIRST EPSS, OpenPhish, URLScan.io, Library of Leaks, FFraud), the address-blacklist
feeds, the default newsfeed RSS feeds, the Domain Finder panels (crt.sh, HackerTarget, RapidDNS,
Wayback Machine, RDAP, URLScan.io), the RU Business Check registries and dumps, the Reddit
archives, threat-actor usernames, Hudson Rock, YouTube, DuckDuckGo, the OpenSanctions dump,
Nominatim, PyPI and GitHub releases. A failure opens a GitHub issue in the Corvid repository.
Every external source the backend calls is listed as either checked or deliberately exempt (for example
key-only, or probing it would act on a real account), and the test suite fails when a new
source is added without that decision.
