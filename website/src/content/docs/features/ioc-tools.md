---
title: IOC Tools
description: IOC lookup, extraction, defanging, domain finder, and WHOIS/CT tools.
---

A set of tools for working with indicators of compromise:

- **IOC Lookup** — analyze IPs, domains, URLs, hashes, emails, and crypto addresses against
  services like VirusTotal, AlienVault, AbuseIPDB, Shodan, Reddit, and Twitter/X. The IOC type is
  auto-detected. Crypto addresses (EVM and Bitcoin) are additionally screened against a
  self-hosted reputation blacklist built from the OFAC SDN sanctions list and ScamSniffer's open
  phishing-address dataset — no API key needed for that check. Single-lookup searches are saved
  to history automatically; bulk lookups are also supported.
- **IOC Extractor** / **IOC Defanger** — pull IOCs out of free text, and fang/defang values for
  safe sharing.
- **Domain Finder** — discover recently registered typosquat/phishing domains via URLScan.io,
  with screenshots and threat-intel cross-checks against the resolved IP.
- **WHOIS/RDAP** and **Certificate Transparency** panels — no API key required for either.
