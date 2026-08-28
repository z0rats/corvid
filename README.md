
# Corvid

[![CI](https://github.com/z0rats/corvid/actions/workflows/ci.yml/badge.svg)](https://github.com/z0rats/corvid/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/z0rats/corvid/branch/main/graph/badge.svg)](https://codecov.io/gh/z0rats/corvid)
[![OpenSSF Scorecard](https://api.securityscorecards.dev/projects/github.com/z0rats/corvid/badge)](https://securityscorecards.dev/viewer/?uri=github.com/z0rats/corvid)

📖 [Documentation](https://z0rats.github.io/corvid/)

_Originaly Corvid started as a fork of [dev-lu/osint_toolkit](https://github.com/dev-lu/osint_toolkit) with
an updated stack, and has since diverged substantially._

## One search bar for everything you look up today

If your daily routine is a wall of browser tabs — VirusTotal in one, Shodan in another, three more for a username or a phishing domain — Corvid replaces that wall with a single keyboard-first search bar. Paste an IP, domain, hash, email, or username and it's routed to the right tools automatically; type a tool name to jump straight to it.

Corvid is self-hostable and built for single-user operation: it runs in one Docker container on your own infrastructure, so investigation data and API keys never pass through a third-party SaaS. It's a workbench, not a data warehouse — no long-term case management, just fast, on-demand IOC lookups, email/image forensics, phishing-domain discovery, identity correlation (Reddit, GitHub, usernames), and detection-rule authoring, with generative AI wired in to speed up analysis and write-ups along the way.

```bash
curl -fsSL https://raw.githubusercontent.com/z0rats/corvid/main/install.sh | bash
```

Pulls pre-built images and starts the app at http://localhost:4000 — no auto-update, see
[Deploy with docker](#deploy-with-docker) for details and the build-from-source alternative.

## Contents

- [Integrated services](#integrated-services)
- [Features](#features)
- [Keyboard-first navigation](#keyboard-first-navigation)
- [Deploy with docker](#deploy-with-docker)
- [Disclaimer](#disclaimer)
- [License](#license)

## Integrated services

IOC lookups auto-route to the right services based on the type you paste in:

- **IPs** — AbuseIPDB, AlienVault, CheckPhish.ai, CrowdSec, GitHub, IPQualityScore, LeakIX, Maltiverse, Pulsedive, Reddit, Shodan, ThreatFox, Twitter/X, VirusTotal
- **Domains** — AlienVault, CheckPhish.ai, GitHub, Library of Leaks, Maltiverse, Pulsedive, Reddit, Shodan, ThreatFox, Twitter/X, URLScan, VirusTotal
- **URLs** — AlienVault, CheckPhish.ai, GitHub, Google Safe Browsing, Maltiverse, Pulsedive, Reddit, Shodan, ThreatFox, Twitter/X, URLScan, VirusTotal
- **Emails** — Emailrep.io, GitHub, Have I Been Pwned, Hunter.io, Library of Leaks, Reddit, Twitter/X
- **Hashes** — AlienVault, GitHub, Maltiverse, Pulsedive, Reddit, ThreatFox, Twitter/X, VirusTotal
- **CVEs** — GitHub, NIST NVD
- **Crypto addresses** (EVM & Bitcoin) — screened against a self-hosted blacklist built from the OFAC SDN sanctions list and ScamSniffer's open phishing-address dataset, refreshed daily in the background; no API key or third-party calls required

## Features

Full write-up of every module (settings, gotchas, endpoints) lives on the
[docs site](https://z0rats.github.io/corvid/) — this is the short version.

### Newsfeed
Aggregates cybersecurity news from trusted sources, extracts IOCs automatically, and analyzes
articles with AI. → [Docs](https://z0rats.github.io/corvid/features/newsfeed/)
<img width="1679" height="1084" alt="newsfeed" src="https://github.com/user-attachments/assets/0c23cc14-4a1a-4c34-9fb8-5064a0f23889" />


### IOC Tools
Analyze IPs, domains, URLs, hashes, emails, and crypto addresses against VirusTotal, AlienVault,
AbuseIPDB, Shodan, and more, single or in bulk, plus Domain Finder (WHOIS/RDAP, Certificate
Transparency, HackerTarget/RapidDNS subdomains, Wayback history, and a keyless Web Check panel —
TLS cert, security headers, DNSSEC, DNS blocklist). → [Docs](https://z0rats.github.io/corvid/features/ioc-tools/)
<img width="1679" height="1102" alt="ioc_lookup" src="https://github.com/user-attachments/assets/40b1e656-ba6c-4f36-b8dd-beee0dca3fdd" />


### Email Analyzer
Parse `.eml` files, run header/security checks, extract IOCs, and get an AI-assisted read on
suspicious messages. → [Docs](https://z0rats.github.io/corvid/features/email-analyzer/)

### Image Tools
Inspect EXIF/GPS/hash metadata, reverse-image search with no API keys, an optional AI photo
geolocation hypothesis, and an opt-in ChronoVerify provenance/C2PA check. →
[Docs](https://z0rats.github.io/corvid/features/image-tools/)

### AI Templates
Reusable AI prompt templates for log analysis, email analysis, and source-code explanation. →
[Docs](https://z0rats.github.io/corvid/features/llm-templates/)
<img width="1679" height="1102" alt="ai_templates" src="https://github.com/user-attachments/assets/42c52c8c-7d2d-4b70-b25c-666d6993832c" />

### CVSS Calculator
Score a vulnerability with CVSS 3.1 or 4.0 and export it. →
[Docs](https://z0rats.github.io/corvid/features/cvss-calculator/)

### Detection Rules
A GUI for creating Sigma, Yara, and Snort/Suricata rules. →
[Docs](https://z0rats.github.io/corvid/features/rule-creator/)

### Reddit Search
A Reddit user's full post/comment history, including removed/deleted content, no API key
required. → [Docs](https://z0rats.github.io/corvid/features/reddit-search/)

### Username & Email Search
Find accounts and mail providers registered to a username, across hundreds of sites. →
[Username Search docs](https://z0rats.github.io/corvid/features/username-search/) /
[Email Search docs](https://z0rats.github.io/corvid/features/email-search/)

### Git Recon
Correlate names, emails, and GitHub logins from commit history via
[gitcolombo](https://github.com/Soxoj/gitcolombo). →
[Docs](https://z0rats.github.io/corvid/features/git-recon/)

### Dork Runner
Run parameterized search-engine dorks against a domain, username, or email. →
[Docs](https://z0rats.github.io/corvid/features/dork-runner/)

### RU Business Check
Due-diligence check on a Russian legal entity or sole proprietor by ИНН/name — ЕГРЮЛ/ЕГРИП
extract, disqualified-persons registry check, and arbitration case history, no API key required.
Russian-only UI. → [Docs](https://z0rats.github.io/corvid/features/ru-business-check/)

### Browser Extension
A minimal Chrome extension ("Corvid Quick Send") lets you select text on any page and send it
straight to IOC Tools lookup, with no build step — load it unpacked from the
[`extension/`](extension/) folder. →
[Docs](https://z0rats.github.io/corvid/features/browser-extension/)


## Keyboard-first navigation

Corvid is built around a single search bar instead of hunting through menus — press `/` or
`⌘K`/`Ctrl+K` from anywhere to open it. Paste a raw IOC value to get routed to the right tool,
type a tool's name to jump to it, or combine both (`john_doe reddit`) to open a tool pre-filled.
See the [Command Palette docs](https://z0rats.github.io/corvid/usage/command-palette/) for the
full grammar (tags, filters, quick actions, defang/fang, playbooks).


## Deploy with docker

### System requirements

- Docker Engine 24+ with the Docker Compose v2 plugin (the `docker compose` command, not the legacy standalone `docker-compose` binary)
- Linux, macOS, or Windows (via Docker Desktop/WSL2)
- At least ~1 GB free disk for the app itself; more if you enable `email_search`'s optional headless checkers, which lazily download a Chromium binary (~150-300 MB) on first use — see [Disk usage](https://z0rats.github.io/corvid/getting-started/backup-and-operations/#disk-usage)
- Outbound HTTPS access for the third-party services you configure (VirusTotal, Shodan, etc.) — no inbound ports need to be exposed
- No GPU or special hardware needed. CPU/RAM haven't been formally benchmarked, but as a single-user tool with no background crawling by default, it's light — a small VM (1-2 vCPU, 2 GB RAM) is comfortable for typical use

### Install

**Option A — one-line install (pre-built images).** Pulls ready-made images from GHCR instead of
building from source. Installs into `~/corvid` by default (override with `CORVID_DIR`):

```bash
curl -fsSL https://raw.githubusercontent.com/z0rats/corvid/main/install.sh | bash
```

Once it's running, open http://localhost:4000. There's no auto-update — new versions aren't
pulled without your say-so. To update later, run `./update.sh` from the install directory (it
pulls the latest images and recreates the containers).

**Option B — build from source.** Gives you a local build instead of pulling from a registry, and
lets you review the Dockerfiles before anything runs:

1. Download the repository and extract the files
2. Navigate to the directory where the `docker-compose.yaml` file is located
3. Start the application:
   - `make up` — start backend and frontend without rebuilding
   - `make rebuild` — rebuild images (e.g. after dependency or Dockerfile changes) and start
   - `make up-backend` / `make up-frontend` — start a single service without rebuilding
   - `make rebuild-backend` / `make rebuild-frontend` — rebuild and start a single service
   - `make help` — list all available targets, including `down`/`logs`/`ps`/`migrate`
4. Once the container is running, you can access the application in your browser at http://localhost:4000

Database migrations run automatically on container startup — no manual step needed after
`make rebuild`. If you need to run one by hand (e.g. to check for pending migrations without
starting the app), you can still run: `make migrate`

### Access token

The app has no user accounts, so it's protected by a single access token instead of a login form.
On first startup, a token is generated automatically and printed to the backend logs
(`make logs`) and saved to `data/.access_token` on the host. Open
http://localhost:4000, and you'll be asked to paste that token once — it's then remembered in
the browser.

To set your own fixed token instead of the auto-generated one, set `API_ACCESS_TOKEN` in `.env`
before starting the container.

### Configuration

Copy [`.env.example`](.env.example) to `.env` to override any setting (all of them have working
defaults, so this is optional). `.env` is read automatically by `docker compose up`. Per-service
API keys and app-level preferences are configured from within the app itself instead — see
[Settings Reference](https://z0rats.github.io/corvid/getting-started/settings-reference/).

### Backup, disk usage & operational security

Settings → Backup lets you download/restore a full backup (database + encryption key,
optionally passphrase-encrypted) from the browser, no shell access needed. Covered in depth on
the docs site: [Backup & Operational Security](https://z0rats.github.io/corvid/getting-started/backup-and-operations/)
— what's under `data/`, the in-app flow vs. a manual host-level backup, disk-usage expectations,
and practices worth following for sensitive engagements (isolating the instance, routing through
Tor/a proxy, key rotation, and more).

## Disclaimer

Corvid is a tool, not a policy — how you point it is on you. It's built for legitimate use
cases: internal security teams triaging IOCs, threat intel analysts enriching indicators,
researchers investigating abuse, and similar authorized work. It is not built for stalking,
harassment, unauthorized surveillance, or investigating people without a lawful basis for
doing so.

Several modules (Reddit Search, Git Recon, Image Tools' reverse-search, email/username
lookups) pull together data that's technically public but can still identify or locate a
real person when combined. Before running them against an individual rather than an IOC or
organization, make sure you have a legitimate basis to do so and that it complies with the
laws of your jurisdiction and the target's (data protection/privacy law, computer-misuse
law, and your organization's own policies, at minimum). Some integrated services carry
their own terms of use and rate limits that are yours to respect — Corvid doesn't police
that for you.

None of this constitutes legal advice, and the author takes no responsibility for how the
tool ends up being used. When in doubt, check with your legal/compliance function before
running an investigation, not after.

## License

Corvid is licensed under the [GNU Affero General Public License v3.0](LICENSE).

You are free to use, modify, and distribute this software, provided that any
modified versions or services built on it are also made available under AGPL-3.0,
including when offered as a network service.

### Commercial Licensing

If AGPL-3.0 doesn't fit your use case — for example, if you want to integrate
Corvid into a proprietary product or offer it as a managed service without
open-sourcing your modifications — a commercial license is available.

Contact: [z0rats.dev@gmail.com]

### Prior Versions

Versions up to and including v0.1.0 were released under the MIT License and
remain available under those terms.
