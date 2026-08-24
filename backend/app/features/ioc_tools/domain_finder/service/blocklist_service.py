"""
Blocklist / DNS-sinkhole check: queries a domain's A record via each of
several public DNS providers' security-filtering resolver and compares the
answer against that same provider's plain resolver. A provider flags a
domain when its filtering resolver withholds the real answer or serves a
different one instead - live-verified against Cisco's public
`malware.testcategory.com` test domain, which Cloudflare's malware-blocking
resolvers (1.1.1.2/1.1.1.3) sinkhole to `0.0.0.0` while every provider's
plain resolver returns the real address.

Comparing each provider's filtered answer against that *same provider's*
plain answer (rather than hardcoding each provider's sinkhole IP) is
deliberate: it keeps working even if a provider changes its sinkhole
address, at the cost of only covering providers that publish both a filtered
and an unfiltered resolver.
"""

import asyncio
import logging

import dns.asyncresolver
import dns.exception
import dns.resolver

from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    BlocklistProviderResult,
    BlocklistRequest,
    BlocklistResponse,
)

logger = logging.getLogger(__name__)

DNS_TIMEOUT = 5.0

# (provider label, filtered/security resolver IP, plain/unfiltered resolver IP).
# Only providers with both a documented filtered and unfiltered tier are
# included - a wrong guessed sinkhole IP would silently make a check useless
# (or worse, wrong), so this stays a short, verified list rather than padded
# out to match every public resolver that merely claims to filter malware.
BLOCKLIST_PROVIDERS: list[tuple[str, str, str]] = [
    ("Cloudflare (malware)", "1.1.1.2", "1.1.1.1"),
    ("Cloudflare (malware + adult)", "1.1.1.3", "1.1.1.1"),
    ("Quad9 (security)", "9.9.9.9", "9.9.9.10"),
    ("OpenDNS FamilyShield", "208.67.222.123", "208.67.222.222"),
]


async def perform_blocklist_check(request: BlocklistRequest) -> BlocklistResponse:
    """
    Check a domain against each configured provider's filtered-vs-plain DNS resolver pair.

    Args:
        request: Validated blocklist request

    Returns:
        BlocklistResponse with a per-provider result and a flagged-count summary
    """
    domain = request.domain
    logger.info("Starting blocklist check for: %s", domain)

    results = await asyncio.gather(
        *(
            _check_provider(domain, name, filtered_ip, plain_ip)
            for name, filtered_ip, plain_ip in BLOCKLIST_PROVIDERS
        )
    )
    results = list(results)

    response = BlocklistResponse(
        domain=domain,
        results=results,
        flagged_count=sum(1 for r in results if r.blocked),
    )
    logger.info(
        "Blocklist check completed for %s - flagged by %s/%s providers",
        domain,
        response.flagged_count,
        len(results),
    )
    return response


async def _check_provider(
    domain: str, provider_name: str, filtered_ip: str, plain_ip: str
) -> BlocklistProviderResult:
    filtered_answer, baseline_answer = await asyncio.gather(
        _resolve_a(domain, filtered_ip),
        _resolve_a(domain, plain_ip),
    )

    # No baseline answer at all - can't distinguish "filtered" from "this
    # domain genuinely doesn't resolve", so don't flag either way
    blocked = bool(baseline_answer) and filtered_answer != baseline_answer

    return BlocklistProviderResult(
        provider=provider_name,
        blocked=blocked,
        filtered_answer=filtered_answer,
        baseline_answer=baseline_answer,
    )


async def _resolve_a(domain: str, nameserver_ip: str) -> list[str]:
    resolver = dns.asyncresolver.Resolver(configure=False)
    resolver.nameservers = [nameserver_ip]
    resolver.timeout = DNS_TIMEOUT
    resolver.lifetime = DNS_TIMEOUT

    try:
        answer = await resolver.resolve(domain, "A")
    except dns.resolver.NXDOMAIN:
        return []
    except dns.resolver.NoAnswer:
        return []
    except dns.resolver.NoNameservers:
        return []
    except dns.exception.Timeout:
        logger.warning("Timeout querying resolver %s for %s", nameserver_ip, domain)
        return []
    except Exception as e:
        logger.warning("Unexpected error querying resolver %s for %s: %s", nameserver_ip, domain, e)
        return []

    return sorted(str(rdata) for rdata in answer)
