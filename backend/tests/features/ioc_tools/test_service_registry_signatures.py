import inspect

import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.service import external_api_clients as service_functions
from app.features.ioc_tools.ioc_lookup.single_lookup.service.ioc_lookup_engine import (
    _get_required_key_names, _prepare_function_args,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.service_registry import (
    register_services, get_all_services,
)

register_services(service_functions)


@pytest.mark.parametrize("service_name", sorted(get_all_services().keys()))
def test_prepared_args_match_function_signature(service_name):
    config = get_all_services()[service_name]
    required_keys = _get_required_key_names(config)
    api_keys = {key: f"fake-{key}" for key in required_keys}
    ioc_type = config['supported_ioc_types'][0]
    extra_args = {'db': None} if config.get('requires_db') else None

    prepared = _prepare_function_args(config, "1.2.3.4", ioc_type, api_keys, extra_args)
    real_params = set(inspect.signature(config['func']).parameters.keys())

    assert set(prepared.keys()) == real_params, (
        f"{service_name}: prepared args {sorted(prepared)} != "
        f"function params {sorted(real_params)}"
    )
