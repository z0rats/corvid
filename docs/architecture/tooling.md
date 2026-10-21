# Build, CI, dependencies and the docs site

Deep-dive referenced from AGENTS.md. How the repo is built, gated and released; the commands
themselves are in `make help`.

## Stack pins worth knowing

- Backend LLM features use `pydantic-ai-slim[anthropic,openai]`, not the `pydantic-ai`
  metapackage, which hard-depends on every provider SDK. `app/utils/llm_service.py`'s model
  registry also auto-discovers models pulled into a local Ollama server via its OpenAI-compatible
  `/v1/models` endpoint (`LLM_OLLAMA_BASE_URL`, no API key, silently skipped if unreachable).
- react-router 8 in declarative mode only: `BrowserRouter`/`Route`/hooks come from `react-router`,
  not the removed `react-router-dom` package.
- `typescript` is pinned below latest (`~6.0.3`), since `typescript-eslint` 8.x's peer range is
  `<6.1.0`. Lift the pin once it accepts 7, and check that Yarn's builtin `compat/typescript` patch
  still applies to 7.x's package layout. TypeScript is adopted incrementally (`allowJs`,
  convert-on-touch, no bulk rewrite).
- ESLint 10 flat config (`frontend/eslint.config.mjs`). `frontend/` and `website/` pin the same
  Yarn release via `packageManager` - bump both together.

## Lock files

`backend/requirements.txt` (runtime; all the image installs) and `requirements-dev.txt` (+ pytest,
ruff, mypy; CI and local venvs) are compiled from their `.in` via `uv pip compile <in> -o <txt>` -
regenerate both, runtime first, never hand-edit (`-P <pkg>` bumps one package). Gates:
`test_requirements_locks_in_sync.py` (drift), `test_direct_imports_declared.py` (`app/` imports
only what `requirements.in` declares). `maigret[pdf]` is the direct requirement since its extra
provides the PDF stack `core/reports/` needs.

## Coverage

Codecov (`pytest-cov` / `vitest --coverage`, uploaded from CI on every push, badge in `README.md`)
reports numbers but has no threshold that fails CI on a drop. Both sides count every source file
toward the denominator, not just ones a test imports: backend via `backend/pyproject.toml`'s
`[tool.coverage.run] source` / `[tool.coverage.report] include_namespace_packages` (most of `app/`
is implicit namespace packages, which coverage.py's unexecuted-file walk skips by default);
frontend via `frontend/vite.config.js`'s `coverage.include` (since Vitest 4 a set `include` alone
reports untested files; the `all: true` beside it is a leftover no-op). The reported percentage
therefore runs lower than a bare `--cov=app` / default vitest setup would show.

## CI (`.github/workflows/ci.yml`)

Tests, a docker-build smoke test, blocking lint (ruff; mypy via `scripts/check_mypy_baseline.py`,
failing only on errors not in `backend/mypy-baseline.txt` - `--update` after fixes; eslint/`tsc`),
report-only CVE scans (`pip-audit` / `yarn npm audit` / Trivy - unfixable transitive findings
likely). Also a `docs-coverage` job (`check-docs-coverage.mjs`), CodeQL and gitleaks (separate
blocking jobs) and an OpenSSF Scorecard job.

## Release (`.github/workflows/release.yml`)

On a `v*.*.*` tag push: multi-arch (`amd64`/`arm64`) images pushed by digest, merged into one
manifest list per image, which gets a CycloneDX SBOM and a Sigstore build-provenance attestation in
GHCR (`gh attestation verify oci://ghcr.io/<owner>/corvid-backend:<tag> --owner <owner>`; why
post-merge: `docs/adr/0005-sbom-attestation-on-merged-manifest.md`).

## Dependabot (`.github/dependabot.yml`)

pip / npm (frontend + website) / docker / actions updates on the 1st and 15th, with a 14-day
`cooldown` as a supply-chain mitigation.

## Pre-commit (`.pre-commit-config.yaml`)

gitleaks; `ruff check --fix` / `ruff format` on staged `backend/` files; local hooks that regenerate
`docs/database-schema.md` (model change) and `extension/generated-ioc-patterns.js` (IOC-detection
change) - a resulting diff fails the hook, so `git add` it and re-commit; the new-`ioc_lookup`-
provider docs gate (`scripts/check_new_ioc_provider_docs.py`); the dangling-`docs/`-reference check.
mypy stays CI-only. Setup: `pre-commit install`.

## Docs site (`website/`)

Public docs at `https://z0rats.github.io/corvid/`, built with Astro + Starlight. Own
`package.json`/`yarn.lock` (Yarn 4, `nodeLinker: node-modules`, not part of any workspace). Content
under `website/src/content/docs/`, sectioned `getting-started/`, `usage/`, `architecture/`,
`features/`. `astro.config.mjs`'s sidebar is `autogenerate` per section, so a page's frontmatter
`sidebar: { order: N }` (gapped by 10; omitted, the page sorts to the end of its section) is the
only place its nav position is declared. Deploys via `.github/workflows/docs.yml` on every push to
`main` touching `website/**` or the workflow itself. Dev: `cd website && yarn dev`; build: `yarn build` (`website/dist/`).
