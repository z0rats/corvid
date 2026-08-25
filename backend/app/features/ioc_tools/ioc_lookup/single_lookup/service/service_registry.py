from app.features.ioc_tools.ioc_lookup.single_lookup.service.provider_spec import (
    ApiKeySpec,
    MultiApiKeySpec,
    ProviderSpec,
    TypeMapping,
    validate_provider_spec,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import IOC_TYPES

# Global service registry
_services: dict[str, ProviderSpec] = {}


def register_services(ioc_lookup_service_module) -> None:
    """
    Register all IOC lookup services with their configurations.

    Args:
        ioc_lookup_service_module: Module containing the service functions
    """
    global _services

    providers = {
        "abuseipdb": ProviderSpec(
            func=ioc_lookup_service_module.check_abuseipdb,
            name="AbuseIPDB",
            supported_ioc_types=[IOC_TYPES["IPV4"]],
            api_key=ApiKeySpec(setting_name="abuseipdb"),
        ),
        "alienvault": ProviderSpec(
            func=ioc_lookup_service_module.check_alienvault,
            name="AlienVault OTX",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["IPV6"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
            ],
            api_key=ApiKeySpec(setting_name="alienvault"),
            type_mapping=TypeMapping(
                param="ioc_type",
                values={
                    IOC_TYPES["IPV4"]: "ip",
                    IOC_TYPES["IPV6"]: "ip",
                    IOC_TYPES["DOMAIN"]: "domain",
                    IOC_TYPES["URL"]: "url",
                    IOC_TYPES["MD5"]: "hash",
                    IOC_TYPES["SHA1"]: "hash",
                    IOC_TYPES["SHA256"]: "hash",
                },
            ),
        ),
        "blacklist": ProviderSpec(
            func=ioc_lookup_service_module.check_blacklist,
            name="Address Blacklist",
            supported_ioc_types=[
                IOC_TYPES["EVM_ADDRESS"],
                IOC_TYPES["BITCOIN_ADDRESS"],
                IOC_TYPES["TRON_ADDRESS"],
                IOC_TYPES["XRP_ADDRESS"],
                IOC_TYPES["DOGECOIN_ADDRESS"],
                IOC_TYPES["LITECOIN_ADDRESS"],
                IOC_TYPES["STELLAR_ADDRESS"],
                IOC_TYPES["BINANCE_CHAIN_ADDRESS"],
                IOC_TYPES["LISK_ADDRESS"],
                IOC_TYPES["CARDANO_ADDRESS"],
            ],
            requires_db=True,
        ),
        "cisakev": ProviderSpec(
            func=ioc_lookup_service_module.check_cisa_kev,
            name="CISA KEV",
            supported_ioc_types=[IOC_TYPES["CVE"]],
        ),
        "checkphish": ProviderSpec(
            func=ioc_lookup_service_module.check_checkphish,
            name="CheckPhish",
            supported_ioc_types=[IOC_TYPES["IPV4"], IOC_TYPES["DOMAIN"], IOC_TYPES["URL"]],
            api_key=ApiKeySpec(setting_name="checkphishai"),
        ),
        "crowdsec": ProviderSpec(
            func=ioc_lookup_service_module.check_crowdsec,
            name="CrowdSec",
            supported_ioc_types=[IOC_TYPES["IPV4"]],
            api_key=ApiKeySpec(setting_name="crowdsec"),
        ),
        "crowdstrike": ProviderSpec(
            func=ioc_lookup_service_module.check_crowdstrike,
            name="CrowdStrike",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["IPV6"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
                IOC_TYPES["EMAIL"],
            ],
            api_key=MultiApiKeySpec(
                {
                    "client_id": "crowdstrike_client_id",
                    "client_secret": "crowdstrike_client_secret",
                }
            ),
        ),
        "emailrepio": ProviderSpec(
            func=ioc_lookup_service_module.check_emailrep,
            name="EmailRep.io",
            supported_ioc_types=[IOC_TYPES["EMAIL"]],
            api_key=ApiKeySpec(setting_name="emailrepio"),
        ),
        "ffraud": ProviderSpec(
            func=ioc_lookup_service_module.check_ffraud,
            name="FFraud",
            supported_ioc_types=[IOC_TYPES["IPV4"], IOC_TYPES["IPV6"]],
        ),
        "ffraudemail": ProviderSpec(
            func=ioc_lookup_service_module.check_ffraud_email,
            name="FFraud",
            supported_ioc_types=[IOC_TYPES["EMAIL"]],
        ),
        "firstepss": ProviderSpec(
            func=ioc_lookup_service_module.search_first_epss,
            name="FIRST.org EPSS",
            supported_ioc_types=[IOC_TYPES["CVE"]],
        ),
        "github": ProviderSpec(
            func=ioc_lookup_service_module.search_github,
            name="GitHub",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["IPV6"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["EMAIL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
                IOC_TYPES["CVE"],
            ],
            api_key=ApiKeySpec(setting_name="github_pat", param="access_token"),
        ),
        "haveibeenpwned": ProviderSpec(
            func=ioc_lookup_service_module.check_hibp,
            name="Have I Been Pwned",
            supported_ioc_types=[IOC_TYPES["EMAIL"]],
            api_key=ApiKeySpec(setting_name="hibp_api_key"),
        ),
        "hudsonrock": ProviderSpec(
            func=ioc_lookup_service_module.check_hudsonrock,
            name="Hudson Rock",
            supported_ioc_types=[IOC_TYPES["EMAIL"], IOC_TYPES["IPV4"], IOC_TYPES["DOMAIN"]],
            type_mapping=TypeMapping(
                param="ioc_type",
                values={
                    IOC_TYPES["EMAIL"]: "email",
                    IOC_TYPES["IPV4"]: "ip",
                    IOC_TYPES["DOMAIN"]: "domain",
                },
            ),
        ),
        "hunterio": ProviderSpec(
            func=ioc_lookup_service_module.check_hunter,
            name="Hunter.io",
            supported_ioc_types=[IOC_TYPES["EMAIL"]],
            api_key=ApiKeySpec(setting_name="hunterio_api_key"),
        ),
        "ipqualityscore": ProviderSpec(
            func=ioc_lookup_service_module.check_ipqualityscore,
            name="IPQualityScore",
            supported_ioc_types=[IOC_TYPES["IPV4"]],
            api_key=ApiKeySpec(setting_name="ipqualityscore"),
        ),
        "libraryofleaks": ProviderSpec(
            func=ioc_lookup_service_module.check_libraryofleaks,
            name="Library of Leaks",
            supported_ioc_types=[IOC_TYPES["EMAIL"], IOC_TYPES["DOMAIN"]],
            bulk_enabled=False,
        ),
        "maltiverse": ProviderSpec(
            func=ioc_lookup_service_module.check_maltiverse,
            name="Maltiverse",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
            ],
            api_key=ApiKeySpec(setting_name="maltiverse"),
            type_mapping=TypeMapping(
                param="endpoint",
                values={
                    IOC_TYPES["IPV4"]: "ip",
                    IOC_TYPES["DOMAIN"]: "hostname",
                    IOC_TYPES["URL"]: "url",
                    IOC_TYPES["MD5"]: "sample/md5",
                    IOC_TYPES["SHA1"]: "sample/sha1",
                    IOC_TYPES["SHA256"]: "sample",
                },
            ),
        ),
        "malwarebazaar": ProviderSpec(
            func=ioc_lookup_service_module.check_malwarebazaar,
            name="MalwareBazaar",
            supported_ioc_types=[IOC_TYPES["MD5"], IOC_TYPES["SHA1"], IOC_TYPES["SHA256"]],
        ),
        "mandiant": ProviderSpec(
            func=ioc_lookup_service_module.check_mandiant,
            name="Mandiant",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["IPV6"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
                IOC_TYPES["EMAIL"],
            ],
            api_key=MultiApiKeySpec({"api_key": "mandiant_key", "api_secret": "mandiant_secret"}),
            type_mapping=TypeMapping(
                param="ioc_type",
                values={
                    IOC_TYPES["IPV4"]: "ip",
                    IOC_TYPES["IPV6"]: "ip",
                    IOC_TYPES["DOMAIN"]: "domain",
                    IOC_TYPES["URL"]: "url",
                    IOC_TYPES["MD5"]: "hash",
                    IOC_TYPES["SHA1"]: "hash",
                    IOC_TYPES["SHA256"]: "hash",
                    IOC_TYPES["EMAIL"]: "email",
                },
            ),
        ),
        "nistnvd": ProviderSpec(
            func=ioc_lookup_service_module.search_nist_nvd,
            name="NIST NVD",
            supported_ioc_types=[IOC_TYPES["CVE"]],
            api_key=ApiKeySpec(setting_name="nist_nvd_api_key"),
        ),
        "openphish": ProviderSpec(
            func=ioc_lookup_service_module.check_openphish,
            name="OpenPhish",
            supported_ioc_types=[IOC_TYPES["DOMAIN"], IOC_TYPES["URL"]],
        ),
        "pulsedive": ProviderSpec(
            func=ioc_lookup_service_module.check_pulsedive,
            name="Pulsedive",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
            ],
            api_key=ApiKeySpec(setting_name="pulsedive"),
        ),
        "reddit": ProviderSpec(
            func=ioc_lookup_service_module.search_reddit,
            name="Reddit",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["IPV6"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["EMAIL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
                IOC_TYPES["CVE"],
            ],
            api_key=MultiApiKeySpec(
                {
                    "client_id": "reddit_client_id",
                    "client_secret": "reddit_client_secret",
                }
            ),
        ),
        "safeBrowse": ProviderSpec(
            func=ioc_lookup_service_module.check_safe_browsing,
            name="Google Safe Browse",
            supported_ioc_types=[IOC_TYPES["DOMAIN"], IOC_TYPES["URL"]],
            api_key=ApiKeySpec(setting_name="safeBrowse"),
        ),
        "shodan": ProviderSpec(
            func=ioc_lookup_service_module.check_shodan,
            name="Shodan",
            supported_ioc_types=[IOC_TYPES["IPV4"], IOC_TYPES["DOMAIN"]],
            api_key=ApiKeySpec(setting_name="shodan"),
            type_mapping=TypeMapping(
                param="method",
                values={
                    IOC_TYPES["IPV4"]: "ip",
                    IOC_TYPES["DOMAIN"]: "domain",
                },
            ),
        ),
        "leakix": ProviderSpec(
            func=ioc_lookup_service_module.check_leakix,
            name="LeakIX",
            supported_ioc_types=[IOC_TYPES["IPV4"]],
            api_key=ApiKeySpec(setting_name="leakix"),
        ),
        "threatfox": ProviderSpec(
            func=ioc_lookup_service_module.check_threatfox,
            name="ThreatFox",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["IPV6"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
            ],
            api_key=ApiKeySpec(setting_name="threatfox"),
        ),
        "twitter": ProviderSpec(
            func=ioc_lookup_service_module.search_twitter,
            name="Twitter/X",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["IPV6"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["EMAIL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
                IOC_TYPES["CVE"],
            ],
            api_key=ApiKeySpec(setting_name="twitter_bearer_token"),
        ),
        "urlhaus": ProviderSpec(
            func=ioc_lookup_service_module.check_urlhaus,
            name="URLhaus",
            supported_ioc_types=[IOC_TYPES["URL"], IOC_TYPES["DOMAIN"], IOC_TYPES["IPV4"]],
        ),
        "urlscanio": ProviderSpec(
            func=ioc_lookup_service_module.check_urlscan,
            name="URLScan.io",
            supported_ioc_types=[IOC_TYPES["DOMAIN"], IOC_TYPES["URL"], IOC_TYPES["IPV4"]],
        ),
        "virustotal": ProviderSpec(
            func=ioc_lookup_service_module.check_virustotal,
            name="VirusTotal",
            supported_ioc_types=[
                IOC_TYPES["IPV4"],
                IOC_TYPES["IPV6"],
                IOC_TYPES["DOMAIN"],
                IOC_TYPES["URL"],
                IOC_TYPES["MD5"],
                IOC_TYPES["SHA1"],
                IOC_TYPES["SHA256"],
            ],
            api_key=ApiKeySpec(setting_name="virustotal"),
            type_mapping=TypeMapping(
                param="ioc_type",
                values={
                    IOC_TYPES["IPV4"]: "ip",
                    IOC_TYPES["IPV6"]: "ip",
                    IOC_TYPES["DOMAIN"]: "domain",
                    IOC_TYPES["URL"]: "url",
                    IOC_TYPES["MD5"]: "hash",
                    IOC_TYPES["SHA1"]: "hash",
                    IOC_TYPES["SHA256"]: "hash",
                },
            ),
        ),
    }

    for spec in providers.values():
        validate_provider_spec(spec)

    _services.update(providers)


def get_service(service_name: str) -> ProviderSpec | None:
    """
    Get service configuration by name.

    Args:
        service_name: The name of the service to retrieve

    Returns:
        ProviderSpec for the service or None if not found
    """
    return _services.get(service_name)


def get_all_services() -> dict[str, ProviderSpec]:
    """
    Get all registered services.

    Returns:
        Dictionary of all service ProviderSpecs
    """
    return _services.copy()


def is_service_registered(service_name: str) -> bool:
    """
    Check if a service is registered.

    Args:
        service_name: The name of the service to check

    Returns:
        True if the service is registered, False otherwise
    """
    return service_name in _services
