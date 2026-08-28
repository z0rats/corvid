from app.core.settings.keywords.config.default_settings import (
    get_default_keywords,
    get_keyword_categories,
    validate_pagination_limit,
)
from app.core.settings.keywords.utils.validation_utils import (
    has_valid_keyword_chars,
    is_valid_keyword_length,
    normalize_keyword,
    sanitize_keyword,
    validate_keyword_format,
)


class TestValidatePaginationLimit:
    def test_a_non_positive_limit_falls_back_to_the_default(self):
        assert validate_pagination_limit(0) == 100
        assert validate_pagination_limit(-5) == 100

    def test_a_limit_within_bounds_passes_through_unchanged(self):
        assert validate_pagination_limit(50) == 50

    def test_a_limit_over_the_max_is_capped(self):
        assert validate_pagination_limit(10_000) == 500


class TestDefaultSettingsAccessors:
    def test_get_default_keywords_returns_a_copy_not_the_live_list(self):
        first = get_default_keywords()
        first.append("mutated")
        assert "mutated" not in get_default_keywords()

    def test_get_keyword_categories_covers_the_expected_categories(self):
        categories = get_keyword_categories()
        assert set(categories) == {"threats", "vulnerabilities", "incidents", "general"}
        assert "malware" in categories["threats"]


class TestValidateKeywordFormat:
    def test_accepts_letters_digits_spaces_hyphens_and_underscores(self):
        assert validate_keyword_format("apt-29_group 1") is True

    def test_rejects_an_empty_or_non_string_value(self):
        assert validate_keyword_format("") is False
        assert validate_keyword_format(None) is False

    def test_rejects_whitespace_only(self):
        assert validate_keyword_format("   ") is False

    def test_rejects_a_value_over_the_max_length(self):
        assert validate_keyword_format("a" * 101) is False

    def test_rejects_disallowed_characters(self):
        assert validate_keyword_format("mal;ware") is False
        assert validate_keyword_format("<script>") is False


class TestNormalizeKeyword:
    def test_trims_and_lowercases(self):
        assert normalize_keyword("  Malware  ") == "malware"

    def test_collapses_internal_whitespace(self):
        assert normalize_keyword("apt   29") == "apt 29"

    def test_empty_input_returns_empty_string(self):
        assert normalize_keyword("") == ""


class TestLengthAndCharHelpers:
    def test_is_valid_keyword_length_boundaries(self):
        assert is_valid_keyword_length("a") is True
        assert is_valid_keyword_length("a" * 100) is True
        assert is_valid_keyword_length("a" * 101) is False
        assert is_valid_keyword_length("") is False

    def test_has_valid_keyword_chars(self):
        assert has_valid_keyword_chars("apt-29_group") is True
        assert has_valid_keyword_chars("mal;ware") is False
        assert has_valid_keyword_chars("") is False


class TestSanitizeKeyword:
    def test_strips_disallowed_characters_and_normalizes(self):
        assert sanitize_keyword("Mal;ware!!") == "malware"

    def test_empty_input_returns_empty_string(self):
        assert sanitize_keyword("") == ""
