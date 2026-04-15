import logging
from email.message import EmailMessage

from ..schemas.email_schemas import EmailWarning, WarningLevel
from ..utils.parsing_utils import extract_email_addresses
from ..utils.security_utils import (
    check_homograph_attack,
    is_suspicious_subject,
    is_suspicious_attachment,
    has_extension_spoofing,
    is_suspicious_mailer,
    check_url_redirection,
    check_ip_address_urls,
    check_data_uri_schemes,
    check_encoded_urls,
    parse_authentication_results
)
from ..utils.validation_utils import validate_email_date
from ..config.email_config import MAX_RELAY_SERVERS

logger = logging.getLogger(__name__)


def _make_warning(level: WarningLevel, title: str, message: str) -> EmailWarning:
    return EmailWarning(warning_tlp=level, warning_title=title, warning_message=message)


def check_from_to_fields(from_addresses: list[str], to_addresses: list[str]) -> EmailWarning:
    message = f"From: {from_addresses[0]} To: {to_addresses[0]}"
    if from_addresses == to_addresses:
        return _make_warning(WarningLevel.RED, "'From' and 'To' fields are the same", message)
    return _make_warning(WarningLevel.GREEN, "'From' and 'To' fields are not the same", message)


def check_return_path_mismatch(from_addresses: list[str], return_path: list[str]) -> EmailWarning:
    message = f"From: {from_addresses[0]} Return-Path: {return_path[0]}"
    if from_addresses != return_path:
        return _make_warning(WarningLevel.RED, "'From' and 'Return-Path' fields do not match", message)
    return _make_warning(WarningLevel.GREEN, "'From' and 'Return-Path' fields do match", message)


def check_message_id(message_id: str) -> EmailWarning:
    if not message_id:
        return _make_warning(WarningLevel.RED, "No message ID", "Message ID field is empty")
    return _make_warning(WarningLevel.GREEN, "Message ID found", "Message ID field is not empty")


def check_homograph_attacks(return_path: str, from_address: str) -> list[EmailWarning]:
    if check_homograph_attack(return_path) or check_homograph_attack(from_address):
        return [_make_warning(
            WarningLevel.RED,
            "Possible homograph attack detected",
            "Multiple Unicode scripts detected in From/Return-Path fields",
        )]
    return [_make_warning(
        WarningLevel.GREEN,
        "No indicators for homograph attack detected",
        "Single Unicode script in From/Return-Path fields",
    )]


def check_subject_security(subject: str) -> list[EmailWarning]:
    if is_suspicious_subject(subject):
        return [_make_warning(
            WarningLevel.AMBER,
            "Suspicious subject line detected",
            f"Subject '{subject}' contains potential phishing keywords",
        )]
    return []


def check_attachment_security(msg: EmailMessage) -> list[EmailWarning]:
    warnings = []
    for attachment in msg.iter_attachments():
        filename = attachment.get_filename()
        if not filename:
            continue
        if is_suspicious_attachment(filename):
            warnings.append(_make_warning(
                WarningLevel.RED,
                "Suspicious attachment detected",
                f"Email contains potentially malicious attachment: {filename}",
            ))
        if has_extension_spoofing(filename):
            warnings.append(_make_warning(
                WarningLevel.RED,
                "Potential extension spoofing",
                f"Attachment '{filename}' has multiple extensions",
            ))
    return warnings


def check_authentication_results(auth_results: list[str]) -> list[EmailWarning]:
    if not auth_results:
        return [_make_warning(
            WarningLevel.AMBER,
            "No authentication results",
            "No SPF/DKIM/DMARC authentication results found",
        )]

    auth_status = parse_authentication_results(auth_results)
    warnings = []
    for protocol, label in [("spf_pass", "SPF"), ("dkim_pass", "DKIM"), ("dmarc_pass", "DMARC")]:
        if not auth_status[protocol]:
            warnings.append(_make_warning(
                WarningLevel.AMBER,
                f"{label} failure",
                f"{label} validation did not pass",
            ))
    return warnings


def check_reply_to_mismatch(reply_to: list[str], from_addresses: list[str]) -> list[EmailWarning]:
    if reply_to and from_addresses and reply_to != from_addresses:
        return [_make_warning(
            WarningLevel.AMBER,
            "Reply-To mismatch",
            f"Reply-To address ({reply_to[0]}) doesn't match From address ({from_addresses[0]})",
        )]
    return []


def check_date_anomalies(date_header: str) -> list[EmailWarning]:
    if not date_header:
        return []
    is_valid, error_msg = validate_email_date(date_header)
    if not is_valid:
        return [_make_warning(WarningLevel.AMBER, "Date anomaly detected", error_msg)]
    return []


def check_html_content_security(msg: EmailMessage) -> list[EmailWarning]:
    warnings = []
    checks = [
        (check_url_redirection, WarningLevel.AMBER, "Potential URL redirection",
         "Email contains links with potential URL redirection"),
        (check_ip_address_urls, WarningLevel.AMBER, "IP address URL detected",
         "Email contains links with raw IP addresses"),
        (check_data_uri_schemes, WarningLevel.RED, "Data URI scheme detected",
         "Email contains potentially malicious data URI schemes"),
        (check_encoded_urls, WarningLevel.AMBER, "Encoded URL detected",
         "Email contains URL-encoded links which may be suspicious"),
    ]
    for part in msg.walk():
        if part.get_content_type() != "text/html":
            continue
        html_content = part.get_content()
        for check_fn, level, title, message in checks:
            if check_fn(html_content):
                warnings.append(_make_warning(level, title, message))
    return warnings


def check_mailer_security(x_mailer: str) -> list[EmailWarning]:
    if x_mailer and is_suspicious_mailer(x_mailer):
        return [_make_warning(
            WarningLevel.AMBER,
            "Suspicious mailer detected",
            f"Email sent using potentially suspicious mailer: {x_mailer}",
        )]
    return []


def check_relay_servers(received_headers: list[str]) -> list[EmailWarning]:
    if len(received_headers) > MAX_RELAY_SERVERS:
        return [_make_warning(
            WarningLevel.AMBER,
            "Multiple relay servers",
            f"Email passed through {len(received_headers)} servers",
        )]
    return []


def perform_security_analysis(msg: EmailMessage) -> list[EmailWarning]:
    """Perform comprehensive security analysis on an email message"""
    warnings = []

    try:
        from_addresses = extract_email_addresses(msg.get('from'))
        to_addresses = extract_email_addresses(msg.get('to'))
        return_path = extract_email_addresses(msg.get('return-path'))
        reply_to = extract_email_addresses(msg.get('reply-to'))
        subject = msg.get('subject') or ""

        warnings.append(check_from_to_fields(from_addresses, to_addresses))
        warnings.append(check_return_path_mismatch(from_addresses, return_path))
        warnings.append(check_message_id(msg.get('message-id')))
        warnings.extend(check_homograph_attacks(msg.get('return-path'), msg.get('from')))
        warnings.extend(check_subject_security(subject))
        warnings.extend(check_attachment_security(msg))

        auth_results = msg.get_all('authentication-results') or []
        warnings.extend(check_authentication_results(auth_results))
        warnings.extend(check_reply_to_mismatch(reply_to, from_addresses))
        warnings.extend(check_date_anomalies(msg.get('date')))
        warnings.extend(check_html_content_security(msg))
        warnings.extend(check_mailer_security(msg.get('x-mailer')))

        received_headers = msg.get_all('received') or []
        warnings.extend(check_relay_servers(received_headers))

    except Exception as e:
        logger.error("Error in security analysis: %s", str(e))
        warnings.append(_make_warning(
            WarningLevel.RED,
            "Error in security analysis",
            f"Error performing security analysis: {str(e)}",
        ))

    return warnings
