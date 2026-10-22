# Certificate Transparency subdomains come from crt.sh and Cert Spotter merged into one panel

crt.sh was the only Certificate Transparency source in `domain_finder`, and it is often
overloaded (it serves an HTML error page instead of JSON, which the crt.sh canary already has to
retry around). While it was down, the CT panel showed only an error. SSLMate's Cert Spotter has a
keyless issuances API that returns the same kind of data. Checked live on 2026-10-22:
`GET api.certspotter.com/v1/issuances?domain=<d>&include_subdomains=true&expand=dns_names`
returns a JSON array of about 80 issuances per page, paginated through a `Link: rel="next"`
header. Its `x-ratelimit-limit` is 10 for an unauthenticated client, and it answers 403
`not_allowed_by_plan` for a name that is not under a public suffix.

## Decision

The existing `/api/domain/ct-subdomains` panel queries crt.sh and Cert Spotter concurrently
(`ct_subdomains_service.py`) and returns one deduplicated `subdomains` list plus a `sources` list
with one `CtSourceStatus` per source (`ok`, `subdomain_count`, `certificate_count`, `truncated`,
`error`, `error_code`). A failed source shows as "not checked" in the panel and never as "no
subdomains" (ADR 0022). The lookup fails only when both sources fail
(`CT_ALL_SOURCES_FAILED`, 502, naming both errors). Cert Spotter is read for exactly one page,
and `truncated` says when more exist. The per-certificate `certificates` detail stays
crt.sh-only, since the panel never rendered it and the two sources' certificate fields differ.

Cert Spotter exists to keep CT enumeration working while crt.sh is down, and only a merged list
delivers that without the analyst cross-reading two panels. The schema change is additive
(`sources` is new; `subdomains`, `certificates` and `total_certificates` keep their meaning for
crt.sh), so nothing that reads the old shape breaks.

## Accepting

- With the keyless quota, a burst of more than a few lookups an hour makes Cert Spotter answer
  429 (`CERTSPOTTER_RATE_LIMITED`). The panel then falls back to crt.sh alone and says so.
- For a large domain, Cert Spotter covers only the newest ~80 certificates. The panel marks this
  as truncated, so the list is not presented as complete.

## Revisit

If Cert Spotter's keyless quota proves too small in practice, add an optional SSLMate API key
(Settings → API Keys) that raises the quota and allows reading more pages.

## Rejected

- **A separate Cert Spotter panel** - simpler and leaves the crt.sh schema untouched, but while
  crt.sh is down the analyst still sees an error panel next to a second list, which is the problem
  this source was added to solve.
- **Paging Cert Spotter up to a cap of several pages** - more complete for large domains, but at
  about 10 keyless queries an hour, three pages per lookup leaves room for only three lookups.
