# GHunt profile lookup (`email_search`'s "Google Profile" panel)

Looks up a Google account's public profile data by email, using
[mxrch/GHunt](https://github.com/mxrch/GHunt) 2.3.4 shelled out to from `email_search/service/
ghunt_profile_service.py`. Runs from its own isolated venv (`/opt/tools/ghunt`, not the main
backend venv - see `docs/adr/0018-isolated-tool-cli-venvs.md`) since `ghunt>=2.3.2` requires
`rich<14`, conflicting with the main lock's `mitreattack-python`. Explicit-click only, same UX
shape as image-tools' ChronoVerify panel - the request goes out to Google under the analyst's own
configured account, never automatically.

## Session format and storage

GHunt has no anonymous mode - it needs a real Google account's session (cookies, OSIDs, an
Android master token), obtained by running `ghunt login` interactively (there's no headless
login flow). The session file GHunt itself writes, `~/.malfrats/ghunt/creds.m`, is:

```
base64(json.dumps({
    "cookies": {...},
    "osids": {...},
    "android": {"master_token": "...", "authorization_tokens": {...}},
}))
```

(read from the pinned 2.3.4 source, `ghunt/objects/base.py::GHuntCreds`). `ghunt_session_service.
parse_ghunt_session` replicates GHunt's own `are_creds_loaded()` check (`cookies`, `osids`, and
`android.master_token` all truthy) to validate a pasted value structurally *without ever running
GHunt* - used both when a session is saved (`PUT /api/email-search/ghunt-profile/session`) and
defensively before every lookup.

Stored as an `Apikey` row named `ghunt_session` (`EncryptedString`, same at-rest encryption as
every other provider key) - see the `service_config.py` entry and `docs/adr/0003-encrypt-only-
third-party-api-keys.md`. A real session is several KB, well past the app's original 500-character
`Apikey.key` cap, which this feature raised (globally, to 20000) since it's a single shared
validator rather than something worth special-casing per service.

Storage save-time validation intentionally doesn't reuse the generic `/api/apikeys` create/update
routes directly - there's no per-service validation hook there (Instagram's similarly-shaped
session validates lazily at use-time instead). `ghunt_session_service.save_ghunt_session` is a
small feature-owned entry point that validates, then calls the same underlying `create_apikey_
service`/`update_apikey_service` to persist - same table, same encryption, just one extra step
before the write. Deleting the session and toggling it active/inactive still go through the
existing generic `/api/apikeys/{name}` routes unchanged, since those don't need the extra check.

The frontend's `GhuntSessionInput` is a dedicated multiline-paste component, not the generic
`ApiKeyInput` used for every other service - no multiline/textarea secret input existed anywhere
in this codebase before this feature (Instagram's spec, which was expected to have solved this
already, no longer exists as a file and never actually built one either).

## Build gotcha: Pillow has no Python 3.14 wheel yet

GHunt depends on Pillow (via its face-hash/image helpers). At the time this was built, Pillow had
no prebuilt wheel for this image's Python 3.14, so `uv pip install ghunt` in the `ghunt-builder`
Dockerfile stage compiles it from source - which needs the same build toolchain as the main
`builder` stage (`build-essential`, `python3-dev`, `zlib1g-dev`, `libjpeg-dev`), not just a bare
interpreter. The compiled `_imaging` extension then needs `libjpeg62-turbo` (the runtime shared
library, not just `-dev`) in the final runtime stage as well - missed on the first pass and caught
by actually building and running the image, not just reading the Dockerfile. Once Pillow ships a
cp314 wheel, `ghunt-builder`'s build-toolchain install becomes unnecessary, but the runtime
`libjpeg62-turbo` package should stay (loaded either way, wheel or compiled).

## Subprocess isolation

GHunt's session-file path is hardcoded with no CLI override, so per-request isolation happens via
the child process's `HOME`: `ghunt_profile_service.run_ghunt_profile`

1. Loads and re-validates the stored session (defensive re-check on top of save-time validation,
   catching a row that predates it or was edited directly in the DB).
2. Acquires a module-level `asyncio.Semaphore(1)` - only one GHunt run at a time. There's exactly
   one stored session and GHunt's own account gets Google-rate-limited, so concurrent runs would
   only race each other against the same account, not add throughput.
3. Creates a private temp dir (`tempfile.mkdtemp`, `chmod 0700`), writes `<tmp>/.malfrats/ghunt/
   creds.m` (`chmod 0600`) with the stored session value, and spawns `asyncio.create_subprocess_
   exec(GHUNT_BIN, "email", <email>, "--json", <tmp>/out.json, env={"HOME": <tmp>, "PATH": "/usr/
   bin:/bin"})` - the environment is fully replaced, not merged, so no app secrets (DB URL, other
   providers' API keys) reach the child process.
4. `asyncio.wait_for(..., timeout=60)`; on timeout, `process.kill()` + `await process.wait()`.
5. The temp dir is removed in a `finally` regardless of outcome (success, timeout, or any other
   exception).

## `--json` output shape (code-derived, not live-captured)

The spec for this feature (`docs/specs/ghunt-integration-spec.md` §3.6/§10) explicitly flags the
`--json` schema as unconfirmed pending a real Google-account session, which wasn't available
during implementation. The shape below was read directly from the pinned 2.3.4 source
(`ghunt/modules/email.py`, `ghunt/parsers/people.py`, `ghunt/objects/encoders.py`) rather than
guessed - accurate to that exact version, but still not verified against a live response.
**Replacing/confirming this with a real captured fixture is an open follow-up**, tracked as a
manual acceptance step (see the spec's own §7/§9).

Top-level shape: `{"<CONTAINER>_CONTAINER": {"profile": <Person>, "play_games": <Player|null>,
"maps": {"photos": null, "reviews": null, "stats": {...}}, "calendar": {"details":...,
"events":...} | null}}`. GHunt only ever proceeds past the "does this email have a public Google
Account" check when `"PROFILE"` is among the found containers, so `<CONTAINER>` is always
`PROFILE` in practice - `parse_ghunt_profile_json` doesn't hardcode that key anyway, just takes
whatever single top-level key is present, in case a future GHunt version changes it.

Only the `profile` section (GHunt's `Person` object) is fully modeled into typed fields -
`gaia_id`, `email`, `profile_photo`/`cover_photo` (url + `is_default`), `last_profile_edit`,
`user_types`, `activated_services`, `entity_type`, `is_enterprise_user`. Two things worth knowing:

- **`names` is always empty.** `PersonName._scrape` is a permanent no-op in upstream itself
  (`pass # Google patched the names :/ very sad`) - Google's response no longer includes usable
  name data and GHunt gave up parsing it. This isn't a bug in this integration; there's no
  `full_name`/`first_name`/`last_name` field in `GhuntProfileResponse` at all, rather than exposing
  fields that can never be populated.
- **`play_games`/`maps`/`calendar` round-trip as opaque `dict | None`**, not fully typed. These
  are large, partly-dead nested objects even upstream (e.g. GHunt's own Maps reviews/photos
  fetching is commented out server-side, leaving only aggregate `stats` counts). Deepening these
  into typed fields is a reasonable follow-up once a real fixture confirms the current shape.

## Exit-code / error mapping

GHunt has no dedicated exit code per failure type:

- **Not found**: both "email doesn't exist" and "email exists but has no linked public Google
  Account" call bare `exit()` (`sys.exit(0)`) *before* writing any `--json` file. So `returncode
  == 0` with no output file on disk is `GHUNT_NOT_FOUND` (404). Unverified live (needs a real
  authenticated session) - see the note at the end of this section.
- **Session/auth failure**: a corrupted/incomplete/Google-rejected session raises an uncaught
  exception (`GHuntInvalidSession` or a deeper `check_and_gen` auth error) - Python's default
  traceback goes to stderr with a non-zero exit code. Mapped to `GHUNT_SESSION_EXPIRED` (409) via
  a best-effort case-insensitive substring match against stderr (`ghuntinvalidsession`, `authurl`,
  `authorization`, `masterautherror`, `osidautherror`); anything else non-zero falls through to
  `GHUNT_EXECUTION_ERROR` (502) with stderr truncated to ~500 characters (never logged/returned
  in full). **Verified against the real built binary** (isolated `HOME` with a garbage
  `creds.m`): exits 1, and the traceback contains `ghunt.errors.GHuntInvalidSession` - the
  substring match fires correctly on real output for this case.
- **Timeout**: `GHUNT_TIMEOUT` (504) after the 60s wall-clock ceiling, `process.kill()`'d.

Every invocation - including a bare `--help` - prints a startup banner and does a live `httpx.get`
to `raw.githubusercontent.com/mxrch/GHunt/master/ghunt/version.py` to check for updates
(`ghunt/ghunt.py::main()`, unconditional, no CLI flag to disable it). **Verified**: the real
banner reads `> GHunt 2.3.4 (🕷️  Spider Edition) <`, matching `get_ghunt_version()`'s regex
exactly, and the update-check call does fire on a plain `--help`. This is an accepted side
effect, not patched around - patching a vendored package's internals from an isolated venv would
be fragile and could silently break on a GHunt version bump. `get_ghunt_version()` uses this same
banner (via a cheap `ghunt --help` call, which never touches a session) and is `lru_cache`d to
avoid triggering that outbound call on every health-check poll.

**What's still unverified**: everything downstream of a real, successfully-authenticated
`load_and_auth()` call - the actual `--json` output shape for a found profile (this doc's schema
section), the `GHUNT_NOT_FOUND` path's exact behavior, and whether a *Google-rejected* (as
opposed to locally-corrupted) session produces the same `GHuntInvalidSession` traceback or a
different one from deeper in `check_and_gen`. All of these need a real Google-account session,
which wasn't available during implementation - manual acceptance step, not something this
change's automated tests can close on their own.
