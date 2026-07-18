"""git_recon's gitcolombo integration shells out to `git clone <url>` via
subprocess - git itself accepts arbitrary URL schemes (file://, ssh://, and on
older git, ext:: command execution), which is outside `ssrf_guard.safe_get`'s
reach since that only wraps httpx clients, not subprocess argv. These tests
guard the allowlist validator that is the sole gate against a user-supplied
target reaching subprocess argv (see git_recon_service.py's module docstring
comment)."""
import pytest

from app.features.git_recon.service.git_recon_service import (
    GitReconError,
    validate_github_nickname,
    validate_github_repo_url,
)


@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/Soxoj/gitcolombo", "https://github.com/Soxoj/gitcolombo"),
        ("https://github.com/soxoj/gitcolombo/", "https://github.com/soxoj/gitcolombo"),
        ("https://github.com/soxoj/gitcolombo.git", "https://github.com/soxoj/gitcolombo"),
        ("  https://github.com/soxoj/gitcolombo  ", "https://github.com/soxoj/gitcolombo"),
    ],
)
def test_validate_github_repo_url_accepts_and_normalizes(url, expected):
    assert validate_github_repo_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ssh://git@internal-host/repo.git",
        "ext::sh -c 'touch pwned'",
        "git://internal-host/repo.git",
        "http://github.com/owner/repo",  # plain http, not https
        "https://github.com.evil.com/owner/repo",  # lookalike host
        "https://evil.com/github.com/owner/repo",  # github.com in the path, not the host
        "https://github.com/owner",  # missing repo segment
        "https://github.com/",
        "",
        "javascript:alert(1)",
        "not a url",
    ],
)
def test_validate_github_repo_url_rejects_non_github_or_dangerous_schemes(url):
    with pytest.raises(GitReconError):
        validate_github_repo_url(url)


@pytest.mark.parametrize("nickname", ["Soxoj", "octocat", "a", "a-b-c", "a" * 39])
def test_validate_github_nickname_accepts_valid_usernames(nickname):
    assert validate_github_nickname(nickname) == nickname


@pytest.mark.parametrize(
    "nickname",
    [
        "",
        "-leading-hyphen",
        "trailing-hyphen-",
        "has space",
        "has/slash",
        "a" * 40,  # over GitHub's 39-char username limit
        "../../etc/passwd",
    ],
)
def test_validate_github_nickname_rejects_invalid(nickname):
    with pytest.raises(GitReconError):
        validate_github_nickname(nickname)
