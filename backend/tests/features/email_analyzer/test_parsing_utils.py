from email.message import EmailMessage

from app.features.email_analyzer.utils.parsing_utils import (
    extract_email_addresses,
    extract_message_text,
    extract_urls_from_text,
    parse_hop_components,
    parse_hop_date,
)

# --- extract_email_addresses ---------------------------------------------


def test_extract_email_addresses_finds_all_addresses_in_header():
    header = "Alice <alice@example.com>, Bob <bob@example.org>"
    assert extract_email_addresses(header) == ["alice@example.com", "bob@example.org"]


def test_extract_email_addresses_returns_none_sentinel_when_header_missing():
    assert extract_email_addresses(None) == ["none"]
    assert extract_email_addresses("") == ["none"]


def test_extract_email_addresses_returns_none_sentinel_when_not_a_string():
    assert extract_email_addresses(12345) == ["none"]


def test_extract_email_addresses_returns_none_sentinel_when_no_match():
    assert extract_email_addresses("no addresses here") == ["none"]


# --- extract_urls_from_text -----------------------------------------------


def test_extract_urls_from_text_finds_http_and_https():
    # URL_PATTERN's character class doesn't include '/', so a path segment
    # after the domain is not captured — this documents that actual behavior.
    text = "Visit http://evil.example and https://good.example"
    assert extract_urls_from_text(text) == [
        "http://evil.example",
        "https://good.example",
    ]


def test_extract_urls_from_text_dedupes_preserving_order():
    text = "http://a.example http://b.example http://a.example"
    assert extract_urls_from_text(text) == ["http://a.example", "http://b.example"]


def test_extract_urls_from_text_strips_trailing_html_markup():
    text = 'click <a href="http://evil.example">http://evil.example</a>'
    urls = extract_urls_from_text(text)
    assert all(">" not in url and "<" not in url for url in urls)
    assert "http://evil.example" in urls


def test_extract_urls_from_text_coerces_non_string_input():
    assert extract_urls_from_text(["http://a.example"]) == ["http://a.example"]


def test_extract_urls_from_text_returns_empty_list_when_no_urls():
    assert extract_urls_from_text("nothing to see here") == []


# --- extract_message_text --------------------------------------------------


def test_extract_message_text_returns_string_for_simple_message():
    msg = EmailMessage()
    msg.set_content("hello world")
    assert extract_message_text(msg) == "hello world\n"


def test_extract_message_text_returns_list_for_multipart_message():
    msg = EmailMessage()
    msg.set_content("plain body")
    msg.add_alternative("<p>html body</p>", subtype="html")

    parts = extract_message_text(msg)

    assert isinstance(parts, list)
    assert any("plain body" in part for part in parts)
    assert any("html body" in part for part in parts)


def test_extract_message_text_skips_attachments():
    msg = EmailMessage()
    msg.set_content("plain body")
    msg.add_attachment(b"binary-data", maintype="application", subtype="octet-stream", filename="a.bin")

    parts = extract_message_text(msg)

    assert isinstance(parts, list)
    assert not any("binary-data" in part for part in parts)


def test_extract_message_text_returns_empty_string_for_message_with_no_body():
    msg = EmailMessage()
    assert extract_message_text(msg) == ""


# --- parse_hop_components ---------------------------------------------------


def test_parse_hop_components_extracts_from_by_and_with():
    hop = "from mail.sender.com (1.2.3.4) by mail.receiver.com with ESMTP id abc123"
    from_server, by_server, with_protocol = parse_hop_components(hop)

    assert from_server == "mail.sender.com"
    assert by_server == "mail.receiver.com"
    assert with_protocol == "ESMTP"


def test_parse_hop_components_returns_none_for_missing_parts():
    from_server, by_server, with_protocol = parse_hop_components("just some text")
    assert (from_server, by_server, with_protocol) == (None, None, None)


def test_parse_hop_components_handles_partial_hop():
    hop = "by mail.receiver.com with ESMTP"
    from_server, by_server, with_protocol = parse_hop_components(hop)

    assert from_server is None
    assert by_server == "mail.receiver.com"
    assert with_protocol == "ESMTP"


# --- parse_hop_date -----------------------------------------------------


def test_parse_hop_date_extracts_date_after_semicolon():
    hop = "from a by b with ESMTP id x; Mon, 1 Jan 2024 00:00:00 +0000"
    assert parse_hop_date(hop) == "Mon, 1 Jan 2024 00:00:00 +0000"


def test_parse_hop_date_returns_none_when_no_semicolon():
    assert parse_hop_date("from a by b with ESMTP") is None
