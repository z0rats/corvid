# IP lookups use HTTPS-only sources and never send a non-public address out

An IP lookup with no keys configured showed no geolocation, ASN or netblock owner, so two
keyless providers were added: `ip_geo` and `ip_rdap`. Gravatar was added the same way, as a
keyless email provider. In each case a free source leaks more about the analyst's lookup than
a slightly poorer one does. Checked live on 2026-10-22: ip-api.com's free tier answers only over
plain HTTP, but it returns the most fields, including `proxy`/`hosting`/`mobile` flags and
reverse DNS. ipapi.is answers over HTTPS without a key with country, region, city, coordinates,
`asn`, `company` and `is_bogon`, but no flags. ipinfo.io answered 429 to its first keyless
request. `rdap.org/ip/<ip>` redirects to the authoritative RIR: RIPE space reaches
`rdap.db.ripe.net` and IPv6 Cloudflare space reaches `rdap.arin.net`. Gravatar's REST v3
`profiles/<sha256>` returns `avatar_url`, which any `<img>` would fetch from Gravatar's CDN.

## Decision

- `ip_geo` uses ipapi.is over HTTPS. `ip_rdap` uses the `rdap.org` bootstrap, follows its
  redirect through `safe_get` and records the RIR that answered. They are two separate
  providers, so each one fails, drifts and reports on its own.
- Both providers, Shodan InternetDB and Censys's host lookup check `is_reserved_ip` (anything that isn't
  `ipaddress.is_global`, plus unparseable input) before any request. For such an address they
  return `reserved: true` without calling out.
- Geolocation and RDAP are context, not a verdict. Their rows are always TLP WHITE and feed no
  score.
- Gravatar is an `ioc_lookup` provider for emails. That gives it lookup history, bulk lookup and
  pivots without a new page. The avatar is shown only as a link, never rendered, so nothing
  reaches Gravatar from the analyst's browser unless they click. Whether the address has an
  avatar of its own is checked by the backend (`?d=404`), the same party that already fetched
  the profile.

The lookup target is the most sensitive thing an investigation tool sends to third parties, so a
source that puts it on the wire in clear text costs more than the fields it adds. The same goes
for a page that tells a profile host someone looked. An RFC 1918 or CGNAT address means nothing
to a public source and does reveal internal addressing.

## Accepting

- No proxy/hosting/mobile flags and no reverse DNS in `ip_geo`. ipapi.is's keyless tier is about
  1,000 requests a day, shared by everything the instance looks up.
- No inline avatar. Seeing the face takes a click, and that click does reach Gravatar from the
  analyst's browser.

## Revisit

- If ipapi.is's keyless tier narrows or starts asking for a key, or if an HTTPS keyless source
  with proxy/hosting flags turns up.

## Rejected

- **ip-api.com** - richest keyless fields, but HTTP-only on the free tier (the IP looked up
  crosses the network in clear text) and its terms say non-commercial use only.
- **ipinfo.io keyless** - rate-limited on the first request.
- **One combined "IP context" provider** - one RIR or geo outage would blank both halves, and
  drift checks could no longer tell which source changed.
- **Sending reserved addresses anyway** - no source has data on them, and they leak the
  analyst's internal network layout.
- **Proxying the Gravatar avatar through the backend** - a new image endpoint for a cosmetic
  gain, and Gravatar would still be told about each view, just from the server's IP.
- **A panel in `email_search` for Gravatar** - that page is built around per-source scans by
  username. A per-address profile view would be new UI that duplicates what an `ioc_lookup` row
  already gives.
