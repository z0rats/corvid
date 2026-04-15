import logging
from email.parser import BytesParser
from email import policy
from datetime import datetime, timezone

from ..schemas.email_schemas import EmailAnalysisResponse, WarningLevel
from .email_parsing_service import (
    extract_basic_info,
    extract_all_headers,
    calculate_email_hashes,
    extract_attachments,
    extract_email_hops,
    extract_urls
)
from .email_security_service import perform_security_analysis
from ..utils.parsing_utils import extract_message_text

logger = logging.getLogger(__name__)


def analyze_email_content(data: bytes) -> EmailAnalysisResponse:
    """Analyze email data and return comprehensive analysis results.

    Raises ValueError if the email cannot be parsed or analyzed.
    """
    logger.info("Starting email analysis for %s byte file", len(data))

    msg = BytesParser(policy=policy.default).parsebytes(data)

    basic_info = extract_basic_info(msg)
    headers = extract_all_headers(msg)
    eml_hashes = calculate_email_hashes(data)
    attachments = extract_attachments(msg)
    hops = extract_email_hops(msg)
    warnings = perform_security_analysis(msg)
    urls = extract_urls(msg)
    message_text = extract_message_text(msg)

    critical_warnings = [w for w in warnings if w.warning_tlp == WarningLevel.RED]
    logger.info("Email analysis completed - Warnings: %s (Critical: %s)", len(warnings), len(critical_warnings))

    return EmailAnalysisResponse(
        basic_info=basic_info,
        headers=headers,
        eml_hashes=eml_hashes,
        attachments=attachments,
        hops=hops,
        warnings=warnings,
        urls=urls,
        message_text=message_text,
        analysis_timestamp=datetime.now(timezone.utc),
        file_size=len(data)
    )
