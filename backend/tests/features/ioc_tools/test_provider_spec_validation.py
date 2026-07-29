import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.service.provider_spec import (
    ApiKeySpec, ProviderSpec, TypeMapping, validate_provider_spec,
)


async def _lookup(ioc: str, ioc_type: str, apikey: str) -> dict:
    return {}


def test_valid_spec_passes():
    spec = ProviderSpec(
        func=_lookup,
        name="Example",
        supported_ioc_types=["IPv4", "Domain"],
        api_key=ApiKeySpec(setting_name="example_key"),
        type_mapping=TypeMapping(param="ioc_type", values={"IPv4": "ip", "Domain": "domain"}),
    )
    validate_provider_spec(spec)


def test_type_mapping_missing_supported_type_raises():
    spec = ProviderSpec(
        func=_lookup,
        name="Example",
        supported_ioc_types=["IPv4", "Domain"],
        api_key=ApiKeySpec(setting_name="example_key"),
        type_mapping=TypeMapping(param="ioc_type", values={"IPv4": "ip"}),
    )
    with pytest.raises(ValueError, match="type_mapping missing entry"):
        validate_provider_spec(spec)


def test_api_key_param_not_matching_function_kwarg_raises():
    spec = ProviderSpec(
        func=_lookup,
        name="Example",
        supported_ioc_types=["IPv4"],
        api_key=ApiKeySpec(setting_name="example_key", param="access_token"),
        type_mapping=TypeMapping(param="ioc_type", values={"IPv4": "ip"}),
    )
    with pytest.raises(ValueError, match="built args"):
        validate_provider_spec(spec)
