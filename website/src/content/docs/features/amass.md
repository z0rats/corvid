---
title: Amass
description: Active DNS enumeration and ASN/netblock discovery via OWASP Amass.
sidebar:
  order: 160
---

Active reconnaissance against a domain via [OWASP Amass](https://github.com/owasp-amass/amass) —
DNS enumeration across its passive data sources, with optional wordlist brute-forcing, plus
ASN/netblock discovery. Unlike a passive lookup, this makes real DNS queries against the
target's own infrastructure — reserve it for domains you're authorized to actively probe.

A scan runs in the background and streams progress live rather than blocking the request,
since active enumeration can take several minutes; it can be cancelled at any point, keeping
whatever was discovered up to that point. Wordlist brute-forcing (off by default) is slower and
noisier — real DNS queries per candidate subdomain — so enable it only when you specifically
want that coverage.

Findings accumulate across every scan of the same domain rather than resetting each run: a
repeat scan reflects everything discovered so far for that domain, not just what changed in the
latest run. Past scans, including their full host/IP results, are kept under **History**.
