# The API key test only makes calls that spend no quota

Settings → API Keys couldn't tell whether a saved key works; a bad key surfaced as an error on
the next lookup. A separate quota panel checked just VirusTotal, Shodan and Hunter.io. A live test
per key needs a call per provider, and for many providers the only authenticated call is a lookup
that spends a daily or monthly allowance or paid credits. Invalid-key behaviour was checked live
on 2026-10-22 with a fake key: most providers answer 401/403. NVD answers with an empty 404 even
for an existing CVE. IPQualityScore's account endpoint answers 200 with `success: false`. abuse.ch
answers 403 `unknown_auth_key`. Mandiant's token endpoint accepts HTTP Basic auth only.

## Decision

- A test calls an account, status or token endpoint (VirusTotal `users/<key>`, Shodan `api-info`,
  Hunter `account`, GitHub `rate_limit`, IPQualityScore `account`, HIBP `subscription/status`,
  OTX `users/me`, Steam `GetSupportedAPIList`, Anthropic/OpenAI `models`, and the CrowdStrike,
  Mandiant and Reddit OAuth token endpoints), or a fixed harmless lookup on a provider with no
  quota at all (NVD, MalwareBazaar, ThreatFox, URLhaus).
- Every other keyed service is in `KEY_TEST_EXEMPT` with a reason shown in the UI as "Can't be
  tested". That covers services whose every call spends credits or a counted allowance, or bills
  (Google Maps), plus the Instagram and Google sessions, since checking those acts on the account.
  A gate test fails on a keyed service in neither registry.
- The quota panel is folded in: a check that reports an allowance returns it with the status.
  `GET /api/services/quota` and `QuotaPanel` are gone.
- Tests run on demand (per service and "Test all") and automatically after a key is saved.
  Results are live only, with no new columns.
- `detail` is fixed text of ours, never the provider's response, so a key a provider echoes back
  can't reach the client.

Testing a key should never cost the analyst the lookups it exists to enable, and a check that
quietly spends a 30-a-day allowance (CrowdSec) or paid credits (Censys) would do exactly that.

## Accepting

- About half the keyed services, AbuseIPDB among them, can't be tested. A bad key there still
  shows up only on the next lookup.
- No last-tested time across reloads.

## Revisit

- If a provider in `KEY_TEST_EXEMPT` gains a free account or status endpoint.

## Rejected

- **Cheapest lookup with a confirmation for metered providers** - covers every service, but it
  spends real allowance and adds a confirm step to "Test all".
- **Persisting the last result** - needs a migration for a status that goes stale anyway.
- **Keeping the quota panel separate** - two places and duplicate calls to the same three
  account endpoints.
- **Testing on demand only** - a mistyped key would stay unnoticed until the first lookup.
