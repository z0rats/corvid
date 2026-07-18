import asyncio
import json
import logging
import re
import shutil
import tempfile
import urllib.error
import urllib.request
from collections import defaultdict

import gitcolombo

from app.core.database import managed_session
from app.features.git_recon.config.git_recon_config import (
    CLONE_WORKERS,
    MAX_REPOS_PER_SCAN,
    WALL_CLOCK_TIMEOUT_SECONDS,
)
from app.features.git_recon.crud.git_recon_crud import complete_search, create_running_search, fail_search

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


def _authed_github_get_json(url: str, token: str | None):
    """gitcolombo's own get_public_repos_count()/get_github_repos() (used below
    for 'nickname' mode's repo-discovery step) never send an Authorization
    header - only get_gpg_keys_emails()/search_commits_by_author() ('search'
    mode) accept a token. Unauthenticated GitHub API calls cap at 60/hour, so
    repo discovery can spuriously report "no public repos" well before that
    limit is visible anywhere else, even with a PAT configured in Settings.
    Reimplemented here (gitcolombo's own public URL/timeout constants, same
    request shape as its private _gh_authed) rather than depending on that
    private helper directly.
    """
    headers = {"Accept": "application/vnd.github+json", "User-Agent": gitcolombo.HTTP_USER_AGENT}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=gitcolombo.HTTP_TIMEOUT) as resp:
            payload = resp.read()
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.debug("GET %s failed: %s", url, exc)
        return None
    try:
        return json.loads(payload.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.debug("Bad JSON from %s: %s", url, exc)
        return None


def _get_public_repos_count(nickname: str, token: str | None) -> int:
    data = _authed_github_get_json(gitcolombo.GITHUB_USER_URL.format(nickname=nickname), token)
    if not data:
        return 0
    return int(data.get("public_repos", 0))


def _get_github_repos(nickname: str, repos_count: int, include_forks: bool, token: str | None) -> set[str]:
    if repos_count <= 0:
        return set()
    per_page = gitcolombo.GITHUB_PER_PAGE
    last_page = (repos_count + per_page - 1) // per_page
    repos: set[str] = set()
    for page in range(1, last_page + 1):
        data = _authed_github_get_json(
            gitcolombo.GITHUB_REPOS_URL.format(nickname=nickname, per_page=per_page, page=page), token,
        )
        if not data:
            continue
        for repo in data:
            if repo.get("fork") and not include_forks:
                continue
            repos.add(repo["html_url"])
    return repos


def _person_to_dict(person: "gitcolombo.Person", mentions: dict[str, dict] | None = None) -> dict:
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
        "mentions": sorted(
            (mentions or {}).values(),
            key=lambda m: m["as_author"] + m["as_committer"],
            reverse=True,
        ),
    }


def _record_mention(
    mentions: dict[str, dict[str, dict]], person_key: str, repo_url: str, commit_hash: str, *, role: str,
) -> None:
    entry = mentions[person_key].setdefault(
        repo_url, {"repo_url": repo_url, "sample_commit": commit_hash, "as_author": 0, "as_committer": 0},
    )
    entry[role] += 1


def _analyst_to_result(
    analyst: "gitcolombo.GitAnalyst",
    repo_outcomes: list[dict],
    notes: list[str],
    mentions: dict[str, dict[str, dict]] | None = None,
) -> dict:
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
        _person_to_dict(p, (mentions or {}).get(p.key))
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
    # gitcolombo.Person only tracks a single last-seen repo/commit per identity
    # (overwritten on every _upsert), so it can't answer "which repos/commits
    # mention this person" itself. analyst.commits is a flat list with no repo
    # attached to each Commit either - the only place that association exists
    # is here, at the per-url append() call site, so we slice out each repo's
    # own commits right after appending them to build that mapping ourselves.
    mentions: dict[str, dict[str, dict]] = defaultdict(dict)
    for url, path in cloned.items():
        if not path:
            continue
        start = len(analyst.commits)
        analyst.append(url, cloned_path=path)
        for commit in analyst.commits[start:]:
            _record_mention(mentions, commit.author, url, commit.hash, role="as_author")
            _record_mention(mentions, commit.committer, url, commit.hash, role="as_committer")

    failed = sum(1 for o in repo_outcomes if not o["cloned"])
    if failed:
        notes.append(f"{failed} of {len(sources)} repo(s) failed to clone")

    if resolve_github_logins and analyst.persons:
        analyst.resolve_persons()

    return _analyst_to_result(analyst, repo_outcomes, notes, mentions)


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
    so a wedged clone/API call can't hang the request indefinitely (raises TimeoutError).
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
        count = await asyncio.to_thread(_get_public_repos_count, nickname, github_token)
        if not count:
            raise GitReconError(
                f"No public repos found for '{nickname}' (or rate-limited - try adding a GitHub PAT in Settings)"
            )
        repos = await asyncio.to_thread(_get_github_repos, nickname, count, include_forks, github_token)
        # _get_github_repos() returns html_url straight from GitHub's own API response
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


async def run_scan_task(
    *,
    mode: str,
    target: str,
    include_forks: bool,
    resolve_github_logins: bool,
    ignore_noreply: bool,
    github_token: str | None,
    queue: asyncio.Queue,
) -> None:
    """Run one gitcolombo scan, persisting its result and streaming coarse-grained
    progress via the given queue.

    Spawned as a background task by the route handler so the request isn't held
    open for the scan's full duration (which can run up to WALL_CLOCK_TIMEOUT_SECONDS
    - long enough that a reverse proxy in front of this app would otherwise time
    out the connection well before the scan finishes). Runs independently of the
    SSE client's connection: it keeps running and persists its result even if the
    client disconnects mid-scan. gitcolombo has no per-item progress callback (git
    cloning/GitHub API calls, not per-site checks like maigret), so this only
    emits "started" and a single terminal event, same as social_analyzer_service.py.
    """
    async with managed_session() as db:
        search = await create_running_search(db, mode=mode, target=target)
        search_id = search.id

    queue.put_nowait({"type": "started", "search_id": search_id, "mode": mode, "target": target})

    try:
        result = await run_scan(
            mode=mode,
            target=target,
            include_forks=include_forks,
            resolve_github_logins=resolve_github_logins,
            ignore_noreply=ignore_noreply,
            github_token=github_token,
        )
    except GitReconError as exc:
        async with managed_session() as db:
            await fail_search(db, search_id, error=str(exc))
        queue.put_nowait({"type": "failed", "search_id": search_id, "error": str(exc)})
        queue.put_nowait(None)
        return
    except TimeoutError:
        error = "Scan timed out"
        async with managed_session() as db:
            await fail_search(db, search_id, error=error)
        queue.put_nowait({"type": "failed", "search_id": search_id, "error": error})
        queue.put_nowait(None)
        return
    except Exception as exc:
        logger.error("Git recon %s scan for '%s' failed: %s", mode, target, exc, exc_info=True)
        async with managed_session() as db:
            await fail_search(db, search_id, error=str(exc))
        queue.put_nowait({"type": "failed", "search_id": search_id, "error": str(exc)})
        queue.put_nowait(None)
        return

    repo_outcomes = result.get("repos", [])
    repos_scanned = sum(1 for r in repo_outcomes if r["cloned"])
    repos_failed = sum(1 for r in repo_outcomes if not r["cloned"])
    persons_found = len(result.get("persons", []))

    async with managed_session() as db:
        await complete_search(
            db, search_id,
            repos_scanned=repos_scanned, repos_failed=repos_failed, persons_found=persons_found, result=result,
        )

    logger.info(
        "Git recon %s scan for '%s': %d person(s), %d repo(s) scanned",
        mode, target, persons_found, repos_scanned,
    )

    queue.put_nowait({
        "type": "completed",
        "search_id": search_id,
        "repos_scanned": repos_scanned,
        "repos_failed": repos_failed,
        "persons_found": persons_found,
    })
    queue.put_nowait(None)
