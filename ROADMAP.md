# Corvid — Improvement Roadmap

Ideas for hardening the project across four angles: performance, UI/UX, security, and resilience (fault tolerance) —
plus a backlog of new OSINT capabilities: tool/site integrations, cross-feature data aggregation, and routine automation.
This is a backlog, not a commitment — pick items opportunistically. Grounded in the current architecture described in `CLAUDE.md`; re-check file/line references before acting since the code will keep moving.

Effort tags: **S** = small/quick win, **M** = medium, **L** = larger effort/design work.

## New OSINT Features

Ideas for expanding investigative capability itself, rather than hardening what already exists.

### Tool & site integrations

- **[M] Certificate Transparency subdomain enumeration (crt.sh).** No API key needed — query crt.sh's JSON endpoint (`?q=%25.<domain>&output=json`) to enumerate subdomains and cert issuance history for a domain. Natural fit inside `domain_finder`, feeding its existing typosquat/phishing discovery flow with a subdomain list to also scan.
- **[M] Wayback Machine / archive.org integration.** Given a URL or domain, pull the list of archived snapshots (`web.archive.org/cdx/search/cdx`) and let the analyst open a historical snapshot — useful for viewing a phishing page's content after it's been taken down. Fits as a `domain_finder` panel or a standalone small feature; must go through `ssrf_guard.safe_get` like every other outbound fetch, since the target URL is user-supplied.
- **[M] Finish wiring Censys.** `ioc_tools/ioc_lookup/config/rate_limiting_config.py` already reserves a rate-limit slot for Censys, but no provider function is actually registered anywhere in `ioc_lookup`. Add the API client (host/certificate search) alongside Shodan in `external_api_clients.py` and register it in `service_registry.py` for IP/domain lookups.
- **[L] Breach/leak search beyond HIBP.** Current email-breach coverage is HIBP only (one of several email providers in `ioc_lookup`). Add DeHashed and/or LeakCheck/IntelligenceX as additional providers — these also support username/domain/password-hash search, which HIBP doesn't. Could extend `ioc_lookup`'s email type, or become a small dedicated "breach search" feature reusing the same `routers`/`service`/`crud` layering as other features.
- **[M] Passive DNS / DNS record dump.** No DNS tooling exists today beyond IOC lookup incidentally hitting Shodan/OTX's own DNS-adjacent endpoints. Add a small DNS utility (A/AAAA/MX/TXT/NS/CNAME dump via `dnspython`, plus reverse DNS) as a `domain_finder` panel or its own lightweight feature — good S/M-effort starting point since resolution is done directly, no paid passive-DNS provider required.
- **[M] Git identity correlation (gitcolombo).** Integrate [Soxoj/gitcolombo](https://github.com/Soxoj/gitcolombo) (MIT, stdlib-only) as a new `git_recon` feature, same `routers`/`service`/`crud` layering as `reddit_search`. Two modes: `--search <username>` (API-only — `/users/{u}/gpg_keys` + `/search/commits?q=author:{u}`, no cloning) and `-u <url>` / `--nickname <user>` (clones repo(s), correlates author/committer identities across `git log --all`, resolves GitHub logins by scraping commit pages). Reuses the existing `github_pat` API key (`core/settings/api_keys`) rather than a new setting. Needs: `git` binary added to `backend/Dockerfile` (not currently installed); a strict `https://github.com/<owner>/<repo>` allowlist validator in front of `git clone`'s subprocess call, since it accepts arbitrary URL schemes and `ssrf_guard.safe_get` only covers `httpx` clients, not subprocess argv; ephemeral clone dir with `rmtree` cleanup per scan (not the persisted `data/` mount); a repo-count cap + wall-clock ceiling mirroring `email_search`'s `PROCESS_WATCHDOG_SECONDS`. Drop the library's local-directory scan mode (`-d`/`-r`) — no server-filesystem browser in this app, and it's needless attack surface.
- **[M] Paste-site monitoring using the existing keyword list.** `core/settings/keywords/` is currently consumed only by `newsfeed/service/feed_processing_service.py` to flag relevant articles. Add a scheduled job (same APScheduler pattern newsfeed already uses) that periodically queries a paste-site search API (e.g. PSBDMP, or Pastebin's paid scraping API) for the same keyword list and surfaces hits the same way newsfeed does — reuses an existing settings module instead of introducing a new one.

### Data aggregation

- **[L] "Investigation" / target-profile entity.** The biggest structural gap: `username_search`, `email_search`, `reddit_search`, `ioc_lookup`, and `email_analyzer` each persist their own independent history table, with nothing tying them together. Introduce an `Investigation` model (id + label + created_at + a loose set of linked search IDs across the existing history tables) so an analyst can group "everything found about this username/email/domain" into one view, and generate a single combined report via the existing generic `core/reports/` renderer instead of separate per-feature reports.
- **[S] Cross-reference newsfeed IOCs against ioc_lookup history.** `newsfeed`'s IOC extraction/MITRE mapping runs independently of anything the analyst has manually looked up in `ioc_lookup`. Add a check (on newsfeed ingest, or on ioc_lookup search) that flags when an IOC appears in both, surfacing "this indicator was also seen in a recent newsfeed article" — a cheap correlation using data both features already collect.

### Routine automation

- **[L] Watchlist / recurring re-scan with alerts.** Every current scan (username_search, email_search, ioc_lookup, reddit_search) is one-shot and manual. Reuse newsfeed's per-feed APScheduler + health-tracking pattern to let an analyst pin a username/domain/IOC to a recurring interval, diff new results against the last run, and push a notification through the existing `alerts/` WebSocket when something new shows up — turns the tool from "look it up now" into "tell me when it changes."

## Performance

- **[M] Missing indexes on hot lookup paths.** Worth auditing: `SingleLookupSearch`/`SingleLookupResult`, `MaigretSearch`/`MaigretSiteResult`, `RedditSearchResult` (unique on `search_id`+`kind`+`reddit_id` — is that backed by an actual index, or just an app-level check?), and newsfeed article tables queried by the trends/analytics feature. Add indexes on FK columns and any column used in `ORDER BY`/`WHERE` for history listing endpoints.
- **[M] Newsfeed IOC/MITRE extraction cost.** If article IOC extraction and MITRE ATT&CK mapping run synchronously inline on ingest for every fetched article, consider whether it should be a separate APScheduler-driven batch step so a slow regex/NLP pass doesn't block the fetch cycle.

## UI / UX


## Security

- **[M] SQLite file permissions & backup story.** `data/corvid.db` holds encrypted API keys but the encryption key itself (`<data_dir>/.encryption_key`) and access token (`<data_dir>/.access_token`) live next to it on the same bind mount. Document (README) that backing up `data/` without also protecting host filesystem permissions defeats the encryption-at-rest story — the key travels with the ciphertext.
- **[M] Rate limiting granularity.** Current `slowapi` limiter (`120/minute`, `5000/hour`) is IP-keyed and global-default. Since this is single-user/self-hosted, the bigger risk is one compromised browser tab or a buggy frontend retry loop hammering an external provider (AbuseIPDB/VirusTotal/Shodan) through your own backend and burning API quota / triggering the provider's own abuse detection — consider a secondary per-provider rate limit/backoff in the IOC lookup service layer, independent of the inbound `slowapi` limiter.
- **[S] Secrets-adjacent log redaction test coverage.** `SecretRedactionFilter` (`log_redaction.py`) is pattern-based and "covers new providers automatically" per `CLAUDE.md` — worth a small regression test per documented pattern (query-param keys, `Bearer` tokens, IPQualityScore path-embedded key) so a refactor of logging config can't silently drop the filter without a test failing.

## Resilience / Fault tolerance

Done: subprocess resilience, per-feed fetch health, and disk-space warnings (see `CLAUDE.md` for the current shape of each). Remaining ideas:

- **[S] Disk-space threshold configurability.** `LOW_DISK_SPACE_THRESHOLD_BYTES` (`core/dependencies.py`) is a hardcoded 1 GiB. Fine for now, but if a deployment legitimately runs closer to the edge (small VPS), consider making it an env-configurable `AppSettings` field instead of a constant.
