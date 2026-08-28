from email.message import EmailMessage

from app.features.email_analyzer.schemas.email_schemas import WarningLevel
from app.features.email_analyzer.service.email_security_service import (
    check_attachment_security,
    check_authentication_results,
    check_date_anomalies,
    check_from_to_fields,
    check_html_content_security,
    check_mailer_security,
    check_message_id,
    check_relay_servers,
    check_reply_to_mismatch,
    check_return_path_mismatch,
    check_subject_security,
    perform_security_analysis,
)


class TestCheckFromToFields:
    def test_red_when_from_and_to_are_identical(self):
        warning = check_from_to_fields(["a@example.com"], ["a@example.com"])
        assert warning.warning_tlp == WarningLevel.RED

    def test_green_when_different(self):
        warning = check_from_to_fields(["a@example.com"], ["b@example.com"])
        assert warning.warning_tlp == WarningLevel.GREEN


class TestCheckReturnPathMismatch:
    def test_red_when_they_differ(self):
        warning = check_return_path_mismatch(["a@example.com"], ["b@example.com"])
        assert warning.warning_tlp == WarningLevel.RED

    def test_green_when_they_match(self):
        warning = check_return_path_mismatch(["a@example.com"], ["a@example.com"])
        assert warning.warning_tlp == WarningLevel.GREEN


class TestCheckMessageId:
    def test_red_when_missing(self):
        assert check_message_id(None).warning_tlp == WarningLevel.RED
        assert check_message_id("").warning_tlp == WarningLevel.RED

    def test_green_when_present(self):
        assert check_message_id("<id@example.com>").warning_tlp == WarningLevel.GREEN


class TestCheckSubjectSecurity:
    def test_flags_a_phishing_style_subject(self):
        warnings = check_subject_security("Urgent: verify your account now")
        assert len(warnings) == 1
        assert warnings[0].warning_tlp == WarningLevel.AMBER

    def test_no_warning_for_a_benign_subject(self):
        assert check_subject_security("Team lunch on Friday") == []


class TestCheckAttachmentSecurity:
    def test_flags_a_suspicious_extension(self):
        msg = EmailMessage()
        msg.set_content("body")
        msg.add_attachment(
            b"data", maintype="application", subtype="octet-stream", filename="invoice.exe"
        )

        warnings = check_attachment_security(msg)

        assert any("Suspicious attachment" in w.warning_title for w in warnings)

    def test_flags_extension_spoofing(self):
        msg = EmailMessage()
        msg.set_content("body")
        msg.add_attachment(
            b"data", maintype="application", subtype="octet-stream", filename="invoice.pdf.exe"
        )

        warnings = check_attachment_security(msg)

        titles = [w.warning_title for w in warnings]
        assert "Suspicious attachment detected" in titles
        assert "Potential extension spoofing" in titles

    def test_no_attachments_returns_no_warnings(self):
        msg = EmailMessage()
        msg.set_content("body")
        assert check_attachment_security(msg) == []


class TestCheckAuthenticationResults:
    def test_no_results_produces_one_amber_warning(self):
        warnings = check_authentication_results([])
        assert len(warnings) == 1
        assert warnings[0].warning_tlp == WarningLevel.AMBER

    def test_all_passing_produces_no_warnings(self):
        warnings = check_authentication_results(["spf=pass dkim=pass dmarc=pass"])
        assert warnings == []

    def test_a_failing_protocol_produces_a_warning_for_it(self):
        warnings = check_authentication_results(["spf=pass dkim=fail dmarc=pass"])
        assert len(warnings) == 1
        assert "DKIM" in warnings[0].warning_title


class TestCheckReplyToMismatch:
    def test_flags_a_mismatch(self):
        warnings = check_reply_to_mismatch(["evil@example.com"], ["alice@example.com"])
        assert len(warnings) == 1
        assert warnings[0].warning_tlp == WarningLevel.AMBER

    def test_no_warning_when_they_match(self):
        assert check_reply_to_mismatch(["alice@example.com"], ["alice@example.com"]) == []

    def test_no_warning_when_either_side_is_empty(self):
        assert check_reply_to_mismatch([], ["alice@example.com"]) == []


class TestCheckDateAnomalies:
    def test_no_warning_for_a_missing_date(self):
        assert check_date_anomalies(None) == []

    def test_flags_an_unparseable_date(self):
        warnings = check_date_anomalies("not a date")
        assert len(warnings) == 1
        assert warnings[0].warning_tlp == WarningLevel.AMBER


class TestCheckHtmlContentSecurity:
    def test_flags_a_malicious_data_uri(self):
        msg = EmailMessage()
        msg.set_content("plain body")
        msg.add_alternative(
            '<a href="data:text/html;base64,PHNjcmlwdD4=">click</a>', subtype="html"
        )

        warnings = check_html_content_security(msg)

        assert any("Data URI" in w.warning_title for w in warnings)

    def test_no_warnings_for_benign_html(self):
        msg = EmailMessage()
        msg.set_content("plain body")
        msg.add_alternative("<p>hello world</p>", subtype="html")

        assert check_html_content_security(msg) == []


class TestCheckMailerSecurity:
    def test_flags_a_suspicious_mailer(self):
        warnings = check_mailer_security("PHPMailer 5.1")
        assert len(warnings) == 1

    def test_no_warning_for_a_normal_mailer(self):
        assert check_mailer_security("Microsoft Outlook") == []

    def test_no_warning_when_absent(self):
        assert check_mailer_security(None) == []


class TestCheckRelayServers:
    def test_flags_too_many_relays(self):
        warnings = check_relay_servers(["hop"] * 6)
        assert len(warnings) == 1

    def test_no_warning_within_the_limit(self):
        assert check_relay_servers(["hop"] * 3) == []


class TestPerformSecurityAnalysis:
    def test_combines_findings_from_multiple_checks(self):
        msg = EmailMessage()
        msg["From"] = "alice@example.com"
        msg["To"] = "alice@example.com"
        msg["Subject"] = "Urgent: verify your account"
        msg.set_content("body")

        warnings = perform_security_analysis(msg)

        titles = [w.warning_title for w in warnings]
        assert "'From' and 'To' fields are the same" in titles
        assert any("subject" in t.lower() for t in titles)
        assert any(w.warning_tlp == WarningLevel.RED for w in warnings)

    def test_a_clean_message_still_returns_a_full_set_of_warnings(self):
        msg = EmailMessage()
        msg["From"] = "alice@example.com"
        msg["To"] = "bob@example.org"
        msg["Message-ID"] = "<id@example.com>"
        msg["Return-Path"] = "alice@example.com"
        msg.set_content("hello")

        warnings = perform_security_analysis(msg)

        assert len(warnings) > 0
