from app.features.email_search.config.mailcat_config import (
    DEFAULT_CHECKERS,
    HEADLESS_CHECKERS,
    SMTP_CHECKERS,
    get_active_checkers,
    get_installed_version,
)


class TestGetActiveCheckers:
    def test_returns_only_default_checkers_when_both_flags_are_off(self):
        checkers = get_active_checkers(enable_smtp_checks=False, enable_headless_checks=False)
        assert checkers == DEFAULT_CHECKERS

    def test_adds_smtp_checkers_when_enabled(self):
        checkers = get_active_checkers(enable_smtp_checks=True, enable_headless_checks=False)
        assert checkers == DEFAULT_CHECKERS + SMTP_CHECKERS

    def test_adds_headless_checkers_when_enabled(self):
        checkers = get_active_checkers(enable_smtp_checks=False, enable_headless_checks=True)
        assert checkers == DEFAULT_CHECKERS + HEADLESS_CHECKERS

    def test_adds_both_when_both_flags_are_on(self):
        checkers = get_active_checkers(enable_smtp_checks=True, enable_headless_checks=True)
        assert checkers == DEFAULT_CHECKERS + SMTP_CHECKERS + HEADLESS_CHECKERS

    def test_smtp_and_headless_checkers_do_not_overlap_with_the_defaults(self):
        default_ids = {id(f) for f in DEFAULT_CHECKERS}
        optional_ids = {id(f) for f in (*SMTP_CHECKERS, *HEADLESS_CHECKERS)}
        assert default_ids.isdisjoint(optional_ids)


class TestGetInstalledVersion:
    def test_returns_a_non_empty_version_string(self):
        version = get_installed_version()
        assert isinstance(version, str)
        assert version

    def test_is_cached_across_calls(self):
        assert get_installed_version() is get_installed_version()
