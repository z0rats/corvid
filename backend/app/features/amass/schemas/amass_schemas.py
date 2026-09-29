import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def _validate_domain(v: str) -> str:
    """Normalize protocol/path/case and reject search patterns - amass takes a
    plain registrable domain, not a URL or a wildcard pattern."""
    if not v or not v.strip():
        raise ValueError("Domain cannot be empty")

    domain = v.strip().lower()
    if domain.startswith(("http://", "https://")):
        domain = domain.split("://", 1)[1]
    if "/" in domain:
        domain = domain.split("/", 1)[0]
    if len(domain) > 255:
        raise ValueError("Domain name too long")
    if any(char in domain for char in [" ", "\t", "\n", "\r", "*", "?"]):
        raise ValueError("Domain contains invalid characters")
    return domain


class ScanRequest(BaseModel):
    """Request to run an amass active-enumeration scan for a domain"""

    domain: str = Field(
        ..., min_length=1, max_length=255, description="Domain to enumerate (e.g. 'example.com')"
    )
    brute_force: bool = Field(
        default=False,
        description=(
            "Enable wordlist brute-forcing in addition to passive sources - slower and "
            "noisier (real DNS queries against the target's infrastructure), off by default"
        ),
    )

    @field_validator("domain")
    @classmethod
    def validate_domain_format(cls, v: str) -> str:
        return _validate_domain(v)


class AmassHost(BaseModel):
    """A single discovered host, as read back from amass's engine via `amass subs`"""

    hostname: str
    ip: str | None = None


class AmassResult(BaseModel):
    hosts: list[AmassHost] = Field(default_factory=list)


class SearchSummary(BaseModel):
    """Summary of a past search, without its full result"""

    id: int
    domain: str
    brute_force: bool
    status: str
    hosts_found: int
    searched_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)


class SearchDetail(SearchSummary):
    """Full detail of a past search, including its persisted result"""

    error: str | None = None
    result: AmassResult | None = None

    model_config = ConfigDict(from_attributes=True)
