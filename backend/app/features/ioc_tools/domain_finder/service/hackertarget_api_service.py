"""
Passive subdomain enumeration via HackerTarget's hostsearch API.

hackertarget.com/hostsearch needs no API key and returns every hostname it
has on file for a domain as plain `hostname,ip` CSV lines - one request, no
pagination. The free tier is rate-limited to a fixed daily quota, signalled
as a plain-text "API count exceeded" line rather than a proper HTTP error
status, so that has to be detected from the response body instead.
"""

import logging

import httpx

from app.features.ioc_tools.domain_finder.service.provider_http import Provider, provider_get

logger = logging.getLogger(__name__)

HACKERTARGET = Provider(
    name="HackerTarget",
    code="HACKERTARGET",
    base_url="https://api.hackertarget.com/hostsearch/",
    accept=None,
)


async def fetch_hackertarget_hosts(domain: str) -> list[tuple[str, str | None]]:
    """Raw (hostname, ip_address) pairs for a domain from HackerTarget's hostsearch API.
    Failures raise `AppHTTPException` (`provider_http`), plus `HACKERTARGET_RATE_LIMITED`
    when the free-tier daily quota is hit."""

    def parse(response: httpx.Response) -> list[tuple[str, str | None]]:
        text = response.text.strip()
        if not text:
            logger.info("HackerTarget returned an empty response for domain: %s", domain)
            return []

        first_line = text.splitlines()[0].strip().lower()
        if "api count exceeded" in first_line:
            logger.warning("HackerTarget free-tier quota hit for domain: %s", domain)
            raise HACKERTARGET.error(
                429,
                "RATE_LIMITED",
                "HackerTarget free-tier API quota exceeded, try again later",
            )
        if first_line.startswith("error"):
            # No hosts on file (or an invalid query our own validator already
            # rejects) - not a failure worth surfacing, just nothing found
            logger.info("HackerTarget found no hosts for domain: %s (%s)", domain, first_line)
            return []

        hosts: list[tuple[str, str | None]] = []
        for line in text.splitlines():
            hostname, _, ip = line.partition(",")
            hostname = hostname.strip()
            if hostname:
                hosts.append((hostname, ip.strip() or None))

        logger.info("Retrieved %s hosts from HackerTarget for domain: %s", len(hosts), domain)
        return hosts

    return await provider_get(HACKERTARGET, subject=domain, params={"q": domain}, parse=parse)
