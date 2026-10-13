# user-scanner as a second Email Search source (library, manifest-gated), not a replacement or a CLI

Email Search's mailcat answers "which mailboxes exist for this *username* at ~26 mail providers".
That is a different question from "which online services have an account for this *email
address*", which [user-scanner](https://github.com/kaifcodec/user-scanner) (MIT, ~210 email
modules) answers, often with profile metadata. Nothing in Corvid answered the second one.

## Decision

Add it as a second `source` on the existing Email Search scan table, driven in-process through its
`engine.check`, with a committed per-module manifest deciding what may run.

- **Source, not replacement.** The inputs differ (username vs full address) and so do the claims
  (a mailbox exists vs an account is registered). `username_search` already models "one table, several
  tools" with `source`; `mail_searches` gets the same column. Results fit the existing child table.
- **Library, not CLI or isolated venv.** `docs/adr/0018-*` exists for dependency conflicts;
  user-scanner has none with the main lock (`httpx<0.29`, `curl_cffi<1`, `rich>=13` all satisfied),
  and in-process gives per-module progress. Importing it under Python 3.14 and loading all modules
  was verified before adopting it.
- **Manifest, not upstream's filter.** A module can answer "is this registered?" by triggering a
  password-reset or verification email to the *target*. Upstream keeps a hand-written list of such
  modules and that list is incomplete (AniList's reset mutation was missing, found by reading the
  modules). The manifest records, for the pinned version, a `run` decision with a reason for every
  blocked module, and default-denies anything it doesn't list; a test fails when an upgrade adds
  modules so each is read before it can run. Reviewed-safe modules whose code merely mentions
  "reset"/"OTP" (a response field, an explicit `sendOtp: false`) are allowed.
- **No Tor/proxy support in v1.** Its proxy handling is a process-global; the run refuses rather than
  silently bypassing a configured Tor/proxy.
- **Not used from it**: cross-scan/pivot engine (its own pivots table is the model for Username
  Search's pivots, reimplemented there), PDF export, MCP server, Hudson Rock call (already ours),
  the email orchestrator (global `httpx` monkey-patch).

## Consequences

- One more runtime dependency whose modules break whenever a service changes its sign-in flow; a
  failing check shows as an error count, never as "not registered".
- Every upgrade is a review task by design (the manifest test). That is the price of not emailing
  strangers.
- The lock file must be regenerated with network access (`uv pip compile requirements.in -o
  requirements.txt`) for the package to be present in the image; until then the source reports itself
  as not installed.
