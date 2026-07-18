import asyncio
import logging
import re
import shutil
import tempfile

import gitcolombo

from app.features.git_recon.config.git_recon_config import (
    CLONE_WORKERS,
    MAX_REPOS_PER_SCAN,
    WALL_CLOCK_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

# gitcolombo's git_clone() shells out to `git clone <url> <dir>` via subprocess -
# git itself accepts arbitrary URL schemes (file://, ssh://, and on older git,
# ext::), which is outside ssrf_guard.safe_get's reach (that only wraps httpx
# clients). Restricting to this shape before a user-supplied URL ever reaches
# subprocess argv is the sole gate against that.
_REPO_URL_RE = re.compile(r"^https://github\.com/([\w.-]+)/([\w.-]+?)(?:\.git)?/?$", re.IGNORECASE)
_NICKNAME_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")


class GitReconError(ValueError):
    """Invalid input (bad URL/nickname), or a scan that found nothing to do"""


def validate_github_repo_url(url: str) -> str:
    """Restrict to a canonical https://github.com/<owner>/<repo> URL, stripping
    any .git suffix / trailing slash so it matches gitcolombo's own clone-target
    naming."""
    match = _REPO_URL_RE.match((url or "").strip())
    if not match:
        raise GitReconError("Only https://github.com/<owner>/<repo> URLs are supported")
    return f"https://github.com/{match.group(1)}/{match.group(2)}"


def validate_github_nickname(nickname: str) -> str:
    nickname = (nickname or "").strip()
    if not _NICKNAME_RE.match(nickname):
        raise GitReconError("Invalid GitHub username")
    return nickname


def _person_to_dict(person: "gitcolombo.Person") -> dict:
    return {
        "key": person.key,
        "name": person.name,
        "email": person.email,
        "as_author": person.as_author,
        "as_committer": person.as_committer,
        "github_login": person.github_login,
        "is_noreply": gitcolombo.is_system_email(person.email),
        "aliases": [
            {
                "name": alias.name,
                "email": alias.email,
                "is_noreply": gitcolombo.is_system_email(alias.email),
            }
            for alias in person.also_known.values()
        ],
    }


def _analyst_to_result(analyst: "gitcolombo.GitAnalyst", repo_outcomes: list[dict], notes: list[str]) -> dict:
    shared_name_groups = [
        {"name": name, "emails": sorted(emails)}
        for name, emails in analyst.name_to_emails.items()
        if len(emails) > 1
    ]
    same_person_clusters = [
        {"names": names, "emails": sorted(emails)}
        for names, emails in analyst.same_emails_persons.values()
    ]
    persons = [
        _person_to_dict(p)
        for p in sorted(analyst.persons.values(), key=lambda p: p.as_author + p.as_committer, reverse=True)
    ]
    return {
        "stats": {
            "repos": len(analyst.repos),
            "commits": len(analyst.commits),
            "persons": len(analyst.persons),
        },
        "repos": repo_outcomes,
        "persons": persons,
        "shared_name_groups": shared_name_groups,
        "same_person_clusters": same_person_clusters,
        "gpg_keys": [],
        "commit_hits": [],
        "notes": notes,
    }


def _run_search_mode_sync(username: str, token: str | None, ignore_noreply: bool) -> dict:
    gpg_results = list(gitcolombo.get_gpg_keys_emails(username, token=token))
    commit_results = list(gitcolombo.search_commits_by_author(username, token=token))

    if ignore_noreply:
        gpg_results = [r for r in gpg_results if not gitcolombo.is_system_email(r["email"])]
        commit_results = [r for r in commit_results if not gitcolombo.is_system_email(r["email"])]

    notes = [] if (gpg_results or commit_results) else ["No emails found via /gpg_keys or /search/commits."]
    return {
        "stats": {"repos": 0, "commits": 0, "persons": 0},
        "repos": [],
        "persons": [],
        "shared_name_groups": [],
        "same_person_clusters": [],
        "gpg_keys": gpg_results,
        "commit_hits": commit_results,
        "notes": notes,
    }


def _run_clone_mode_sync(sources: list[str], repos_dir: str, *, resolve_github_logins: bool) -> dict:
    notes: list[str] = []
    cloned = gitcolombo.clone_many(sources, repos_dir, workers=CLONE_WORKERS)
    repo_outcomes = [{"url": url, "cloned": path is not None} for url, path in cloned.items()]

    analyst = gitcolombo.GitAnalyst(repos_dir=repos_dir)
    for url, path in cloned.items():
        if path:
            analyst.append(url, cloned_path=path)

    failed = sum(1 for o in repo_outcomes if not o["cloned"])
    if failed:
        notes.append(f"{failed} of {len(sources)} repo(s) failed to clone")

    if resolve_github_logins and analyst.persons:
        analyst.resolve_persons()

    return _analyst_to_result(analyst, repo_outcomes, notes)


async def run_scan(
    *,
    mode: str,
    target: str,
    include_forks: bool,
    resolve_github_logins: bool,
    ignore_noreply: bool,
    github_token: str | None,
) -> dict:
    """Run one gitcolombo scan (search/url/nickname) and return a GitReconResult-
    shaped dict.

    All of gitcolombo's I/O is blocking (subprocess + urllib), so each stage runs
    via asyncio.to_thread; the whole operation is bounded by WALL_CLOCK_TIMEOUT_SECONDS
    so a wedged clone/API call can't hang the request indefinitely (raises
    TimeoutError, mapped to a 504 by the router).
    """
    if mode == "search":
        username = validate_github_nickname(target)
        return await asyncio.wait_for(
            asyncio.to_thread(_run_search_mode_sync, username, github_token, ignore_noreply),
            timeout=WALL_CLOCK_TIMEOUT_SECONDS,
        )

    if mode == "url":
        sources = [validate_github_repo_url(target)]
        discovered_count = 1
    elif mode == "nickname":
        nickname = validate_github_nickname(target)
        count = await asyncio.to_thread(gitcolombo.get_public_repos_count, nickname)
        if not count:
            raise GitReconError(
                f"No public repos found for '{nickname}' (or rate-limited - try adding a GitHub PAT in Settings)"
            )
        repos = await asyncio.to_thread(gitcolombo.get_github_repos, nickname, count, include_forks)
        # get_github_repos() returns html_url straight from GitHub's own API response
        # (not user input), but re-validate defensively before any of it reaches
        # git_clone()'s subprocess call.
        sources = sorted(r for r in repos if _REPO_URL_RE.match(r))
        discovered_count = len(sources)
        if len(sources) > MAX_REPOS_PER_SCAN:
            sources = sources[:MAX_REPOS_PER_SCAN]
    else:
        raise GitReconError(f"Unknown scan mode: {mode}")

    if not sources:
        raise GitReconError("No repositories to scan")

    repos_dir = tempfile.mkdtemp(prefix="git-recon-")
    try:
        result = await asyncio.wait_for(
            asyncio.to_thread(
                _run_clone_mode_sync,
                sources,
                repos_dir,
                resolve_github_logins=resolve_github_logins,
            ),
            timeout=WALL_CLOCK_TIMEOUT_SECONDS,
        )
    finally:
        shutil.rmtree(repos_dir, ignore_errors=True)

    if discovered_count > len(sources):
        result.setdefault("notes", []).append(
            f"found {discovered_count} public repo(s), scanning only the first {MAX_REPOS_PER_SCAN}"
        )
    return result
