import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

ProviderFunc = Callable[..., Awaitable[dict[str, Any]]]


@dataclass(frozen=True)
class ApiKeySpec:
    """A single API key. Sent as `apikey=<value>` unless `param` overrides the name."""

    setting_name: str
    param: str = "apikey"


@dataclass(frozen=True)
class MultiApiKeySpec:
    """Several API keys, each mapped to its own function kwarg."""

    params: dict[str, str]  # {function_kwarg: setting_name}


@dataclass(frozen=True)
class TypeMapping:
    """How the detected IOC type is passed to the provider function.

    `values` must have an entry for every type in the owning ProviderSpec's
    `supported_ioc_types` — enforced by `validate_provider_spec`, not left to an
    implicit `.lower()` fallback.
    """

    param: str
    values: dict[str, str]


@dataclass(frozen=True)
class ProviderSpec:
    func: ProviderFunc
    name: str
    supported_ioc_types: list[str]
    api_key: ApiKeySpec | MultiApiKeySpec | None = None
    type_mapping: TypeMapping | None = None
    requires_db: bool = False
    bulk_enabled: bool = True

    @property
    def required_key_names(self) -> list[str]:
        match self.api_key:
            case ApiKeySpec(setting_name=name):
                return [name]
            case MultiApiKeySpec(params=params):
                return list(params.values())
            case None:
                return []


def build_call_args(
    spec: ProviderSpec,
    ioc: str,
    ioc_type: str,
    api_keys: dict[str, str],
    extra_args: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the argument dict for a provider's lookup function."""
    args: dict[str, Any] = {"ioc": ioc.strip()}

    if spec.type_mapping is not None:
        args[spec.type_mapping.param] = spec.type_mapping.values[ioc_type]

    match spec.api_key:
        case ApiKeySpec(setting_name=name, param=param):
            args[param] = api_keys.get(name)
        case MultiApiKeySpec(params=params):
            for param, name in params.items():
                args[param] = api_keys.get(name)

    if extra_args:
        args.update(extra_args)

    return args


def validate_provider_spec(spec: ProviderSpec) -> None:
    """Raise ValueError if `spec` doesn't match its function's real signature for
    every supported IOC type, or if its type_mapping is missing a supported type."""
    fake_keys = {name: f"fake-{name}" for name in spec.required_key_names}
    extra = {"db": None} if spec.requires_db else None

    for ioc_type in spec.supported_ioc_types:
        if spec.type_mapping is not None and ioc_type not in spec.type_mapping.values:
            raise ValueError(
                f"{spec.name}: type_mapping missing entry for supported type {ioc_type!r}"
            )
        args = build_call_args(spec, "1.2.3.4", ioc_type, fake_keys, extra)
        real_params = set(inspect.signature(spec.func).parameters)
        if set(args) != real_params:
            raise ValueError(
                f"{spec.name}: built args {sorted(args)} != function params {sorted(real_params)}"
            )
