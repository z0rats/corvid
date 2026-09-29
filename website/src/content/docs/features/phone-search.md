---
title: Phone Search
description: Check whether a phone number is registered with Amazon, Microsoft, or Facebook.
sidebar:
  order: 180
---

Checks a single E.164 phone number (e.g. `+15551234567`) against Amazon, Microsoft, and Facebook's
own sign-in/account-recovery flows, the same "single credential, many providers" pattern as
[Email Search](/corvid/features/email-search/) and [Username Search](/corvid/features/username-search/) -
except the checkers are Corvid's own in-house implementations rather than a wrapped third-party
tool, since no suitable Python package existed. Progress streams live as each provider is checked,
and found providers are saved to history.

Checks one phone number per scan, not built for bulk enumeration - the same deliberate scope limit
as [gophoner](https://github.com/M4elstr0m/gophoner), the tool this feature's approach was inspired
by.

## Limitations

Amazon and Facebook's checkers scrape each vendor's current sign-in/account-recovery page rather
than a documented API, so they can break silently if either vendor changes their page layout.
Microsoft's checker instead uses `login.live.com`'s `GetCredentialType.srf` endpoint, the same
public, well-documented technique several other Microsoft-account-enumeration tools rely on -
of the three, it's the least likely to drift.

None of the three checkers spoof a browser-realistic TLS/JA3 fingerprint, so they're more easily
rate-limited or blocked than a real browser would be. A proxy can be configured under
**Settings → Phone Search** to route around this.
