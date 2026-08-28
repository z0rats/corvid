import hashlib
from email.message import EmailMessage

from app.features.email_analyzer.service.email_analyzer_service import analyze_email_content


def _sample_eml_bytes() -> bytes:
    msg = EmailMessage()
    msg["From"] = "alice@example.com"
    msg["To"] = "bob@example.org"
    msg["Subject"] = "Meeting notes"
    msg["Date"] = "Mon, 1 Jan 2024 00:00:00 +0000"
    msg["Message-ID"] = "<abc123@example.com>"
    msg["Received"] = "from a.example by b.example with ESMTP; Mon, 1 Jan 2024 00:00:00 +0000"
    msg.set_content("See http://example.com/notes for details.")
    msg.add_attachment(
        b"attachment-bytes", maintype="application", subtype="pdf", filename="notes.pdf"
    )
    return msg.as_bytes()


class TestAnalyzeEmailContent:
    def test_returns_a_fully_populated_response(self):
        data = _sample_eml_bytes()

        result = analyze_email_content(data)

        assert result.basic_info.from_address == "alice@example.com"
        assert result.basic_info.subject == "Meeting notes"
        assert result.file_size == len(data)
        assert result.eml_hashes.sha256 == hashlib.sha256(data).hexdigest()
        assert len(result.attachments) == 1
        assert result.attachments[0].filename == "notes.pdf"
        assert len(result.hops) == 1
        assert "http://example.com" in result.urls
        assert len(result.warnings) > 0
        assert any(h["From"] == "alice@example.com" for h in result.headers)

    def test_a_minimal_message_still_produces_a_response(self):
        msg = EmailMessage()
        msg["From"] = "alice@example.com"
        msg.set_content("hi")
        data = msg.as_bytes()

        result = analyze_email_content(data)

        assert result.attachments == []
        assert result.hops == []
        assert result.file_size == len(data)
