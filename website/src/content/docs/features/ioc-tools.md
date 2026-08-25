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
- **Library of Leaks** — checks a domain or email against a public, keyless Aleph instance
  (run by DDoSecrets/investigativedata.io) indexing tens of millions of records across dozens of
  breach/leak collections. Only per-collection hit counts are shown — never the matching
  documents' own content — with a link out to review the source material on Library of Leaks
  itself. Bulk lookup isn't offered for it, to stay within the shared anonymous rate limit of
  this free, non-profit service.
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
- **Certificate Transparency subdomain enumeration** — via crt.sh's public JSON log mirror,
  deduping SAN entries across all matching certificates; each discovered subdomain is one click
  away from re-running the Domain Finder typosquat search against it. No API key needed.
- **HackerTarget subdomains** — passive subdomain enumeration via HackerTarget's free
  `hostsearch` API, resolved IP alongside each hostname; same one-click re-scan as the
  Certificate Transparency panel. No API key needed (free-tier daily quota).
- **RapidDNS subdomains** — passive subdomain enumeration via RapidDNS's public lookup page
  (DNS records aggregated from public passive-DNS sources), same one-click re-scan. No API key
  needed.
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
