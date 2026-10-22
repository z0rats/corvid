"""Shared filtering for subdomain-enumeration sources."""

from collections.abc import Iterable


def subdomains_of(names: Iterable[str], domain: str) -> set[str]:
    """The names that are `domain` itself or sit under it, lower-cased, with a leading `*.`
    wildcard stripped. Every source's answer can carry unrelated hosts (multi-domain SAN
    certificates, same-IP neighbours, near-miss matches), so only these count as subdomains."""
    found = set()
    for name in names:
        normalized = name.strip().lower().removeprefix("*.")
        if normalized == domain or normalized.endswith(f".{domain}"):
            found.add(normalized)
    return found
