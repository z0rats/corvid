from app.core.settings.api_keys.service import keyless_providers


def teardown_function():
    keyless_providers.set_keyless_provider_names(set())


def test_defaults_to_empty():
    assert keyless_providers.get_keyless_provider_names() == set()
    assert keyless_providers.is_keyless_provider("urlscan") is False


def test_set_keyless_provider_names_replaces_the_set():
    keyless_providers.set_keyless_provider_names({"urlscan", "hudsonrock"})

    assert keyless_providers.get_keyless_provider_names() == {"urlscan", "hudsonrock"}
    assert keyless_providers.is_keyless_provider("urlscan") is True
    assert keyless_providers.is_keyless_provider("hudsonrock") is True
    assert keyless_providers.is_keyless_provider("abuseipdb") is False

    keyless_providers.set_keyless_provider_names({"hudsonrock"})

    assert keyless_providers.get_keyless_provider_names() == {"hudsonrock"}
    assert keyless_providers.is_keyless_provider("urlscan") is False
