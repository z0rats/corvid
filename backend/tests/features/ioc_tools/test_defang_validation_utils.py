from app.features.ioc_tools.ioc_defanger.utils.validation_utils import (
    sanitize_input_text,
    validate_defang_operation,
    validate_ioc_format,
    validate_ioc_text,
)


class TestValidateDefangOperation:
    def test_accepts_defang_and_fang(self):
        assert validate_defang_operation("defang") is True
        assert validate_defang_operation("fang") is True

    def test_is_case_insensitive(self):
        assert validate_defang_operation("DEFANG") is True
        assert validate_defang_operation("Fang") is True

    def test_rejects_an_unknown_operation(self):
        assert validate_defang_operation("delete") is False


class TestValidateIocText:
    def test_true_for_an_ip_address(self):
        assert validate_ioc_text("contact 1.2.3.4 for details") is True

    def test_true_for_a_defanged_domain(self):
        assert validate_ioc_text("see evil[.]com for more") is True

    def test_true_for_a_url(self):
        assert validate_ioc_text("visit http://evil.com now") is True

    def test_true_for_a_hash(self):
        assert validate_ioc_text("d41d8cd98f00b204e9800998ecf8427e") is True

    def test_false_for_text_with_no_ioc_like_content(self):
        assert validate_ioc_text("just some plain words with no indicators") is False

    def test_false_for_empty_or_whitespace_only_text(self):
        assert validate_ioc_text("") is False
        assert validate_ioc_text("   ") is False

    def test_false_for_non_string_input(self):
        assert validate_ioc_text(None) is False


class TestSanitizeInputText:
    def test_normalizes_windows_and_mac_line_endings_to_unix(self):
        assert sanitize_input_text("a\r\nb\rc") == "a\nb\nc"

    def test_collapses_three_or_more_blank_lines_to_two(self):
        assert sanitize_input_text("a\n\n\n\nb") == "a\n\nb"

    def test_collapses_repeated_spaces_and_tabs_to_one_space(self):
        assert sanitize_input_text("a\t\tb   c") == "a b c"

    def test_strips_leading_and_trailing_whitespace(self):
        assert sanitize_input_text("  hello  ") == "hello"

    def test_non_string_input_returns_empty_string(self):
        assert sanitize_input_text(None) == ""


class TestValidateIocFormat:
    def test_true_for_a_domain_like_string(self):
        assert validate_ioc_format("evil.com") is True

    def test_false_when_too_short(self):
        assert validate_ioc_format("ab") is False

    def test_false_when_too_long(self):
        assert validate_ioc_format("a" * 2049) is False

    def test_false_for_empty_or_non_string_input(self):
        assert validate_ioc_format("") is False
        assert validate_ioc_format(None) is False

    def test_false_when_no_domain_like_characters_present(self):
        assert validate_ioc_format("!!!###???") is False
