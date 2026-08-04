---
title: Security
description: Access control, SSRF protection, and secrets handling.
---

Corvid is not production-hardened (early prototype, per the README) — treat the notes below as
what the app does today, not a guarantee for every deployment scenario. See the README's
[Operational security notes](https://github.com/z0rats/corvid#deploy-with-docker) for deployment
guidance.

## Access control

No user accounts — the app is single-user. Every `/api/*` route is guarded behind one shared
bearer token (`API_ACCESS_TOKEN`, or auto-generated and persisted to `data/.access_token` on
first startup). `/docs`, `/redoc`, and `/openapi.json` are covered too. The healthcheck endpoint
and the alerts WebSocket handshake are the only exceptions (the WebSocket checks the same token
via a query param, since browsers can't set a custom header on the handshake).

## Secrets at rest

Per-service API keys (VirusTotal, Shodan, Hunter.io, etc.) are encrypted at rest with a Fernet
key, either provided via `SECURITY_ENCRYPTION_KEY` or auto-generated at
`data/.encryption_key`. Losing that file makes stored keys unrecoverable — back it up alongside
the database.

## SSRF protection

Any backend code that fetches a user-supplied or externally-sourced URL goes through a shared
SSRF guard that resolves and validates the hostname before the request is made, rejecting
private/loopback/link-local/reserved IPs, and re-validates every redirect hop. This covers
favicon downloads, newsfeed fetching, LLM-template web content, and domain WHOIS/RDAP redirects.

## Dependency and code scanning

CI runs `pip-audit`/`yarn npm audit` and Trivy for dependency and image CVEs, plus CodeQL (SAST)
and gitleaks (secret scanning) as blocking checks on every push. Dependabot opens weekly update
PRs for pip, npm/yarn, Docker, and GitHub Actions, each with a cooldown period.
