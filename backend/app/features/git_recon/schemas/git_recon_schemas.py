import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ScanRequest(BaseModel):
    """Request to run a gitcolombo scan for a target"""

    mode: Literal["search", "url", "nickname"] = Field(
        ...,
        description="'search': GitHub-API-only email lookup for a username (GPG-key UIDs + "
        "commit search, no cloning). 'url': clone and analyze a single GitHub repo. "
        "'nickname': clone and analyze every public (non-fork by default) repo owned by a "
        "GitHub user/org.",
    )
    target: str = Field(
        ..., min_length=1, max_length=300,
        description="GitHub username (search/nickname modes) or a https://github.com/<owner>/<repo> URL (url mode)",
    )
    include_forks: bool = Field(default=False, description="nickname mode only: include forked repositories")
    resolve_github_logins: bool = Field(
        default=True,
        description="url/nickname mode only: resolve each identity's GitHub login by scraping its last commit's page",
    )
    ignore_noreply: bool = Field(
        default=True,
        description="Filter service noreply addresses (github noreply, users.noreply.github.com, etc.) out of search-mode results",
    )


class GpgKeyEmail(BaseModel):
    email: str
    verified: bool
    key_id: str
    created_at: str
    source: str


class CommitSearchHit(BaseModel):
    email: str
    name: str
    role: str
    repo: str
    sha: str
    date: str


class PersonAlias(BaseModel):
    name: str
    email: str
    is_noreply: bool = False


class PersonMention(BaseModel):
    """One repo this identity was seen in, with a representative commit to link to"""

    repo_url: str
    sample_commit: str
    as_author: int = 0
    as_committer: int = 0


class GitPerson(BaseModel):
    key: str
    name: str
    email: str
    as_author: int
    as_committer: int
    github_login: str | None = None
    is_noreply: bool = False
    aliases: list[PersonAlias] = Field(default_factory=list)
    mentions: list[PersonMention] = Field(default_factory=list)


class SharedNameGroup(BaseModel):
    """A commit-author name observed with more than one email address"""

    name: str
    emails: list[str]


class SamePersonCluster(BaseModel):
    """Multiple names that all resolve to the exact same set of emails"""

    names: list[str]
    emails: list[str]


class RepoOutcome(BaseModel):
    url: str
    cloned: bool


class GitReconResult(BaseModel):
    stats: dict[str, int] = Field(default_factory=dict)
    repos: list[RepoOutcome] = Field(default_factory=list)
    persons: list[GitPerson] = Field(default_factory=list)
    shared_name_groups: list[SharedNameGroup] = Field(default_factory=list)
    same_person_clusters: list[SamePersonCluster] = Field(default_factory=list)
    gpg_keys: list[GpgKeyEmail] = Field(default_factory=list)
    commit_hits: list[CommitSearchHit] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class SearchSummary(BaseModel):
    """Summary of a past search, without its full result"""

    id: int
    mode: str
    target: str
    status: str
    repos_scanned: int
    repos_failed: int
    persons_found: int
    searched_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SearchDetail(SearchSummary):
    """Full detail of a past search, including its persisted result"""

    error: str | None = None
    result: GitReconResult | None = None

    model_config = ConfigDict(from_attributes=True)
