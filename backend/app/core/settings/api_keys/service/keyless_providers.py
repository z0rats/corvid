"""Names of ioc_lookup providers that need no API key, exposed here so api_keys settings
routes don't have to import from ioc_tools (settings is a lower-level module than features)."""

_keyless_names: set[str] = set()


def set_keyless_provider_names(names: set[str]) -> None:
    global _keyless_names
    _keyless_names = names


def is_keyless_provider(name: str) -> bool:
    return name in _keyless_names


def get_keyless_provider_names() -> set[str]:
    return _keyless_names
