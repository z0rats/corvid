---
title: IOC Tools
description: IOC lookup, extraction, defanging, domain finder, and WHOIS/CT tools.
sidebar:
  order: 20
---

A set of tools for working with indicators of compromise:

- **IOC Lookup** — analyze IPs, domains, URLs, hashes, emails, and crypto addresses against
  services like VirusTotal, AlienVault, AbuseIPDB, Shodan, LeakIX, Reddit, and Twitter/X (see
  [External Services](/corvid/architecture/external-services/) for the full provider list, and
  which need an API key). The IOC type is auto-detected. Crypto addresses (EVM and Bitcoin) are
  additionally screened against a
  self-hosted reputation blacklist built from the OFAC SDN sanctions list and ScamSniffer's open
  phishing-address dataset, refreshed daily in the background — no API key or third-party call
  needed for that specific check. Lookups can be done one at a time or in bulk.
- **CVE enrichment** — a CVE lookup is additionally checked against CISA's Known Exploited
  Vulnerabilities (KEV) catalog (is it actively exploited in the wild, and is there known
  ransomware use) and FIRST.org's EPSS score (the probability it will be exploited in the next 30
  days). Both are keyless; KEV's full catalog is cached in-process for an hour since CISA only
  publishes a bulk dump, not a per-CVE endpoint.
- **OpenPhish** — checks a domain or URL against OpenPhish's free, keyless community phishing
  feed (a flat list, no per-URL endpoint, so the full feed is cached in-process for up to an
  hour rather than re-downloaded per lookup — same pattern as the CISA KEV catalog above).
- **URLhaus** — abuse.ch's malware-URL database, queried by URL, domain, or IPv4: a URL returns
  its own status, tags, blacklist flags, and dropped payloads; a domain or IP returns every
  malware URL URLhaus has seen on that host (first 10 shown). Needs a free abuse.ch Auth-Key,
  the same one ThreatFox uses.
- **Library of Leaks** — checks a domain or email against a public, keyless Aleph instance
  (run by DDoSecrets/investigativedata.io) indexing tens of millions of records across dozens of
  breach/leak collections. Only per-collection hit counts are shown — never the matching
  documents' own content — with a link out to review the source material on Library of Leaks
  itself. Bulk lookup isn't offered for it, to stay within the shared anonymous rate limit of
  this free, non-profit service.
- **Shodan InternetDB** — open ports, hostnames, tags, CPEs and known CVEs for an IPv4 or IPv6
  address from Shodan's free, keyless InternetDB (a weekly summary of Shodan's scans; free for
  non-commercial use). An IP Shodan has no data on shows "no data", not an error; each listed CVE
  is one click away from a CVE lookup. The full Shodan host lookup still needs a Shodan key.
- **LeakCheck** — which breaches an email address appears in (breach name and month) and which
  kinds of data were exposed, from LeakCheck's free, keyless Public API. Never the leaked records
  or passwords themselves. LeakCheck allows about one request per second, so bulk lookups are
  throttled to that.
- **IP Geolocation** — country, region, city, coordinates, ASN and owning company for an IPv4 or
  IPv6 address from ipapi.is's free, keyless HTTPS tier (about 1,000 lookups a day). Geolocation
  is approximate. It's context only and never changes a verdict.
- **IP RDAP** — who holds the netblock an IPv4 or IPv6 address is in: netblock name, handle,
  CIDR and range, registrant, registration dates and the abuse contact. Corvid asks `rdap.org`,
  which hands the query to whichever regional registry is authoritative (ARIN, RIPE NCC, APNIC,
  LACNIC or AFRINIC), so a European address gets RIPE's record rather than an ARIN referral. The
  abuse email is one click away from its own lookup. Unallocated space shows "no RDAP record".
  No API key needed.
- **Private and reserved addresses** — IP Geolocation, IP RDAP, Shodan InternetDB and Censys never send a private,
  loopback, link-local, CGNAT or documentation-range address to anyone; the card says the
  address is private or reserved instead.
- **Censys** — for an IP, the services Censys sees on each port (protocol, transport, last
  scan, TLS certificate subject), with hostnames, ASN and location; for a domain, the software
  stack Censys identifies on its web property (port 443, falling back to 80), with anything
  Censys classifies as a WAF highlighted, and that site's certificate. A domain Censys has
  nothing on uses two lookups from your Censys quota (443, then 80). Needs a free Censys account's Personal Access Token: create one under
  **API Access** in the Censys Platform user menu and paste it into Settings → API Keys →
  Censys. The free tier covers these lookups; Censys search needs a paid organization and isn't
  used. A rejected token shows a "create a new token" message.
- **Gravatar** — the public Gravatar profile behind an email address (display name, job,
  company, location, about) and the linked accounts Gravatar has verified (GitHub, X, Mastodon,
  Instagram and others). Each account links to the profile and offers a username search, and
  GitHub, Reddit, Instagram and Steam accounts also pivot straight into Git Recon, Reddit Search,
  Instagram Search or Steam Recon. An account whose URL holds a numeric or opaque id rather than
  a username (a Facebook `profile.php?id=` link, a Steam `/profiles/` link) gets no username
  pivot. The avatar is shown only as a link: your browser doesn't load it, so Gravatar isn't
  told the profile was viewed. If the address has no avatar of its own, the card says so instead
  of linking Gravatar's default image. The keyless API doesn't return a profile's other links,
  only verified accounts. An address without a public profile shows "no public profile". No API
  key needed.
- **History** — every single-IOC lookup is saved automatically once every queried service has
  responded, so past investigations stay reviewable. Any saved lookup can be exported as an HTML
  or PDF report — see [Reports & Exports](/corvid/architecture/reports/).
- **Newsfeed cross-reference** — a looked-up IOC is automatically checked against articles the
  [Newsfeed](/corvid/features/newsfeed/) module has already extracted IOCs from, surfacing any
  article that mentions the same indicator.
- **IOC Extractor** / **IOC Defanger** — pull IOCs out of free text, and fang/defang values for
  safe sharing (the command palette's `defang`/`fang <value>` shortcut does the same without
  opening this panel). Beyond the standard IOC types, the extractor also flags secret-shaped
  strings (AWS/Google/Slack/GitHub key formats, JWTs, PEM private key headers) and
  security-interesting API/route paths pulled from quoted strings in pasted source/JS
  (`/api/...`, `/admin/...`, etc.) — these two categories aren't tied to an `ioc_lookup`
  provider, so they skip the "Analyze" pivot the other categories offer.
- **Domain Finder** — discover recently registered typosquat/phishing domains via URLScan.io,
  with screenshots and threat-intel cross-checks against the resolved IP. No API key needed
  beyond URLScan.io's own.
- **WHOIS/RDAP** — via the public `rdap.org` bootstrap redirector. No historical snapshots (no
  API key needed).
- **Certificate Transparency subdomain enumeration** — via crt.sh's public JSON log mirror and
  SSLMate's Cert Spotter, queried together and merged into one deduplicated subdomain list; each
  discovered subdomain is one click away from re-running the Domain Finder typosquat search
  against it. The panel shows one line per source. A source that failed says "not checked"
  rather than reading as "no subdomains", and the panel only fails when both do, so CT results
  still come back while crt.sh is overloaded. Cert Spotter's keyless tier allows only a few
  queries an hour, so Corvid reads one page (about 80 of the newest certificates) and says when
  more exist. No API key needed.
- **HackerTarget subdomains** — passive subdomain enumeration via HackerTarget's free
  `hostsearch` API, resolved IP alongside each hostname; same one-click re-scan as the
  Certificate Transparency panel. No API key needed (free-tier daily quota).
- **RapidDNS subdomains** — passive subdomain enumeration via RapidDNS's public lookup page
  (DNS records aggregated from public passive-DNS sources), same one-click re-scan. No API key
  needed.
- **subfinder subdomains** — passive subdomain enumeration via subfinder (shelled out to as a
  subprocess), aggregating results across its keyless sources with per-subdomain source
  attribution. Unlike the other subdomain panels this runs on an explicit click rather than
  automatically, since a scan can take up to a minute. No API key needed.
- **Host Probe** — detects which of http/https is live for a domain via httpx (also shelled
  out to as a subprocess), reporting page title, server, detected technologies, favicon hash,
  and TLS certificate data - a useful next step after enumerating subdomains. Runs on an
  explicit click, since it connects directly to the domain rather than a third-party API.
  No API key needed.
- **Web Check** — four keyless site-hardening checks: TLS certificate inspection (issuer,
  validity, SAN, hostname match — verification is skipped so self-signed/expired/mismatched
  certificates are shown rather than refused), HTTPS security response headers (HSTS, CSP,
  X-Frame-Options, etc.), a DNSSEC signal (published DNSKEY/DS records), and a DNS blocklist
  check against several public providers' security-filtering resolvers (Cloudflare, Quad9,
  OpenDNS FamilyShield). No API key needed.
- **DNSDumpster** — DNS records enriched with ASN, geolocation, reverse DNS, and HTTP(S) banner
  fingerprints per resolved host, via DNSDumpster's official API. Needs its own free-tier API
  key (`dnsdumpster.com`), configured under Settings → API Keys; free tier caps results at 50
  records per domain, no domain-map image or pagination (those are Plus-tier only).
- **Wayback Machine** — lists archived snapshots of a domain via the Internet Archive's CDX API
  (one capture per day), with the capture count and date range, and a direct link to open each
  snapshot on web.archive.org. No API key needed.
- **Temporal Analysis** — aggregates WHOIS registration/expiry/update dates, the live TLS
  certificate's validity window, Wayback Machine first/last capture, and any `dateCreated`/
  `dateModified`/`datePublished` found in the homepage's schema.org JSON-LD into one chronological
  scatter timeline (domain/infrastructure events vs. page-content events), plus a sortable event
  list below it. Reuses the WHOIS/SSL/Wayback panels' own lookups rather than a separate API; a
  single source failing (e.g. no TLS listener) is shown as unavailable rather than failing the
  whole timeline. No API key needed.
- **Site Crawler** — crawls a domain's same-host pages/scripts (default up to 15 pages, depth 2)
  starting from its HTTPS homepage, following only same-host links, and runs every fetched page
  through the same IOC extraction engine as the standalone IOC Extractor above. Unlike the other
  Domain Finder panels this doesn't run automatically on every search — it makes several outbound
  requests per crawl, so it only starts on an explicit click. No API key needed.
