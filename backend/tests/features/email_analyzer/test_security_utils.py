from app.features.email_analyzer.utils.security_utils import (
    check_data_uri_schemes,
    check_encoded_urls,
    check_homograph_attack,
    check_ip_address_urls,
    check_url_redirection,
    has_extension_spoofing,
    is_suspicious_attachment,
    is_suspicious_mailer,
    is_suspicious_subject,
    parse_authentication_results,
)

# --- check_homograph_attack ---------------------------------------------
#
# check_homograph_attack() only flags text where TWO OR MORE distinct
# non-Latin scripts are mixed together. It does NOT flag the far more common
# real-world homograph pattern of swapping a single non-Latin lookalike
# character into an otherwise-Latin domain (e.g. Cyrillic 'а' for Latin 'a'
# in "paypal.com"), because after `scripts.discard('LATIN')` only one
# non-Latin script name remains in the set, and `len(scripts) > 1` is False.
# These tests document the function's actual behavior, including that gap.


def test_check_homograph_attack_flags_two_mixed_non_latin_scripts():
    # Cyrillic 'а' (U+0430) + Greek 'α' (U+03B1) mixed into a Latin domain
    assert check_homograph_attack("pаypαl.com") is True


def test_check_homograph_attack_pure_latin_is_not_flagged():
    assert check_homograph_attack("paypal.com") is False


def test_check_homograph_attack_does_not_catch_single_script_substitution():
    # Known gap: a single Cyrillic lookalike swapped into an otherwise-Latin
    # domain is the classic homograph phishing pattern, but this function
    # returns False for it since only one non-Latin script is present.
    single_char_swap = "pаypal.com"  # 'а' here is Cyrillic U+0430
    assert check_homograph_attack(single_char_swap) is False


def test_check_homograph_attack_pure_non_latin_single_script_is_not_flagged():
    assert check_homograph_attack("раупал.com") is False


def test_check_homograph_attack_handles_none_and_non_string():
    assert check_homograph_attack(None) is False
    assert check_homograph_attack(12345) is False
    assert check_homograph_attack("") is False


# --- is_suspicious_subject -----------------------------------------------


def test_is_suspicious_subject_matches_known_phishing_terms():
    assert is_suspicious_subject("Urgent: verify your account now") is True
    assert is_suspicious_subject("Your bank statement is ready") is True


def test_is_suspicious_subject_case_insensitive():
    assert is_suspicious_subject("URGENT ACTION REQUIRED") is True


def test_is_suspicious_subject_ignores_benign_text():
    assert is_suspicious_subject("Weekly team lunch on Friday") is False


def test_is_suspicious_subject_handles_empty():
    assert is_suspicious_subject("") is False
    assert is_suspicious_subject(None) is False


# --- is_suspicious_attachment / has_extension_spoofing --------------------


def test_is_suspicious_attachment_flags_executable_extensions():
    assert is_suspicious_attachment("invoice.exe") is True
    assert is_suspicious_attachment("payload.js") is True
    assert is_suspicious_attachment("script.PS1") is True  # case-insensitive


def test_is_suspicious_attachment_allows_common_document_types():
    assert is_suspicious_attachment("invoice.pdf") is False
    assert is_suspicious_attachment("report.docx") is False


def test_is_suspicious_attachment_handles_no_extension():
    assert is_suspicious_attachment("README") is False
    assert is_suspicious_attachment("") is False


def test_has_extension_spoofing_detects_double_extension():
    assert has_extension_spoofing("invoice.pdf.exe") is True


def test_has_extension_spoofing_single_extension_is_fine():
    assert has_extension_spoofing("invoice.pdf") is False
    assert has_extension_spoofing("README") is False
    assert has_extension_spoofing("") is False


# --- is_suspicious_mailer -------------------------------------------------


def test_is_suspicious_mailer_flags_known_bulk_mailer_patterns():
    assert is_suspicious_mailer("PHPMailer 6.5") is True
    assert is_suspicious_mailer("Bulk Mail Sender 2.0") is True


def test_is_suspicious_mailer_allows_common_legit_clients():
    assert is_suspicious_mailer("Microsoft Outlook 16.0") is False
    assert is_suspicious_mailer("Apple Mail (18E5210a)") is False


def test_is_suspicious_mailer_handles_missing_header():
    assert is_suspicious_mailer(None) is False
    assert is_suspicious_mailer("") is False


# --- HTML content checks (verified against realistic phishing HTML) -------


def test_check_url_redirection_flags_click_lure_with_non_www_href():
    html = '<a href="http://evil-example.tld/login">Click here</a>'
    assert check_url_redirection(html) is True


def test_check_url_redirection_allows_plain_www_link():
    html = '<a href="https://www.legit-bank.com/account">Visit our site</a>'
    assert check_url_redirection(html) is False


def test_check_ip_address_urls_flags_raw_ip_href():
    html = '<a href="http://192.168.1.5/login">Login</a>'
    assert check_ip_address_urls(html) is True


def test_check_ip_address_urls_allows_domain_href():
    html = '<a href="http://example.com/login">Login</a>'
    assert check_ip_address_urls(html) is False


def test_check_data_uri_schemes_flags_html_data_uri():
    html = '<iframe src="data:text/html;base64,PHNjcmlwdD4="></iframe>'
    assert check_data_uri_schemes(html) is True


def test_check_data_uri_schemes_allows_image_data_uri():
    html = '<img src="data:image/png;base64,iVBORw0KGgo=">'
    assert check_data_uri_schemes(html) is False


def test_check_encoded_urls_flags_percent_encoded_href():
    html = '<a href="%68%74%74%70%3a%2f%2fexample.com">Link</a>'
    assert check_encoded_urls(html) is True


def test_check_encoded_urls_allows_plain_href():
    html = '<a href="http://example.com">Link</a>'
    assert check_encoded_urls(html) is False


def test_html_checks_handle_empty_content():
    assert check_url_redirection("") is False
    assert check_ip_address_urls("") is False
    assert check_data_uri_schemes("") is False
    assert check_encoded_urls("") is False


# --- parse_authentication_results ------------------------------------------
#
# This is a naive substring check over the joined, lowercased header text,
# not a structured parse of the Authentication-Results header. It cannot
# distinguish "spf=pass" appearing as the real verdict from it appearing
# incidentally elsewhere in the same header blob (e.g. quoted in a comment,
# or as part of a compound result like "best-guess spf=pass"). These tests
# cover both the intended behavior and that documented gap.


def test_parse_authentication_results_all_pass_gmail_style():
    headers = [
        "mx.google.com; dkim=pass header.i=@example.com; spf=pass "
        "smtp.mailfrom=example.com; dmarc=pass action=none header.from=example.com"
    ]
    result = parse_authentication_results(headers)
    assert result == {"spf_pass": True, "dkim_pass": True, "dmarc_pass": True}


def test_parse_authentication_results_all_fail_outlook_style():
    headers = ["spf=fail (sender IP is 1.2.3.4) smtp.mailfrom=attacker.tld; dkim=fail; dmarc=fail"]
    result = parse_authentication_results(headers)
    assert result == {"spf_pass": False, "dkim_pass": False, "dmarc_pass": False}


def test_parse_authentication_results_handles_missing_or_empty():
    assert parse_authentication_results([]) == {"spf_pass": False, "dkim_pass": False, "dmarc_pass": False}
    assert parse_authentication_results(None) == {"spf_pass": False, "dkim_pass": False, "dmarc_pass": False}


def test_parse_authentication_results_merges_multiple_header_lines():
    headers = ["spf=pass smtp.mailfrom=example.com", "dkim=pass header.d=example.com", "dmarc=pass"]
    result = parse_authentication_results(headers)
    assert result == {"spf_pass": True, "dkim_pass": True, "dmarc_pass": True}


def test_parse_authentication_results_false_positives_on_substring_match():
    # Known gap: a genuinely failing SPF check that happens to contain the
    # substring "spf=pass" anywhere in the header text (e.g. quoted from a
    # forwarded/relayed hop) is misread as a pass, since this is substring
    # matching rather than parsing the actual verdict token.
    headers = ["spf=fail (originally spf=pass at an earlier relay hop) smtp.mailfrom=attacker.tld"]
    result = parse_authentication_results(headers)
    assert result["spf_pass"] is True  # documents the false positive, not the desired behavior
