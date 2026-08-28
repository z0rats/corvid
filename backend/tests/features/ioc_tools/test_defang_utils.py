from app.features.ioc_tools.ioc_defanger.utils.defang_utils import (
    apply_defang_patterns,
    apply_fang_patterns,
    calculate_processing_stats,
    is_ioc_changed,
    split_ioc_text,
)


class TestApplyDefangPatterns:
    def test_defangs_a_url(self):
        assert apply_defang_patterns("http://evil.com/path") == "hxxp[://]evil[.]com[/]path"

    def test_defangs_an_ip(self):
        assert apply_defang_patterns("1.2.3.4") == "1[.]2[.]3[.]4"

    def test_defangs_an_email(self):
        assert apply_defang_patterns("user@evil.com") == "user[@]evil[.]com"

    def test_non_string_input_is_returned_unchanged(self):
        assert apply_defang_patterns(None) is None
        assert apply_defang_patterns(123) == 123

    def test_empty_string_is_returned_unchanged(self):
        assert apply_defang_patterns("") == ""

    def test_strips_surrounding_whitespace(self):
        assert apply_defang_patterns("  1.2.3.4  ") == "1[.]2[.]3[.]4"


class TestApplyFangPatterns:
    def test_fangs_a_defanged_url(self):
        assert apply_fang_patterns("hxxp[://]evil[.]com[/]path") == "http://evil.com/path"

    def test_fangs_bracket_dot_notation(self):
        assert apply_fang_patterns("1[.]2[.]3[.]4") == "1.2.3.4"

    def test_fangs_paren_and_brace_dot_notation(self):
        assert apply_fang_patterns("evil(.)com") == "evil.com"
        assert apply_fang_patterns("evil{.}com") == "evil.com"

    def test_fangs_dot_word_notation(self):
        assert apply_fang_patterns("evil[dot]com") == "evil.com"
        assert apply_fang_patterns("evil dot com") == "evil.com"

    def test_fangs_at_notation(self):
        assert apply_fang_patterns("user[@]evil.com") == "user@evil.com"
        assert apply_fang_patterns("user[at]evil.com") == "user@evil.com"

    def test_non_string_input_is_returned_unchanged(self):
        assert apply_fang_patterns(None) is None

    def test_defang_then_fang_roundtrips_to_the_original(self):
        original = "http://evil.com/path?x=1"
        assert apply_fang_patterns(apply_defang_patterns(original)) == original


class TestSplitIocText:
    def test_splits_on_newlines(self):
        assert split_ioc_text("1.2.3.4\nevil.com\nuser@evil.com") == [
            "1.2.3.4",
            "evil.com",
            "user@evil.com",
        ]

    def test_splits_on_commas_and_semicolons(self):
        assert split_ioc_text("1.2.3.4, evil.com; other.com") == [
            "1.2.3.4",
            "evil.com",
            "other.com",
        ]

    def test_splits_on_multiple_consecutive_spaces(self):
        assert split_ioc_text("1.2.3.4    evil.com") == ["1.2.3.4", "evil.com"]

    def test_non_string_input_returns_empty_list(self):
        assert split_ioc_text(None) == []
        assert split_ioc_text("") == []

    def test_blank_lines_are_dropped(self):
        assert split_ioc_text("1.2.3.4\n\n\nevil.com") == ["1.2.3.4", "evil.com"]


class TestIsIocChanged:
    def test_true_when_processed_differs_from_original(self):
        assert is_ioc_changed("1.2.3.4", "1[.]2[.]3[.]4") is True

    def test_false_when_unchanged(self):
        assert is_ioc_changed("1.2.3.4", "1.2.3.4") is False


class TestCalculateProcessingStats:
    def test_counts_processed_changed_and_unchanged(self):
        results = [{"changed": True}, {"changed": False}, {"changed": True}]
        assert calculate_processing_stats(results) == {
            "total_processed": 3,
            "total_changed": 2,
            "total_unchanged": 1,
        }

    def test_empty_results_are_all_zero(self):
        assert calculate_processing_stats([]) == {
            "total_processed": 0,
            "total_changed": 0,
            "total_unchanged": 0,
        }

    def test_missing_changed_key_defaults_to_unchanged(self):
        assert calculate_processing_stats([{}]) == {
            "total_processed": 1,
            "total_changed": 0,
            "total_unchanged": 1,
        }
