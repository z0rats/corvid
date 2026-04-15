import asyncio
import logging
from base64 import b64encode
from typing import Any

from app.core.config.settings import settings
from .client_base import (
    ServiceError,
    ServiceAuthError,
    ServiceRateLimitError,
    ServiceUnavailableError,
    get_client,
    close_client,
    handle_response,
    _require_apikey,
    _require_credentials,
    _authenticate_oauth,
)

logger = logging.getLogger(__name__)


async def check_abuseipdb(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IP reputation lookup using AbuseIPDB API"""
    _require_apikey("AbuseIPDB", apikey)
    logger.debug("Checking IP %s with AbuseIPDB", ioc)

    client = get_client()
    response = await client.get(
        url='https://api.abuseipdb.com/api/v2/check',
        params={'ipAddress': ioc, 'maxAgeInDays': '90', 'verbose': True},
        headers={'Accept': 'application/json', 'Key': apikey}
    )
    return await handle_response("AbuseIPDB", response)


_ALIENVAULT_SECTIONS: dict[str, list[str]] = {
    'ip': ['reputation', 'malware'],
    'domain': ['malware'],
    'url': ['url_list'],
    'hash': ['analysis'],
}


async def _fetch_alienvault_section(
    client, indicator_type: str, ioc: str, section: str, headers: dict[str, str]
) -> tuple[str, dict[str, Any] | None]:
    """Fetch a single OTX section with a tight timeout"""
    try:
        params = {'limit': 25} if section in ('passive_dns', 'malware', 'url_list') else {}
        response = await client.get(
            url=f'https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{ioc}/{section}',
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

    type_map = {'ip': 'IPv4', 'domain': 'domain', 'url': 'url', 'hash': 'file'}
    indicator_type = type_map.get(ioc_type, 'IPv4')
    headers = {'X-OTX-API-KEY': apikey}

    logger.debug("Checking %s %s with AlienVault OTX", indicator_type, ioc)

    client = get_client()
    extra_sections = _ALIENVAULT_SECTIONS.get(ioc_type, [])

    all_tasks = [
        _fetch_alienvault_section(client, indicator_type, ioc, 'general', headers),
        *[_fetch_alienvault_section(client, indicator_type, ioc, s, headers) for s in extra_sections],
    ]
    all_results = await asyncio.gather(*all_tasks)

    general_section_name, general_data = all_results[0]
    if general_data is None:
        response = await client.get(
            url=f'https://otx.alienvault.com/api/v1/indicators/{indicator_type}/{ioc}/general',
            headers=headers,
        )
        general_data = await handle_response("AlienVault OTX", response)

    result = general_data
    for section_name, section_data in all_results[1:]:
        if section_data is not None:
            result[f'section_{section_name}'] = section_data

    return result


async def check_checkphish(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform URL/domain phishing check using CheckPhish API"""
    _require_apikey("CheckPhish", apikey)
    logger.debug("Checking URL %s with CheckPhish", ioc)

    client = get_client()
    response = await client.post(
        url='https://developers.checkphish.ai/api/neo/scan',
        json={'apiKey': apikey, 'urlInfo': {'url': ioc}}
    )
    return await handle_response("CheckPhish", response)


async def check_crowdsec(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IP reputation lookup using CrowdSec CTI API"""
    _require_apikey("CrowdSec", apikey)
    logger.debug("Checking IP %s with CrowdSec", ioc)

    client = get_client()
    response = await client.get(
        url=f'https://cti.api.crowdsec.net/v2/smoke/{ioc}',
        headers={'x-api-key': apikey}
    )
    return await handle_response("CrowdSec", response)


async def check_crowdstrike(ioc: str, client_id: str, client_secret: str) -> dict[str, Any]:
    """Perform IOC lookup using CrowdStrike Falcon Intelligence API"""
    _require_credentials("CrowdStrike", client_id=client_id, client_secret=client_secret)
    logger.debug("Authenticating with CrowdStrike")

    access_token = await _authenticate_oauth(
        "CrowdStrike",
        'https://api.crowdstrike.com/oauth2/token',
        data={'client_id': client_id, 'client_secret': client_secret},
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
    )

    logger.debug("Looking up IOC %s with CrowdStrike", ioc)

    client = get_client()
    response = await client.get(
        url='https://api.crowdstrike.com/intel/combined/indicators/v1',
        params={'filter': f"indicator:'{ioc}'"},
        headers={'Authorization': f'Bearer {access_token}'}
    )
    return await handle_response("CrowdStrike", response)


async def check_emailrep(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform email reputation lookup using EmailRep.io API"""
    _require_apikey("EmailRep.io", apikey)
    logger.debug("Checking email %s with EmailRep.io", ioc)

    client = get_client()
    response = await client.get(
        url=f'https://emailrep.io/{ioc}',
        headers={'Key': apikey, 'User-Agent': 'OSINT-Toolkit'}
    )
    return await handle_response("EmailRep.io", response)


async def search_github(ioc: str, access_token: str) -> dict[str, Any]:
    """Search for IOC mentions in GitHub code repositories"""
    _require_apikey("GitHub", access_token)
    logger.debug("Searching for IOC %s on GitHub", ioc)

    client = get_client()
    response = await client.get(
        url='https://api.github.com/search/code',
        params={'q': f'"{ioc}"'},
        headers={'Authorization': f'Bearer {access_token}', 'Accept': 'application/vnd.github.v3+json'}
    )
    return await handle_response("GitHub", response)


async def check_hibp(ioc: str, apikey: str) -> dict[str, Any]:
    """Check if email address appears in known data breaches using HIBP API"""
    _require_apikey("HIBP", apikey)
    logger.debug("Checking email %s with HIBP", ioc)

    client = get_client()
    response = await client.get(
        url=f'https://haveibeenpwned.com/api/v3/breachedaccount/{ioc}',
        headers={'hibp-api-key': apikey, 'User-Agent': 'OSINT-Toolkit'}
    )
    if response.status_code == 404:
        return {"message": "Not found in any breaches."}
    return await handle_response("HIBP", response)


async def check_hunter(ioc: str, apikey: str) -> dict[str, Any]:
    """Verify email address using Hunter.io API"""
    _require_apikey("Hunter.io", apikey)
    logger.debug("Verifying email %s with Hunter.io", ioc)

    client = get_client()
    response = await client.get(
        url='https://api.hunter.io/v2/email-verifier',
        params={'email': ioc, 'api_key': apikey}
    )
    return await handle_response("Hunter.io", response)


async def check_ipqualityscore(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IP quality and fraud scoring using IPQualityScore API"""
    _require_apikey("IPQualityScore", apikey)
    logger.debug("Checking IP %s with IPQualityScore", ioc)

    client = get_client()
    response = await client.get(url=f'https://www.ipqualityscore.com/api/json/ip/{apikey}/{ioc}')
    return await handle_response("IPQualityScore", response)


async def check_maltiverse(ioc: str, endpoint: str, apikey: str) -> dict[str, Any]:
    """Perform IOC lookup using Maltiverse API"""
    _require_apikey("Maltiverse", apikey)
    logger.debug("Checking %s %s with Maltiverse", endpoint, ioc)

    client = get_client()
    response = await client.get(
        url=f'https://api.maltiverse.com/{endpoint}/{ioc}',
        headers={'Authorization': f'Bearer {apikey}'}
    )
    return await handle_response("Maltiverse", response)


async def check_malwarebazaar(ioc: str) -> dict[str, Any]:
    """Perform hash lookup using MalwareBazaar API"""
    logger.debug("Checking hash %s with MalwareBazaar", ioc)

    client = get_client()
    response = await client.post(
        url='https://mb-api.abuse.ch/api/v1/',
        data={'query': 'get_info', 'hash': ioc}
    )
    return await handle_response("MalwareBazaar", response)


async def check_mandiant(ioc: str, ioc_type: str, api_key: str, api_secret: str) -> dict[str, Any]:
    """Perform IOC lookup using Mandiant Advantage API"""
    _require_credentials("Mandiant", api_key=api_key, api_secret=api_secret)
    logger.debug("Authenticating with Mandiant")

    access_token = await _authenticate_oauth(
        "Mandiant",
        'https://api.intelligence.mandiant.com/token',
        data={'grant_type': 'client_credentials', 'client_id': api_key, 'client_secret': api_secret},
    )

    logger.debug("Looking up %s %s with Mandiant", ioc_type, ioc)

    client = get_client()
    response = await client.post(
        url='https://api.intelligence.mandiant.com/v4/indicator',
        headers={'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json', 'Accept': 'application/json'},
        json={"requests": [{"type": ioc_type, "value": ioc}]}
    )
    return await handle_response("Mandiant", response)


async def search_nist_nvd(ioc: str, apikey: str) -> dict[str, Any]:
    """Search for CVE information using NIST NVD API"""
    _require_apikey("NIST NVD", apikey)
    logger.debug("Looking up CVE %s with NIST NVD", ioc)

    client = get_client()
    response = await client.get(
        url='https://services.nvd.nist.gov/rest/json/cves/2.0',
        params={'cveId': ioc},
        headers={'apiKey': apikey}
    )
    return await handle_response("NIST NVD", response)


async def check_pulsedive(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IOC lookup using Pulsedive API"""
    _require_apikey("Pulsedive", apikey)
    logger.debug("Checking IOC %s with Pulsedive", ioc)

    client = get_client()
    response = await client.get(
        url='https://pulsedive.com/api/info.php',
        params={'indicator': ioc, 'key': apikey, 'pretty': '1'}
    )
    return await handle_response("Pulsedive", response)


async def search_reddit(ioc: str, client_id: str, client_secret: str) -> dict[str, Any]:
    """Search for IOC mentions on Reddit using Reddit API"""
    _require_credentials("Reddit", client_id=client_id, client_secret=client_secret)
    logger.debug("Authenticating with Reddit")

    access_token = await _authenticate_oauth(
        "Reddit",
        'https://www.reddit.com/api/v1/access_token',
        data={'grant_type': 'client_credentials'},
        headers={'User-Agent': 'OSINT-Toolkit/0.1'},
        auth=(client_id, client_secret),
    )

    logger.debug("Searching for IOC %s on Reddit", ioc)

    client = get_client()
    response = await client.get(
        url='https://oauth.reddit.com/search',
        params={'q': f'"{ioc}"', 'limit': 25},
        headers={'Authorization': f'bearer {access_token}', 'User-Agent': 'OSINT-Toolkit/0.1'}
    )
    raw = await handle_response("Reddit", response)

    children = raw.get("data", {}).get("children", [])
    posts = [
        {
            "id": child["data"].get("id"),
            "title": child["data"].get("title"),
            "author": child["data"].get("author"),
            "subreddit": child["data"].get("subreddit_name_prefixed") or child["data"].get("subreddit"),
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
        "client": {"clientId": "osint-toolkit", "clientVersion": settings.api.version},
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE", "POTENTIALLY_HARMFUL_APPLICATION"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": ioc}]
        }
    }
    client = get_client()
    response = await client.post(
        url='https://safebrowsing.googleapis.com/v4/threatMatches:find',
        params={'key': apikey},
        json=payload
    )
    return await handle_response("Google Safe Browse", response)


async def check_shodan(ioc: str, method: str, apikey: str) -> dict[str, Any]:
    """Perform IP or domain lookup using Shodan API"""
    _require_apikey("Shodan", apikey)

    endpoint = 'host' if method == 'ip' else 'dns/domain'

    logger.debug("Checking %s %s with Shodan", method, ioc)

    client = get_client()
    response = await client.get(
        url=f'https://api.shodan.io/shodan/{endpoint}/{ioc}',
        params={'key': apikey}
    )
    return await handle_response("Shodan", response)


async def check_threatfox(ioc: str, apikey: str) -> dict[str, Any]:
    """Perform IOC lookup using ThreatFox API"""
    _require_apikey("ThreatFox", apikey)
    logger.debug("Checking IOC %s with ThreatFox", ioc)

    client = get_client()
    response = await client.post(
        url='https://threatfox-api.abuse.ch/api/v1/',
        headers={'API-KEY': apikey},
        json={'query': 'search_ioc', 'search_term': ioc}
    )
    return await handle_response("ThreatFox", response)


async def search_twitter(ioc: str, apikey: str) -> dict[str, Any]:
    """Search for IOC mentions on Twitter/X using Twitter API v2"""
    _require_apikey("Twitter/X", apikey)
    logger.debug("Searching for IOC %s on Twitter/X", ioc)

    client = get_client()
    response = await client.get(
        url='https://api.twitter.com/2/tweets/search/recent',
        params={'query': f'"{ioc}" -is:retweet'},
        headers={'Authorization': f'Bearer {apikey}'}
    )
    return await handle_response("Twitter/X", response)


async def check_urlhaus(ioc: str) -> dict[str, Any]:
    """Perform URL lookup using URLhaus API"""
    logger.debug("Checking URL %s with URLhaus", ioc)

    client = get_client()
    response = await client.post(
        url='https://urlhaus-api.abuse.ch/v1/url/',
        data={'url': ioc}
    )
    return await handle_response("URLhaus", response)


async def check_urlscan(ioc: str) -> dict[str, Any]:
    """Search for IOC information using URLScan.io API"""
    logger.debug("Searching for IOC %s on URLScan.io", ioc)

    client = get_client()
    response = await client.get(
        url='https://urlscan.io/api/v1/search/',
        params={'q': f'page.ip:"{ioc}" OR page.domain:"{ioc}"'}
    )
    return await handle_response("URLScan.io", response)


async def check_virustotal(ioc: str, ioc_type: str, apikey: str) -> dict[str, Any]:
    """Perform IOC lookup using VirusTotal API v3"""
    _require_apikey("VirusTotal", apikey)

    type_map = {'ip': 'ip_addresses', 'domain': 'domains', 'url': 'urls', 'hash': 'files'}
    indicator_type = type_map.get(ioc_type, 'ip_addresses')

    if indicator_type == 'urls':
        ioc_safe = b64encode(ioc.encode()).decode().strip("=")
    else:
        ioc_safe = ioc

    logger.debug("Checking %s %s with VirusTotal", ioc_type, ioc)

    client = get_client()
    response = await client.get(
        url=f'https://www.virustotal.com/api/v3/{indicator_type}/{ioc_safe}',
        headers={'x-apikey': apikey}
    )
    if response.status_code == 404:
        raise ServiceError("VirusTotal", "Not found on VirusTotal", status_code=404)
    return await handle_response("VirusTotal", response)
