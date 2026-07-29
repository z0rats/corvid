import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.service import external_api_clients as service_functions
from app.features.ioc_tools.ioc_lookup.single_lookup.service.provider_spec import validate_provider_spec
from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import (
    register_services, get_all_services,
)

register_services(service_functions)


@pytest.mark.parametrize("service_name", sorted(get_all_services().keys()))
def test_provider_spec_matches_function_signature(service_name):
    spec = get_all_services()[service_name]
    validate_provider_spec(spec)
