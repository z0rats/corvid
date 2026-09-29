# Phone Search reimplements its checkers in-house rather than wrapping gophoner

Phone Search (single E.164 phone number, checked against Amazon/Microsoft/Facebook's
sign-in/account-recovery flows) reproduces the technique of
[gophoner](https://github.com/M4elstr0m/gophoner), a Go CLI that does the same thing across a
wider provider set. Two decisions were made before writing any code: not to wrap or vendor
gophoner itself, and to ship only the three providers whose checks are plain HTTP, deferring the
two that need a headless browser.

## Not vendoring gophoner: license and language

gophoner is licensed under the PolyForm Internal Use License 1.0.0, which explicitly prohibits
redistributing it or a modified version of it to anyone else, and prohibits offering it as a
hosted/managed service. Corvid's `release.yml` builds and publishes multi-arch backend/frontend
images to GHCR on every tag; baking gophoner's binary into that published image would redistribute
it to every Corvid user who pulls the image, which the license does not permit. Even setting the
license aside, gophoner is a Go binary shelled out to from a Python codebase - inconsistent with
every other scan-style feature here (`email_search`, `username_search`'s maigret source, `git_recon`),
which run in-process.

Its README, technique description (`is_registered.go` per provider), and each provider's own
public sign-in/account-recovery surface were read to understand *what* each checker does; no
gophoner source was copied into this codebase. `amazon_checker.py`/`microsoft_checker.py`/
`facebook_checker.py`'s actual request/response handling is this project's own implementation,
following this codebase's existing scan-style feature layout (`email_search`'s checker-module
pattern), not gophoner's.

## Google/OpenAI deferred: they need a headless browser, HTTP alone doesn't work

gophoner's Amazon/Microsoft/Facebook checkers are plain HTTP flows; its Google and OpenAI checkers
instead drive a full headless Chrome (`chromedp`), since both providers' identifier-first sign-in
pages are too JS-heavy/bot-gated for a bare HTTP client. Shipping only the three HTTP-only checkers
first, gated behind nothing extra, and deferring Google/OpenAI to a later phase (via `pyppeteer`,
already an optional dependency of `email_search`'s headless checkers and `image_tools`, gated the
same way `email_search` gates its own `enable_headless_checks`) keeps the first version's
dependency footprint and failure surface small, and matches the project's general preference for
shipping the low-risk slice of a feature before its higher-maintenance half.

## Scraping fragility is accepted, not solved

Amazon and Facebook's checkers scrape each vendor's current sign-in/account-recovery page rather
than a documented API - unlike Microsoft's `GetCredentialType.srf`, which is a stable, publicly
documented endpoint several other Microsoft-account-enumeration tools already rely on. Amazon's
and Facebook's exact form field names and "not found" text markers were written from a best-effort
read of each page's current shape, not verified against live requests during development (making
speculative probe requests against real third-party account-recovery endpoints without a concrete
authorized target wasn't judged appropriate), and may need adjustment once exercised against the
live pages. This mirrors this project's existing posture toward other best-effort scrapers
(`dork_runner`'s search engines, `domain_finder`'s panels) rather than a new risk: it's called out
explicitly in `website/src/content/docs/features/phone-search.md` and each checker module's own
docstring so a future drift is a documentation-pointed fix, not a surprise.

## Single-target scope, by design

Like gophoner itself ("architecturally scoped to reduce abuse potential... not built for bulk
enumeration"), Phone Search's `/api/phone-search/scan` checks one phone number per request. This
is a deliberate scope limit carried over from the tool that inspired this feature, not an
oversight to be lifted later - repeatedly probing account-recovery flows for many numbers in
sequence is a meaningfully different (and more abuse-prone) capability than checking one number
an analyst already has in hand.
