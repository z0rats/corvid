from app.core.settings.modules.config.default_settings import (
    get_available_modules,
    is_available_module,
)
from app.core.settings.modules.utils.validation_utils import (
    is_supported_module,
    normalize_module_name,
    validate_enabled_status,
    validate_module_name,
)


class TestIsAvailableModule:
    def test_true_for_a_known_module(self):
        assert is_available_module("newsfeed") is True

    def test_false_for_an_unknown_module(self):
        assert is_available_module("not_a_real_module") is False

    def test_get_available_modules_returns_a_copy_not_the_live_list(self):
        modules = get_available_modules()
        modules.append("mutated")
        assert "mutated" not in get_available_modules()


class TestValidateModuleName:
    def test_accepts_letters_digits_hyphens_and_underscores(self):
        assert validate_module_name("image_tools-2") is True

    def test_rejects_an_empty_or_non_string_value(self):
        assert validate_module_name("") is False
        assert validate_module_name(None) is False

    def test_rejects_a_value_over_the_max_length(self):
        assert validate_module_name("a" * 101) is False

    def test_rejects_disallowed_characters(self):
        assert validate_module_name("mod;ule") is False


class TestIsSupportedModule:
    def test_delegates_to_the_available_modules_list(self):
        assert is_supported_module("newsfeed") is True
        assert is_supported_module("not_a_real_module") is False


class TestNormalizeModuleName:
    def test_trims_and_lowercases_a_valid_name(self):
        assert normalize_module_name("  NewsFeed  ") == "newsfeed"

    def test_returns_none_for_an_invalid_name(self):
        assert normalize_module_name("mod;ule") is None

    def test_returns_none_for_empty_or_non_string_input(self):
        assert normalize_module_name("") is None
        assert normalize_module_name(None) is None


class TestValidateEnabledStatus:
    def test_true_for_a_bool(self):
        assert validate_enabled_status(True) is True
        assert validate_enabled_status(False) is True

    def test_false_for_a_non_bool(self):
        assert validate_enabled_status("true") is False
        assert validate_enabled_status(1) is False
