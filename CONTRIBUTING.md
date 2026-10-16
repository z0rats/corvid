# Contributing to Corvid

Thanks for your interest. Corvid is solo-maintained, so the process is deliberately light.

## Reporting bugs and requesting features

- **Bugs and feature requests:** open a [GitHub issue](https://github.com/z0rats/corvid/issues).
  For a bug, include the Corvid version (Settings → About, or the image tag), what you did,
  what you expected, and what happened — relevant lines from `data/logs/` help a lot (they're
  scrubbed of API keys, but double-check before pasting).
- **Security vulnerabilities:** do **not** open a public issue — follow [SECURITY.md](SECURITY.md).
- **Questions and ideas:** [GitHub Discussions](https://github.com/z0rats/corvid/discussions).

Issues and discussions are public and searchable; English is preferred.

## Contributing code

1. Fork the repository and create a branch off `main`.
2. Make your change (see requirements below), then open a pull request against `main`.
3. CI must pass, and every pull request needs an approving review from the code owner before it
   can be merged.

For anything larger than a small fix, open an issue first so the approach can be agreed on
before you spend time on it.

Setting up a local environment (backend, frontend, docs site) is described in
[Local Development](https://z0rats.github.io/corvid/getting-started/local-development/);
`make help` lists the test and lint targets CI uses.

## Requirements for acceptable contributions

- **Tests are required.** New functionality, and any substantial change to existing behavior,
  must come with automated tests in the same pull request — `pytest` under `backend/tests/`,
  Vitest next to the frontend code. Bug fixes should include a test that fails without the fix.
  Run `make test` before opening a PR.
- **Lint must be clean.** Backend: `ruff check`, `ruff format`, and mypy (no new errors beyond
  `backend/mypy-baseline.txt`). Frontend: ESLint and `tsc`. `make lint` runs all of them, the same
  way CI does. Installing the pre-commit hooks (`pre-commit install`) catches most of this early.
- **Follow the existing structure.** Backend features use the `routers` → `service` → `crud` →
  `models`/`schemas` split; frontend features mirror the backend directory names. Match the
  style of the surrounding code.
- **Security-sensitive code:** any HTTP request to a user-influenced URL must go through
  `core/security/ssrf_guard.py`; never log or return secrets.
- **Documentation:** user-facing changes update `README.md` and/or the docs site under
  `website/` in the same pull request.
- **Commit messages** follow [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat(scope): ...`, `fix(scope): ...`).
- **Dependencies:** keep new ones to a minimum, and they must be compatible with AGPL-3.0.

## Licensing of contributions

Corvid is licensed under [AGPL-3.0](LICENSE). By submitting a contribution you agree that it is
your own work and that it is licensed under the same terms.
