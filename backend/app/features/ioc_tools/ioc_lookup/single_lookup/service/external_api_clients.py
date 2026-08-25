import asyncio
import logging
import time
from base64 import b64encode
from typing import Any
from urllib.parse import quote, urlsplit

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings
from app.features.ioc_tools.ioc_lookup.single_lookup.models.blacklist_models import (
    BlacklistedAddress,
    BlacklistSource,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import normalize_address

from .client_base import (
    ServiceError,
    ServiceUnavailableError,
    _authenticate_oauth,
    _require_apikey,
    _require_credentials,
    get_client,
    handle_response,
)

logger = logging.getLogger(__name__)


async def check_abuseipdb(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IP reputation lookup using AbuseIPDB API"""
    _require_apikey("AbuseIPDB", apikey)
    logger.debug("Checking IP %s with AbuseIPDB", ioc)

    client = get_client()
    response = await client.get(
        url="https://api.abuseipdb.com/api/v2/check",
        params={"ipAddress": ioc, "maxAgeInDays": "90", "verbose": True},
        headers={"Accept": "application/json", "Key": apikey},
    )
    return await handle_response("AbuseIPDB", response)


_ALIENVAULT_SECTIONS: dict[str, list[str]] = {
    "ip": ["reputation", "malware"],
    "domain": ["malware"],
    "url": ["url_list"],
    "hash": ["analysis"],
}


async def _fetch_alienvault_section(
    client, indicator_type: str, ioc: str, section: str, headers: dict[str, str]
) -> tuple[str, dict[str, Any] | None]:
    """Fetch a single OTX section with a tight timeout"""
    try:
        params = {"limit": 25} if section in ("passive_dns", "malware", "url_list") else {}
        response = await client.get(
            url=f"https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{ioc}/{section}",
            headers=headers,
            params=params,
            timeout=10.0,
        )
        response.raise_for_status()
        return (section, response.json())
    except Exception:
        logger.warning("AlienVault OTX: failed to fetch section '%s' for %s", section, ioc)
        return (section, None)


async def check_alienvault(ioc: str, ioc_type: str, apikey: str) -> dict[str, Any]:
    """Perform enriched IOC lookup using AlienVault OTX API with multiple sections"""
    _require_apikey("AlienVault OTX", apikey)

    type_map = {"ip": "IPv4", "domain": "domain", "url": "url", "hash": "file"}
    indicator_type = type_map.get(ioc_type, "IPv4")
    headers = {"X-OTX-API-KEY": apikey}

    logger.debug("Checking %s %s with AlienVault OTX", indicator_type, ioc)

    client = get_client()
    extra_sections = _ALIENVAULT_SECTIONS.get(ioc_type, [])

    all_tasks = [
        _fetch_alienvault_section(client, indicator_type, ioc, "general", headers),
        *[
            _fetch_alienvault_section(client, indicator_type, ioc, s, headers)
            for s in extra_sections
        ],
    ]
    all_results = await asyncio.gather(*all_tasks)

    general_section_name, general_data = all_results[0]
    if general_data is None:
        response = await client.get(
            url=f"https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{ioc}/general",
            headers=headers,
        )
        general_data = await handle_response("AlienVault OTX", response)

    result = general_data
    for section_name, section_data in all_results[1:]:
        if section_data is not None:
            result[f"section_{section_name}"] = section_data

    return result


async def check_checkphish(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform URL/domain phishing check using CheckPhish API"""
    _require_apikey("CheckPhish", apikey)
    logger.debug("Checking URL %s with CheckPhish", ioc)

    client = get_client()
    response = await client.post(
        url="https://developers.checkphish.ai/api/neo/scan",
        json={"apiKey": apikey, "urlInfo": {"url": ioc}},
    )
    return await handle_response("CheckPhish", response)


async def check_crowdsec(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IP reputation lookup using CrowdSec CTI API"""
    _require_apikey("CrowdSec", apikey)
    logger.debug("Checking IP %s with CrowdSec", ioc)

    client = get_client()
    response = await client.get(
        url=f"https://cti.api.crowdsec.net/v2/smoke/{ioc}", headers={"x-api-key": apikey}
    )
    return await handle_response("CrowdSec", response)


async def check_crowdstrike(ioc: str, client_id: str, client_secret: str) -> dict[str, Any]:
    """Perform IOC lookup using CrowdStrike Falcon Intelligence API"""
    _require_credentials("CrowdStrike", client_id=client_id, client_secret=client_secret)
    logger.debug("Authenticating with CrowdStrike")

    access_token = await _authenticate_oauth(
        "CrowdStrike",
        "https://api.crowdstrike.com/oauth2/token",
        data={"client_id": client_id, "client_secret": client_secret},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )

    logger.debug("Looking up IOC %s with CrowdStrike", ioc)

    client = get_client()
    response = await client.get(
        url="https://api.crowdstrike.com/intel/combined/indicators/v1",
        params={"filter": f"indicator:'{ioc}'"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    return await handle_response("CrowdStrike", response)


async def check_emailrep(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform email reputation lookup using EmailRep.io API"""
    _require_apikey("EmailRep.io", apikey)
    logger.debug("Checking email %s with EmailRep.io", ioc)

    client = get_client()
    response = await client.get(
        url=f"https://emailrep.io/{ioc}", headers={"Key": apikey, "User-Agent": "Corvid"}
    )
    return await handle_response("EmailRep.io", response)


async def check_ffraud(ioc: str) -> dict[str, Any]:
    """Perform IP fraud-intelligence lookup using FFraud's free, keyless public API"""
    logger.debug("Checking IP %s with FFraud", ioc)

    client = get_client()
    response = await client.get(url=f"https://api.ffraud.com/public/ip/{ioc}")
    return await handle_response("FFraud", response)


async def check_ffraud_email(ioc: str) -> dict[str, Any]:
    """Check email for disposable/role/blacklisted status using FFraud's free, keyless public API"""
    logger.debug("Checking email %s with FFraud", ioc)

    client = get_client()
    response = await client.post(
        url="https://api.ffraud.com/public/email/check", json={"email": ioc}
    )
    return await handle_response("FFraud", response)


async def check_libraryofleaks(ioc: str) -> dict[str, Any]:
    """Check for breach/leak mentions using Library of Leaks' free, keyless public API
    (an Aleph instance run by DDoSecrets/investigativedata.io indexing ~28.7M records across
    57 leak collections).

    Deliberately requests `limit=0` and only a per-collection facet count — never the matching
    entities themselves, which carry raw leaked content (email bodies, passwords, PII). That way
    the leaked content itself is never fetched, let alone returned here to end up persisted in
    corvid's own lookup history; the analyst reviews it on Library of Leaks itself via `search_url`.
    """
    logger.debug("Checking %s with Library of Leaks", ioc)

    client = get_client()
    response = await client.get(
        url="https://search.libraryofleaks.org/api/2/entities",
        params={
            "q": ioc,
            "filter:schemata": "Thing",
            "limit": 0,
            "facet": "collection_id",
            "facet_size:collection_id": 20,
        },
    )
    result = await handle_response("Library of Leaks", response)

    collection_facets = result.get("facets", {}).get("collection_id", {}).get("values", [])
    collections = [
        {
            "label": c["label"],
            "category": c["category"],
            "count": c["count"],
            "url": f"https://search.libraryofleaks.org/datasets/{c['id']}",
        }
        for c in collection_facets
    ]

    return {
        "query": ioc,
        "total_hits": result.get("total", 0),
        "collections": collections,
        "search_url": f"https://search.libraryofleaks.org/search?q={quote(ioc)}",
    }


async def search_github(ioc: str, access_token: str) -> dict[str, Any]:
    """Search for IOC mentions in GitHub code repositories"""
    _require_apikey("GitHub", access_token)
    logger.debug("Searching for IOC %s on GitHub", ioc)

    client = get_client()
    response = await client.get(
        url="https://api.github.com/search/code",
        params={"q": f'"{ioc}"'},
        headers={
            "Authorization": f"Bearer {access_token}",
            "Accept": "application/vnd.github.v3+json",
        },
    )
    return await handle_response("GitHub", response)


async def check_hibp(ioc: str, apikey: str) -> dict[str, Any]:
    """Check if email address appears in known data breaches using HIBP API"""
    _require_apikey("HIBP", apikey)
    logger.debug("Checking email %s with HIBP", ioc)

    client = get_client()
    response = await client.get(
        url=f"https://haveibeenpwned.com/api/v3/breachedaccount/{ioc}",
        headers={"hibp-api-key": apikey, "User-Agent": "Corvid"},
    )
    if response.status_code == 404:
        return {"message": "Not found in any breaches."}
    return await handle_response("HIBP", response)


_HUDSON_ROCK_ENDPOINTS = {
    "email": ("search-by-email", "email"),
    "ip": ("search-by-ip", "ip"),
    "domain": ("search-by-domain", "domain"),
}


async def check_hudsonrock(ioc: str, ioc_type: str) -> dict[str, Any]:
    """Check for infostealer/malware-log exposure using Hudson Rock's free, keyless public API"""
    endpoint, param = _HUDSON_ROCK_ENDPOINTS[ioc_type]
    logger.debug("Checking %s %s with Hudson Rock", ioc_type, ioc)

    client = get_client()
    response = await client.get(
        url=f"https://cavalier.hudsonrock.com/api/json/v2/osint-tools/{endpoint}",
        params={param: ioc},
    )
    return await handle_response("Hudson Rock", response)


async def check_hunter(ioc: str, apikey: str) -> dict[str, Any]:
    """Verify email address using Hunter.io API"""
    _require_apikey("Hunter.io", apikey)
    logger.debug("Verifying email %s with Hunter.io", ioc)

    client = get_client()
    response = await client.get(
        url="https://api.hunter.io/v2/email-verifier", params={"email": ioc, "api_key": apikey}
    )
    return await handle_response("Hunter.io", response)


async def check_ipqualityscore(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IP quality and fraud scoring using IPQualityScore API"""
    _require_apikey("IPQualityScore", apikey)
    logger.debug("Checking IP %s with IPQualityScore", ioc)

    client = get_client()
    response = await client.get(url=f"https://www.ipqualityscore.com/api/json/ip/{apikey}/{ioc}")
    return await handle_response("IPQualityScore", response)


async def check_maltiverse(ioc: str, endpoint: str, apikey: str) -> dict[str, Any]:
    """Perform IOC lookup using Maltiverse API"""
    _require_apikey("Maltiverse", apikey)
    logger.debug("Checking %s %s with Maltiverse", endpoint, ioc)

    client = get_client()
    response = await client.get(
        url=f"https://api.maltiverse.com/{endpoint}/{ioc}",
        headers={"Authorization": f"Bearer {apikey}"},
    )
    return await handle_response("Maltiverse", response)


async def check_malwarebazaar(ioc: str) -> dict[str, Any]:
    """Perform hash lookup using MalwareBazaar API"""
    logger.debug("Checking hash %s with MalwareBazaar", ioc)

    client = get_client()
    response = await client.post(
        url="https://mb-api.abuse.ch/api/v1/", data={"query": "get_info", "hash": ioc}
    )
    return await handle_response("MalwareBazaar", response)


async def check_mandiant(ioc: str, ioc_type: str, api_key: str, api_secret: str) -> dict[str, Any]:
    """Perform IOC lookup using Mandiant Advantage API"""
    _require_credentials("Mandiant", api_key=api_key, api_secret=api_secret)
    logger.debug("Authenticating with Mandiant")

    access_token = await _authenticate_oauth(
        "Mandiant",
        "https://api.intelligence.mandiant.com/token",
        data={
            "grant_type": "client_credentials",
            "client_id": api_key,
            "client_secret": api_secret,
        },
    )

    logger.debug("Looking up %s %s with Mandiant", ioc_type, ioc)

    client = get_client()
    response = await client.post(
        url="https://api.intelligence.mandiant.com/v4/indicator",
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"requests": [{"type": ioc_type, "value": ioc}]},
    )
    return await handle_response("Mandiant", response)


async def search_nist_nvd(ioc: str, apikey: str) -> dict[str, Any]:
    """Search for CVE information using NIST NVD API"""
    _require_apikey("NIST NVD", apikey)
    logger.debug("Looking up CVE %s with NIST NVD", ioc)

    client = get_client()
    response = await client.get(
        url="https://services.nvd.nist.gov/rest/json/cves/2.0",
        params={"cveId": ioc},
        headers={"apiKey": apikey},
    )
    return await handle_response("NIST NVD", response)


_KEV_CATALOG_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"
)
_KEV_CACHE_TTL_SECONDS = 3600  # CISA updates the catalog at most a few times a day
_kev_cache: dict[str, Any] = {"catalog": None, "fetched_at": 0.0}
_kev_cache_lock = asyncio.Lock()


async def _get_kev_catalog() -> dict[str, dict[str, Any]]:
    """Fetch and cache CISA's full KEV catalog, keyed by upper-cased CVE ID.

    CISA only publishes the full catalog (~1300 entries), no per-CVE endpoint, so this keeps
    an in-process copy refreshed on a TTL rather than re-downloading the whole feed on every
    lookup.
    """
    async with _kev_cache_lock:
        catalog = _kev_cache["catalog"]
        age = time.monotonic() - _kev_cache["fetched_at"]
        if catalog is not None and age < _KEV_CACHE_TTL_SECONDS:
            return catalog

        client = get_client()
        response = await client.get(url=_KEV_CATALOG_URL)
        raw = await handle_response("CISA KEV", response)
        catalog = {
            entry["cveID"].upper(): entry
            for entry in raw.get("vulnerabilities", [])
            if entry.get("cveID")
        }
        _kev_cache["catalog"] = catalog
        _kev_cache["fetched_at"] = time.monotonic()
        return catalog


async def check_cisa_kev(ioc: str) -> dict[str, Any]:
    """Check whether a CVE is listed in CISA's Known Exploited Vulnerabilities catalog"""
    logger.debug("Checking CVE %s against CISA KEV", ioc)

    catalog = await _get_kev_catalog()
    entry = catalog.get(ioc.upper())
    if entry is None:
        return {"listed": False}
    return {"listed": True, **entry}


async def search_first_epss(ioc: str) -> dict[str, Any]:
    """Look up a CVE's EPSS exploit-prediction score via FIRST.org's public API"""
    logger.debug("Looking up CVE %s with FIRST.org EPSS", ioc)

    client = get_client()
    response = await client.get(
        url="https://api.first.org/data/v1/epss",
        params={"cve": ioc},
    )
    return await handle_response("FIRST.org EPSS", response)


async def check_pulsedive(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IOC lookup using Pulsedive API"""
    _require_apikey("Pulsedive", apikey)
    logger.debug("Checking IOC %s with Pulsedive", ioc)

    client = get_client()
    response = await client.get(
        url="https://pulsedive.com/api/info.php",
        params={"indicator": ioc, "key": apikey, "pretty": "1"},
    )
    return await handle_response("Pulsedive", response)


async def search_reddit(ioc: str, client_id: str, client_secret: str) -> dict[str, Any]:
    """Search for IOC mentions on Reddit using Reddit API"""
    _require_credentials("Reddit", client_id=client_id, client_secret=client_secret)
    logger.debug("Authenticating with Reddit")

    access_token = await _authenticate_oauth(
        "Reddit",
        "https://www.reddit.com/api/v1/access_token",
        data={"grant_type": "client_credentials"},
        headers={"User-Agent": "Corvid/0.1"},
        auth=(client_id, client_secret),
    )

    logger.debug("Searching for IOC %s on Reddit", ioc)

    client = get_client()
    response = await client.get(
        url="https://oauth.reddit.com/search",
        params={"q": f'"{ioc}"', "limit": 25},
        headers={"Authorization": f"bearer {access_token}", "User-Agent": "Corvid/0.1"},
    )
    raw = await handle_response("Reddit", response)

    children = raw.get("data", {}).get("children", [])
    posts = [
        {
            "id": child["data"].get("id"),
            "title": child["data"].get("title"),
            "author": child["data"].get("author"),
            "subreddit": child["data"].get("subreddit_name_prefixed")
            or child["data"].get("subreddit"),
            "score": child["data"].get("score", 0),
            "num_comments": child["data"].get("num_comments", 0),
            "created_utc": child["data"].get("created_utc"),
            "message": child["data"].get("selftext") or None,
            "url": f"https://www.reddit.com{child['data'].get('permalink', '')}",
        }
        for child in children
        if child.get("data")
    ]

    return {"posts": posts, "count": raw.get("data", {}).get("dist", len(posts))}


async def check_safe_browsing(ioc: str, apikey: str) -> dict[str, Any]:
    """Check URL safety using Google Safe Browsing API"""
    _require_apikey("Google Safe Browse", apikey)
    logger.debug("Checking URL %s with Google Safe Browsing", ioc)

    payload = {
        "client": {"clientId": "corvid", "clientVersion": settings.api.version},
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": ioc}],
        },
    }
    client = get_client()
    response = await client.post(
        url="https://safebrowsing.googleapis.com/v4/threatMatches:find",
        params={"key": apikey},
        json=payload,
    )
    return await handle_response("Google Safe Browse", response)


async def check_shodan(ioc: str, method: str, apikey: str) -> dict[str, Any]:
    """Perform IP or domain lookup using Shodan API"""
    _require_apikey("Shodan", apikey)

    endpoint = "host" if method == "ip" else "dns/domain"

    logger.debug("Checking %s %s with Shodan", method, ioc)

    client = get_client()
    response = await client.get(
        url=f"https://api.shodan.io/shodan/{endpoint}/{ioc}", params={"key": apikey}
    )
    return await handle_response("Shodan", response)


async def check_leakix(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform a host lookup using the LeakIX API - open services and any leaks found on it"""
    _require_apikey("LeakIX", apikey)
    logger.debug("Checking IP %s with LeakIX", ioc)

    client = get_client()
    response = await client.get(
        url=f"https://leakix.net/host/{ioc}",
        headers={"api-key": apikey, "Accept": "application/json"},
    )
    return await handle_response("LeakIX", response)


async def check_threatfox(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IOC lookup using ThreatFox API"""
    _require_apikey("ThreatFox", apikey)
    logger.debug("Checking IOC %s with ThreatFox", ioc)

    client = get_client()
    response = await client.post(
        url="https://threatfox-api.abuse.ch/api/v1/",
        headers={"API-KEY": apikey},
        json={"query": "search_ioc", "search_term": ioc},
    )
    return await handle_response("ThreatFox", response)


async def search_twitter(ioc: str, apikey: str) -> dict[str, Any]:
    """Search for IOC mentions on Twitter/X using Twitter API v2"""
    _require_apikey("Twitter/X", apikey)
    logger.debug("Searching for IOC %s on Twitter/X", ioc)

    client = get_client()
    response = await client.get(
        url="https://api.twitter.com/2/tweets/search/recent",
        params={"query": f'"{ioc}" -is:retweet'},
        headers={"Authorization": f"Bearer {apikey}"},
    )
    return await handle_response("Twitter/X", response)


async def check_urlhaus(ioc: str) -> dict[str, Any]:
    """Perform URL lookup using URLhaus API"""
    logger.debug("Checking URL %s with URLhaus", ioc)

    client = get_client()
    response = await client.post(url="https://urlhaus-api.abuse.ch/v1/url/", data={"url": ioc})
    return await handle_response("URLhaus", response)


_OPENPHISH_FEED_URL = "https://openphish.com/feed.txt"
_OPENPHISH_CACHE_TTL_SECONDS = 3600  # community feed updates every few hours
_openphish_cache: dict[str, Any] = {"urls": None, "domains": None, "fetched_at": 0.0}
_openphish_cache_lock = asyncio.Lock()


async def _get_openphish_feed() -> tuple[set[str], set[str]]:
    """Fetch and cache OpenPhish's free community feed (one phishing URL per line).

    The free tier has no per-URL lookup endpoint, so this mirrors the CISA KEV catalog
    cache: the whole feed is refreshed on a TTL rather than re-downloaded per lookup.
    """
    async with _openphish_cache_lock:
        urls = _openphish_cache["urls"]
        age = time.monotonic() - _openphish_cache["fetched_at"]
        if urls is not None and age < _OPENPHISH_CACHE_TTL_SECONDS:
            return urls, _openphish_cache["domains"]

        client = get_client()
        try:
            response = await client.get(url=_OPENPHISH_FEED_URL)
            response.raise_for_status()
        except httpx.HTTPStatusError as http_err:
            raise ServiceError(
                "OpenPhish", f"OpenPhish error: HTTP {http_err.response.status_code}"
            ) from http_err
        except httpx.RequestError as req_err:
            raise ServiceUnavailableError(
                "OpenPhish", f"Could not connect to OpenPhish: {req_err}"
            ) from req_err

        lines = [line.strip() for line in response.text.splitlines() if line.strip()]
        urls = set(lines)
        domains = {hostname.lower() for line in lines if (hostname := urlsplit(line).hostname)}

        _openphish_cache["urls"] = urls
        _openphish_cache["domains"] = domains
        _openphish_cache["fetched_at"] = time.monotonic()
        return urls, domains


async def check_openphish(ioc: str) -> dict[str, Any]:
    """Check a URL or bare domain against OpenPhish's free community phishing feed"""
    logger.debug("Checking %s against OpenPhish community feed", ioc)

    urls, domains = await _get_openphish_feed()

    if "://" in ioc:
        matched_urls = [ioc] if ioc in urls else []
    elif ioc.lower() in domains:
        matched_urls = sorted(u for u in urls if urlsplit(u).hostname == ioc.lower())[:10]
    else:
        matched_urls = []

    return {"listed": bool(matched_urls), "matched_urls": matched_urls}


async def check_urlscan(ioc: str) -> dict[str, Any]:
    """Search for IOC information using URLScan.io API"""
    logger.debug("Searching for IOC %s on URLScan.io", ioc)

    client = get_client()
    response = await client.get(
        url="https://urlscan.io/api/v1/search/",
        params={"q": f'page.ip:"{ioc}" OR page.domain:"{ioc}"'},
    )
    return await handle_response("URLScan.io", response)


async def check_virustotal(ioc: str, ioc_type: str, apikey: str) -> dict[str, Any]:
    """Perform IOC lookup using VirusTotal API v3"""
    _require_apikey("VirusTotal", apikey)

    type_map = {"ip": "ip_addresses", "domain": "domains", "url": "urls", "hash": "files"}
    indicator_type = type_map.get(ioc_type, "ip_addresses")

    if indicator_type == "urls":
        ioc_safe = b64encode(ioc.encode()).decode().strip("=")
    else:
        ioc_safe = ioc

    logger.debug("Checking %s %s with VirusTotal", ioc_type, ioc)

    client = get_client()
    response = await client.get(
        url=f"https://www.virustotal.com/api/v3/{indicator_type}/{ioc_safe}",
        headers={"x-apikey": apikey},
    )
    if response.status_code == 404:
        raise ServiceError("VirusTotal", "Not found on VirusTotal", status_code=404)
    return await handle_response("VirusTotal", response)


async def check_blacklist(ioc: str, db: AsyncSession) -> dict[str, Any]:
    """Check a crypto address against the locally-stored OFAC SDN + ScamSniffer + OpenSanctions
    (il_mod_crypto) blacklist.

    Resolves instantly from the local DB (no external call), populated on a schedule
    by blacklist_refresh_service.refresh_blacklist.
    """
    normalized = normalize_address(ioc)
    logger.debug("Checking address %s against local blacklist", normalized)

    result = await db.execute(
        select(BlacklistedAddress).where(
            BlacklistedAddress.address == normalized, BlacklistedAddress.is_active.is_(True)
        )
    )
    matches = result.scalars().all()

    ofac_match = next((m for m in matches if m.source == BlacklistSource.OFAC.value), None)
    scamsniffer_match = next(
        (m for m in matches if m.source == BlacklistSource.SCAMSNIFFER.value), None
    )
    opensanctions_match = next(
        (m for m in matches if m.source == BlacklistSource.OPENSANCTIONS.value), None
    )

    return {
        "address": normalized,
        "matched": bool(matches),
        "sources": [m.source for m in matches],
        "ofac": {
            "entity_name": ofac_match.entity_name,
            "program": ofac_match.label,
            "chain": ofac_match.chain,
            "remarks": (ofac_match.details or {}).get("remarks"),
        }
        if ofac_match
        else None,
        "scamsniffer": {
            "chain": scamsniffer_match.chain,
            "phishing_domain": (scamsniffer_match.details or {}).get("phishing_domain"),
        }
        if scamsniffer_match
        else None,
        "opensanctions": {
            "chain": opensanctions_match.chain,
            "topics": opensanctions_match.label,
            "holder_name": opensanctions_match.entity_name,
            "dataset": (opensanctions_match.details or {}).get("dataset"),
            "profile_url": (opensanctions_match.details or {}).get("profile_url"),
        }
        if opensanctions_match
        else None,
    }
