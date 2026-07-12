![ost_logo](https://user-images.githubusercontent.com/44299200/210261186-1f0486a7-79e8-41b6-85f1-9e69915123aa.png)

# OSINT Toolkit
> **Warning**
> OSINT Toolkit is not production ready yet. This is an early prototype, that still needs some work to be done. 
## A fullstack web application built for security analysts

OSINT Toolkit is a self-hostable, on-demand analysis platform designed for security specialists. It consolidates various security tools into a single, easy-to-use environment, streamlining everyday tasks. Optimized for single-user operation, OSINT Toolkit runs locally in a Docker container and is not intended for long-term data storage or management. Instead, it focuses on accelerating daily workflows, such as news aggregation and analysis, IOC and email investigations, and the creation of threat detection rules. To further enhance efficiency, OSINT Toolkit integrates generative AI capabilities, providing additional support for analysis and decision-making. 


## Integrated services
| IPs            | Domains       | URLs                 | Emails           | Hashes     | CVEs     | Crypto Addresses |
|----------------|---------------|----------------------|------------------|------------|----------|------------------|
| AbuseIPDB      | Alienvault    | Alienvault           | Emailrep.io      | Alienvault | GitHub   | OFAC SDN (self-hosted) |
| Alienvault     | Checkphish.ai | Checkphish.ai        | GitHub           | GitHub     | NIST NVD | ScamSniffer (self-hosted) |
| Checkphish.ai  | GitHub        | GitHub               | Hunter.io        | Maltiverse |          |          |
| CrowdSec       | Maltiverse    | Google Safe Browsing | Have I Been Pwnd | Pulsedive  |          |          |
| GitHub         | Pulsedive     | Maltiverse           | Reddit           | Reddit     |          |          |
| IPQualityScore | Shodan        | Pulsedive            | Twitter          | ThreatFox  |          |          |
| Maltiverse     | ThreatFox     | Shodan               |                  | Twitter    |          |          |
| Pulsedive      | Reddit        | ThreatFox            |                  | Virustotal |          |          |
| Shodan         | Twitter       | Reddit               |                  |            |          |          |
| Reddit         | URLScan       | Twitter              |                  |            |          |          |
| ThreatFox      | Virustotal    | URLScan              |                  |            |          |          |
| Twitter        |               | Virustotal            |                  |            |          |          |
| Virustotal     |               |                      |                  |            |          |          |

> Crypto address checks (EVM and Bitcoin) run against a self-hosted blacklist built from the
> OFAC SDN sanctions list and ScamSniffer's open phishing-address dataset — no API key or
> third-party calls required, refreshed daily in the background.

## Features
### Newsfeed
The Newsfeed module keeps you up to date about the latest cybersecurity news by aggregating articles from trusted sources such as Wired, The Hacker News, Security Magazine, Threatpost, TechCrunch Security, and Dark Reading. Stay up-to-date with industry trends and potential threats without having to visit multiple websites or subscribe to numerous newsletters. The module extracts IOCs automatically from the news articles and lets you analyze news in no time using AI.
<img width="1679" height="1084" alt="newsfeed" src="https://github.com/user-attachments/assets/0c23cc14-4a1a-4c34-9fb8-5064a0f23889" />


### IOC Tools
The IOC Tools module helps you analyze different types of indicators of compromise (IOCs) such as IP addresses, hashes, email addresses, domains, URLs, and crypto addresses (EVM and Bitcoin). It leverages services like VirusTotal, AlienVault, AbuseIPDB, and social media platforms like Reddit and Twitter to gather information about the IOCs. Crypto addresses are screened against a self-hosted reputation blacklist built from the OFAC SDN sanctions list and ScamSniffer's open phishing-address dataset, refreshed daily — no API key or third-party calls needed for this check. The module automatically detects the type of IOC being analyzed and utilizes the appropriate services to provide relevant information, enabling you to identify potential threats and take necessary actions to protect your organization. Analysis can be done individual per IOC or in bulk. Also fanging and defanging is possible for sharing IOCs safely.
<img width="1679" height="1102" alt="ioc_lookup" src="https://github.com/user-attachments/assets/40b1e656-ba6c-4f36-b8dd-beee0dca3fdd" />


### Email Analyzer
The Email Analyzer module allows you to analyze .eml files for potential threats. Simply drag and drop an .eml file into the module, and it will parse the file, perform basic security checks, extract indicators of compromise (IOCs), and analyze messages with the help of AI. Analyze the IOCs using various open-source intelligence (OSINT) services, and enhance your organization's email security.


### Image Tools
The Image Tools module lets you inspect an image file for OSINT purposes. Upload a picture to see every piece of metadata it carries — EXIF camera/device info, capture timestamp, GPS location with a map link, embedded thumbnail, file properties, and MD5/SHA1/SHA256 hashes. You can also kick off a reverse image search without any API keys: provide the image's URL to get deep links straight into Google Lens, Yandex, Bing, and TinEye, or use the same buttons to open each engine for a manual upload.


### Domain Finder
The Domain Finder module helps you to protect your organization from phishing attacks by searching for recently registered domains that match specific patterns. By utilizing the URLScan.io API, you can view screenshots of websites associated with domains without visiting them directly. Additionally, you can check each domain and its resolved IP against multiple threat intelligence services, further enhancing your organization's security.


### AI Templates
The AI Templates module provides powerful AI-based solutions for log data analysis, email text analysis, and source code explanation. It lets you create templates for AI tasks and supports you in the prompt engineering process.
<img width="1679" height="1102" alt="ai_templates" src="https://github.com/user-attachments/assets/42c52c8c-7d2d-4b70-b25c-666d6993832c" />


### CVSS Calculator
The CVSS Calculator module allows you to calculate the CVSS 3.1 score of a vulnerability and export the calculation as a markdown or JSON file.


### Detection Rules
The Detection Rules module is a GUI for creating Sigma, Yara and Snort/Suricate rules.


### Reddit Search
The Reddit Search module finds a Reddit user's full post and comment history, including content removed by moderators or deleted by its author, by querying the public Arctic Shift and PullPush archive APIs in parallel — no API key required. Filter by subreddit, date range, or NSFW status, and page through results by post or comment. Each search is saved to history so you can revisit it later.



## Deploy with docker
1. Download the repository and extract the files
2. Navigate to the directory where the `docker-compose.yaml` file is located
3. Start the application:
   - `make up` — start backend and frontend without rebuilding
   - `make rebuild` — rebuild images (e.g. after dependency or Dockerfile changes) and start
   - `make up-backend` / `make up-frontend` — start a single service without rebuilding
   - `make rebuild-backend` / `make rebuild-frontend` — rebuild and start a single service
4. Once the container is running, you can access the application in your browser at http://localhost:4000

In case the database schema changed, run a migration before starting the container:
`docker compose run --rm backend alembic upgrade head`

### Access token

The app has no user accounts, so it's protected by a single access token instead of a login form.
On first startup, a token is generated automatically and printed to the backend logs
(`docker compose logs backend`) and saved to `data/.access_token` on the host. Open
http://localhost:4000, and you'll be asked to paste that token once — it's then remembered in
the browser.

To set your own fixed token instead of the auto-generated one, set `API_ACCESS_TOKEN` in `.env`
before starting the container.

### Configuration

Copy [`.env.example`](.env.example) to `.env` to override any setting (all of them have working
defaults, so this is optional). `.env` is read automatically by `docker compose up`.

### Operational security notes

This tool talks to third-party services (VirusTotal, Shodan, target mail servers via
`email_search`'s SMTP checks, etc.) using your own infrastructure's IP, and stores investigation
history in a local database. Some practices worth following, especially for sensitive engagements:

- **Isolate the instance.** Run it on a dedicated VM/VPS or an isolated host, not your daily-driver
  machine — a target under investigation can potentially see inbound lookups against them.
- **Route sensitive lookups through Tor/a proxy.** `email_search` supports `use_tor`/`proxy_url`,
  and `username_search`'s maigret source has its own proxy setting, for when a target could
  plausibly monitor who's probing them.
- **Never enable `SECURITY_ALLOW_PRIVATE_NETWORK_TARGETS` outside dev/testing** — it's a direct
  SSRF opt-out.
- **Segment and rotate API keys** per engagement where the provider supports multiple keys, so a
  compromised key from one case doesn't expose others.
- **Don't cross-contaminate identities.** Some features (e.g. Image Tools' reverse-search
  deep-links) open external services directly in your browser — use a separate, logged-out
  browser profile for sensitive lookups so they don't tie back to your personal accounts.

## License

OSINT Toolkit is licensed under the [GNU Affero General Public License v3.0](LICENSE).

You are free to use, modify, and distribute this software, provided that any
modified versions or services built on it are also made available under AGPL-3.0,
including when offered as a network service.

### Commercial Licensing

If AGPL-3.0 doesn't fit your use case — for example, if you want to integrate
OSINT Toolkit into a proprietary product or offer it as a managed service without
open-sourcing your modifications — a commercial license is available.

Contact: [contact@osint-toolkit.com]

### Prior Versions

Versions up to and including v0.1.0 were released under the MIT License and
remain available under those terms.