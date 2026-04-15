from typing import Any
from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import IOC_TYPES

# Global service registry
_services: dict[str, dict[str, Any]] = {}


def register_services(ioc_lookup_service_module) -> None:
    """
    Register all IOC lookup services with their configurations.
    
    Args:
        ioc_lookup_service_module: Module containing the service functions
    """
    global _services
    
    _services.update({
        'abuseipdb': {
            'func': ioc_lookup_service_module.check_abuseipdb,
            'name': 'AbuseIPDB',
            'api_key_name': 'abuseipdb',
            'supported_ioc_types': [IOC_TYPES['IPV4']],
        },
        'alienvault': {
            'func': ioc_lookup_service_module.check_alienvault,
            'name': 'AlienVault OTX',
            'api_key_name': 'alienvault',
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['IPV6'], IOC_TYPES['DOMAIN'],
                IOC_TYPES['URL'], IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256']
            ],
            'requires_type': True,
            'ioc_type_param': 'ioc_type',
            'type_map': {
                IOC_TYPES['IPV4']: 'ip', IOC_TYPES['IPV6']: 'ip',
                IOC_TYPES['DOMAIN']: 'domain', IOC_TYPES['URL']: 'url',
                IOC_TYPES['MD5']: 'hash', IOC_TYPES['SHA1']: 'hash', IOC_TYPES['SHA256']: 'hash',
            }
        },
        'checkphish': {
            'func': ioc_lookup_service_module.check_checkphish,
            'name': 'CheckPhish',
            'api_key_name': 'checkphishai',
            'supported_ioc_types': [IOC_TYPES['IPV4'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL']],
        },
        'crowdsec': {
            'func': ioc_lookup_service_module.check_crowdsec,
            'name': 'CrowdSec',
            'api_key_name': 'crowdsec',
            'supported_ioc_types': [IOC_TYPES['IPV4']],
        },
        'crowdstrike': {
            'func': ioc_lookup_service_module.check_crowdstrike,
            'name': 'CrowdStrike',
            'multi_key': True,
            'api_key_names': ['crowdstrike_client_id', 'crowdstrike_client_secret'],
            'api_key_params': {
                'client_id': 'crowdstrike_client_id',
                'client_secret': 'crowdstrike_client_secret'
            },
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['IPV6'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL'],
                IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256'], IOC_TYPES['EMAIL']
            ],
        },
        'emailrepio': {
            'func': ioc_lookup_service_module.check_emailrep,
            'name': 'EmailRep.io',
            'api_key_name': 'emailrepio',
            'supported_ioc_types': [IOC_TYPES['EMAIL']],
        },
        'github': {
            'func': ioc_lookup_service_module.search_github,
            'name': 'GitHub',
            'api_key_name': 'github_pat',
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['IPV6'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL'],
                IOC_TYPES['EMAIL'], IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256'],
                IOC_TYPES['CVE']
            ],
        },
        'haveibeenpwned': {
            'func': ioc_lookup_service_module.check_hibp,
            'name': 'Have I Been Pwned',
            'api_key_name': 'hibp_api_key',
            'supported_ioc_types': [IOC_TYPES['EMAIL']],
        },
        'hunterio': {
            'func': ioc_lookup_service_module.check_hunter,
            'name': 'Hunter.io',
            'api_key_name': 'hunterio_api_key',
            'supported_ioc_types': [IOC_TYPES['EMAIL']],
        },
        'ipqualityscore': {
            'func': ioc_lookup_service_module.check_ipqualityscore,
            'name': 'IPQualityScore',
            'api_key_name': 'ipqualityscore',
            'supported_ioc_types': [IOC_TYPES['IPV4']],
        },
        'maltiverse': {
            'func': ioc_lookup_service_module.check_maltiverse,
            'name': 'Maltiverse',
            'api_key_name': 'maltiverse',
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL'],
                IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256']
            ],
            'requires_type': True,
            'ioc_type_param': 'endpoint',
            'type_map': {
                IOC_TYPES['IPV4']: 'ip',
                IOC_TYPES['DOMAIN']: 'hostname',
                IOC_TYPES['URL']: 'url',
                IOC_TYPES['MD5']: 'sample/md5',
                IOC_TYPES['SHA1']: 'sample/sha1',
                IOC_TYPES['SHA256']: 'sample',
            },
        },
        'malwarebazaar': {
            'func': ioc_lookup_service_module.check_malwarebazaar,
            'name': 'MalwareBazaar',
            'api_key_name': 'malwarebazaar',
            'supported_ioc_types': [IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256']],
        },
        'mandiant': {
            'func': ioc_lookup_service_module.check_mandiant,
            'name': 'Mandiant',
            'multi_key': True,
            'api_key_names': ['mandiant_key', 'mandiant_secret'],
            'api_key_params': {'api_key': 'mandiant_key', 'api_secret': 'mandiant_secret'},
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['IPV6'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL'],
                IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256'], IOC_TYPES['EMAIL']
            ],
            'requires_type': True,
            'ioc_type_param': 'ioc_type',
            'type_map': {
                IOC_TYPES['IPV4']: 'ip', IOC_TYPES['IPV6']: 'ip',
                IOC_TYPES['DOMAIN']: 'domain', IOC_TYPES['URL']: 'url',
                IOC_TYPES['MD5']: 'hash', IOC_TYPES['SHA1']: 'hash', IOC_TYPES['SHA256']: 'hash',
                IOC_TYPES['EMAIL']: 'email',
            }
        },
        'nistnvd': {
            'func': ioc_lookup_service_module.search_nist_nvd,
            'name': 'NIST NVD',
            'api_key_name': 'nist_nvd_api_key',
            'supported_ioc_types': [IOC_TYPES['CVE']],
        },
        'pulsedive': {
            'func': ioc_lookup_service_module.check_pulsedive,
            'name': 'Pulsedive',
            'api_key_name': 'pulsedive',
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL'],
                IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256']
            ],
        },
        'reddit': {
            'func': ioc_lookup_service_module.search_reddit,
            'name': 'Reddit',
            'multi_key': True,
            'api_key_names': ['reddit_client_id', 'reddit_client_secret'],
            'api_key_params': {'client_id': 'reddit_client_id', 'client_secret': 'reddit_client_secret'},
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['IPV6'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL'],
                IOC_TYPES['EMAIL'], IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256'],
                IOC_TYPES['CVE']
            ],
        },
        'safeBrowse': {
            'func': ioc_lookup_service_module.check_safe_browsing,
            'name': 'Google Safe Browse',
            'api_key_name': 'safeBrowse',
            'supported_ioc_types': [IOC_TYPES['DOMAIN'], IOC_TYPES['URL']],
        },
        'shodan': {
            'func': ioc_lookup_service_module.check_shodan,
            'name': 'Shodan',
            'api_key_name': 'shodan',
            'supported_ioc_types': [IOC_TYPES['IPV4'], IOC_TYPES['DOMAIN']],
            'requires_type': True,
            'ioc_type_param': 'method',
            'type_map': {
                IOC_TYPES['IPV4']: 'ip',
                IOC_TYPES['DOMAIN']: 'domain',
            }
        },
        'threatfox': {
            'func': ioc_lookup_service_module.check_threatfox,
            'name': 'ThreatFox',
            'api_key_name': 'threatfox',
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['IPV6'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL'],
                IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256']
            ],
        },
        'twitter': {
            'func': ioc_lookup_service_module.search_twitter,
            'name': 'Twitter/X',
            'api_key_name': 'twitter_bearer_token',
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['IPV6'], IOC_TYPES['DOMAIN'], IOC_TYPES['URL'],
                IOC_TYPES['EMAIL'], IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256'],
                IOC_TYPES['CVE']
            ],
        },
        'urlhaus': {
            'func': ioc_lookup_service_module.check_urlhaus,
            'name': 'URLhaus',
            'api_key_name': 'urlhaus',
            'supported_ioc_types': [IOC_TYPES['URL'], IOC_TYPES['DOMAIN'], IOC_TYPES['IPV4']],
        },
        'urlscanio': {
            'func': ioc_lookup_service_module.check_urlscan,
            'name': 'URLScan.io',
            'api_key_name': None,
            'supported_ioc_types': [IOC_TYPES['DOMAIN'], IOC_TYPES['URL'], IOC_TYPES['IPV4']],
        },
        'virustotal': {
            'func': ioc_lookup_service_module.check_virustotal,
            'name': 'VirusTotal',
            'api_key_name': 'virustotal',
            'supported_ioc_types': [
                IOC_TYPES['IPV4'], IOC_TYPES['IPV6'], IOC_TYPES['DOMAIN'],
                IOC_TYPES['URL'], IOC_TYPES['MD5'], IOC_TYPES['SHA1'], IOC_TYPES['SHA256']
            ],
            'requires_type': True,
            'ioc_type_param': 'ioc_type',
            'type_map': {
                IOC_TYPES['IPV4']: 'ip', IOC_TYPES['IPV6']: 'ip',
                IOC_TYPES['DOMAIN']: 'domain', IOC_TYPES['URL']: 'url',
                IOC_TYPES['MD5']: 'hash', IOC_TYPES['SHA1']: 'hash', IOC_TYPES['SHA256']: 'hash',
            }
        },
    })


def get_service(service_name: str) -> dict[str, Any] | None:
    """
    Get service configuration by name.
    
    Args:
        service_name: The name of the service to retrieve
        
    Returns:
        Service configuration dictionary or None if not found
    """
    return _services.get(service_name)


def get_all_services() -> dict[str, dict[str, Any]]:
    """
    Get all registered services.
    
    Returns:
        Dictionary of all service configurations
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
