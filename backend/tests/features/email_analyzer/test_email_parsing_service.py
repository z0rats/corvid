import hashlib
from email.message import EmailMessage

from app.features.email_analyzer.service.email_parsing_service import (
    calculate_email_hashes,
    extract_all_headers,
    extract_attachments,
    extract_basic_info,
    extract_email_hops,
    extract_urls,
    parse_single_hop,
)


def _base_message() -> EmailMessage:
    msg = EmailMessage()
    msg["From"] = "alice@example.com"
    msg["To"] = "bob@example.org"
    msg["Subject"] = "Hello"
    msg["Date"] = "Mon, 1 Jan 2024 00:00:00 +0000"
    msg["Message-ID"] = "<abc123@example.com>"
    return msg


class TestExtractBasicInfo:
    def test_extracts_the_expected_headers(self):
        msg = _base_message()

        info = extract_basic_info(msg)

        assert info.from_address == "alice@example.com"
        assert info.to_address == "bob@example.org"
        assert info.subject == "Hello"
        assert info.message_id == "<abc123@example.com>"

    def test_missing_headers_come_back_as_none(self):
        info = extract_basic_info(EmailMessage())
        assert info.from_address is None
        assert info.cc is None


class TestExtractAllHeaders:
    def test_returns_one_dict_per_header_in_order(self):
        msg = EmailMessage()
        msg["From"] = "alice@example.com"
        msg["Subject"] = "Hello"

        headers = extract_all_headers(msg)

        assert headers == [{"From": "alice@example.com"}, {"Subject": "Hello"}]


class TestCalculateEmailHashes:
    def test_matches_hashlib_directly(self):
        data = b"raw email bytes"

        hashes = calculate_email_hashes(data)

        assert hashes.md5 == hashlib.md5(data).hexdigest()
        assert hashes.sha1 == hashlib.sha1(data).hexdigest()
        assert hashes.sha256 == hashlib.sha256(data).hexdigest()


class TestExtractAttachments:
    def test_extracts_filename_and_hashes(self):
        msg = _base_message()
        msg.set_content("body text")
        payload = b"binary-content"
        msg.add_attachment(
            payload, maintype="application", subtype="octet-stream", filename="evil.exe"
        )

        attachments = extract_attachments(msg)

        assert len(attachments) == 1
        assert attachments[0].filename == "evil.exe"
        assert attachments[0].md5 == hashlib.md5(payload).hexdigest()
        assert attachments[0].sha256 == hashlib.sha256(payload).hexdigest()

    def test_sanitizes_a_filename_with_path_separators(self):
        msg = _base_message()
        msg.set_content("body text")
        msg.add_attachment(
            b"data",
            maintype="application",
            subtype="octet-stream",
            filename="../../etc/passwd",
        )

        attachments = extract_attachments(msg)

        assert "/" not in attachments[0].filename

    def test_no_attachments_returns_an_empty_list(self):
        msg = _base_message()
        msg.set_content("body text")

        assert extract_attachments(msg) == []


class TestParseSingleHop:
    def test_parses_a_well_formed_hop(self):
        hop = (
            "from mail.sender.com (1.2.3.4) by mail.receiver.com with ESMTP id abc123; "
            "Mon, 1 Jan 2024 00:00:00 +0000"
        )

        result = parse_single_hop(hop, 1)

        assert result.number == 1
        assert result.from_server == "mail.sender.com"
        assert result.by_server == "mail.receiver.com"
        assert result.with_protocol == "ESMTP"
        assert result.date == "Mon, 1 Jan 2024 00:00:00 +0000"
        assert result.parse_error is None

    def test_a_hop_that_cannot_be_parsed_returns_a_parse_error_instead_of_raising(self):
        result = parse_single_hop(None, 3)

        assert result.number == 3
        assert result.from_server is None
        assert result.parse_error is not None


class TestExtractEmailHops:
    def test_extracts_every_received_header(self):
        msg = _base_message()
        msg["Received"] = "from a.example by b.example with ESMTP; Mon, 1 Jan 2024 00:00:00 +0000"
        msg["Received"] = "from c.example by d.example with SMTP; Tue, 2 Jan 2024 00:00:00 +0000"

        hops = extract_email_hops(msg)

        assert len(hops) == 2
        assert {h.from_server for h in hops} == {"a.example", "c.example"}

    def test_no_received_headers_returns_an_empty_list(self):
        assert extract_email_hops(_base_message()) == []


class TestExtractUrls:
    def test_finds_urls_in_the_message_body(self):
        msg = _base_message()
        msg.set_content("Click http://evil.example/phish now")

        assert extract_urls(msg) == ["http://evil.example"]

    def test_no_urls_returns_an_empty_list(self):
        msg = _base_message()
        msg.set_content("nothing suspicious here")

        assert extract_urls(msg) == []
