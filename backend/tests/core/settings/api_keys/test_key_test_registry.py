"""Gate: every keyed service in Settings → API Keys either has a live key test or a stated
reason it can't have one, so a new keyed service can't silently ship without a Test button."""

from app.core.settings.api_keys.config.service_config import SERVICE_DEFINITIONS
from app.core.settings.api_keys.service.key_test_clients import KEY_TEST_EXEMPT, KEY_TESTS

KEYED = {key for key, definition in SERVICE_DEFINITIONS.items() if definition.required_keys}


def test_every_keyed_service_has_a_test_or_an_exemption():
    missing = sorted(KEYED - KEY_TESTS.keys() - KEY_TEST_EXEMPT.keys())
    assert not missing, (
        f"add a check to KEY_TESTS or a reason to KEY_TEST_EXEMPT in key_test_clients.py: {missing}"
    )


def test_no_service_is_both_tested_and_exempt():
    assert not KEY_TESTS.keys() & KEY_TEST_EXEMPT.keys()


def test_registries_name_only_keyed_services():
    stale = sorted((KEY_TESTS.keys() | KEY_TEST_EXEMPT.keys()) - KEYED)
    assert not stale, f"not a keyed service in SERVICE_DEFINITIONS: {stale}"


def test_exemption_reasons_are_sentences():
    assert all(reason.strip().endswith(".") for reason in KEY_TEST_EXEMPT.values())
