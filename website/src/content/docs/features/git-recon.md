---
title: Git Recon
description: Correlate names, emails, and GitHub logins from commit history.
---

Correlates names, emails, and GitHub logins from git commit history using
[gitcolombo](https://github.com/Soxoj/gitcolombo). Three modes:

- **Search** — API-only (GitHub GPG keys + commit search), no cloning required.
- **URL** — clones a single repository.
- **Nickname** — clones every public, non-fork repository of a GitHub user/org.

`URL`/`Nickname` mode clones full (non-shallow) history and cross-references author vs. committer
identity across `git log --all` to surface aliases and shared-identity clusters — each identity
also shows which repos it appeared in, with commit counts and a sample commit you can click
through to on GitHub. Scans run in the background and stream progress live rather than blocking
the request, since a large org can take a while to fully clone and analyze.

A GitHub personal access token (configured under **Settings → API Keys**) is optional but
recommended — without one, both API-only search and nickname mode's repo-discovery step fall back
to GitHub's unauthenticated rate limit (60 requests/hour).

Unlike Username Search, Email Search, and other scan-style features, a Git Recon scan can't be
cancelled once started.
