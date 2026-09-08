import pytest

from app.core.settings.api_keys.config.service_config import get_service_definition
from app.features.ioc_tools.ioc_lookup.single_lookup.service import (
    external_api_clients as service_functions,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.provider_spec import (
    validate_provider_spec,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import (
    get_all_services,
    register_services,
)

register_services(service_functions)


@pytest.mark.parametrize("service_name", sorted(get_all_services().keys()))
def test_provider_spec_matches_function_signature(service_name):
    spec = get_all_services()[service_name]
    validate_provider_spec(spec)


# service_registry.py provider keys that don't map 1:1 onto a service_config.py
# SERVICE_DEFINITIONS key.
_SERVICE_CONFIG_KEY_OVERRIDES = {"checkphish": "checkphishai"}

# Fully keyless providers with no Settings entry (nothing to configure, so no
# ServiceDefinition exists to compare against).
_NO_SERVICE_CONFIG_ENTRY = {
    "cisakev",
    "ffraud",
    "ffraudemail",
    "firstepss",
    "hudsonrock",
    "libraryofleaks",
    "openphish",
}


@pytest.mark.parametrize("service_name", sorted(set(get_all_services()) - _NO_SERVICE_CONFIG_ENTRY))
def test_supported_ioc_types_match_service_config(service_name):
    """A provider's dispatch coverage (service_registry.py) and its Settings-page
    description (service_config.py) must agree on which IOC types it supports —
    otherwise the Settings page promises coverage the app never actually queries
    for, or vice versa (this caught AbuseIPDB claiming IPv4-only dispatch while
    Settings advertised IPv6 too). Add a provider to _NO_SERVICE_CONFIG_ENTRY only
    if it's genuinely keyless and has no ServiceDefinition to compare against."""
    spec = get_all_services()[service_name]
    config_key = _SERVICE_CONFIG_KEY_OVERRIDES.get(service_name, service_name)
    definition = get_service_definition(config_key)
    assert definition is not None, (
        f"{service_name!r} has no ServiceDefinition ({config_key!r}) in service_config.py — "
        "add one, or add this provider to _NO_SERVICE_CONFIG_ENTRY if it's genuinely keyless"
    )
    assert set(spec.supported_ioc_types) == set(definition.supported_ioc_types), (
        f"{service_name!r}: service_registry.py says {sorted(spec.supported_ioc_types)}, "
        f"service_config.py says {sorted(definition.supported_ioc_types)}"
    )
