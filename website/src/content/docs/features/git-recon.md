---
title: Git Recon
description: Correlate names, emails, and GitHub logins from commit history.
---

Correlates names, emails, and GitHub logins from git commit history using
[gitcolombo](https://github.com/Soxoj/gitcolombo). Three modes:

- **Search** — API-only (GitHub GPG keys + commit search), no cloning required.
- **URL** / **Nickname** — clones one repository, or every public non-fork repository of a
  user/org, and cross-references author vs. committer identities across full history to surface
  aliases and shared-identity clusters.

A GitHub personal access token (configured under Settings → API Keys) is optional but recommended
to avoid unauthenticated GitHub rate limits.
