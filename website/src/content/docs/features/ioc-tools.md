---
title: IOC Tools
description: IOC lookup, extraction, defanging, domain finder, and WHOIS/CT tools.
sidebar:
  order: 20
---

A set of tools for working with indicators of compromise:

- **IOC Lookup** — analyze IPs, domains, URLs, hashes, emails, and crypto addresses against
  services like VirusTotal, AlienVault, AbuseIPDB, Shodan, Reddit, and Twitter/X. The IOC type is
  auto-detected. Crypto addresses (EVM and Bitcoin) are additionally screened against a
  self-hosted reputation blacklist built from the OFAC SDN sanctions list and ScamSniffer's open
  phishing-address dataset, refreshed daily in the background — no API key or third-party call
  needed for that specific check. Lookups can be done one at a time or in bulk.
- **History** — every single-IOC lookup is saved automatically once every queried service has
  responded, so past investigations stay reviewable. Any saved lookup can be exported as an HTML
  or PDF report — see [Reports & Exports](/corvid/architecture/reports/).
- **Newsfeed cross-reference** — a looked-up IOC is automatically checked against articles the
  [Newsfeed](/corvid/features/newsfeed/) module has already extracted IOCs from, surfacing any
  article that mentions the same indicator.
- **IOC Extractor** / **IOC Defanger** — pull IOCs out of free text, and fang/defang values for
  safe sharing (the command palette's `defang`/`fang <value>` shortcut does the same without
  opening this panel).
- **Domain Finder** — discover recently registered typosquat/phishing domains via URLScan.io,
  with screenshots and threat-intel cross-checks against the resolved IP. No API key needed
  beyond URLScan.io's own.
- **WHOIS/RDAP** — via the public `rdap.org` bootstrap redirector. No historical snapshots (no
  API key needed).
- **Certificate Transparency subdomain enumeration** — via crt.sh's public JSON log mirror,
  deduping SAN entries across all matching certificates; each discovered subdomain is one click
  away from re-running the Domain Finder typosquat search against it. No API key needed.
- **DNSDumpster** — DNS records enriched with ASN, geolocation, reverse DNS, and HTTP(S) banner
  fingerprints per resolved host, via DNSDumpster's official API. Needs its own free-tier API
  key (`dnsdumpster.com`), configured under Settings → API Keys; free tier caps results at 50
  records per domain, no domain-map image or pagination (those are Plus-tier only).
