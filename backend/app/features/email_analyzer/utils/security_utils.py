"""Security analysis utilities for email analyzer."""

import logging
import re
import unicodedata as ud
from functools import lru_cache

from ..config.email_config import (
    SUSPICIOUS_SUBJECT_PATTERNS,
    SUSPICIOUS_ATTACHMENT_EXTENSIONS,
    SUSPICIOUS_MAILER_PATTERNS,
    HTML_REDIRECTION_PATTERN,
    IP_ADDRESS_URL_PATTERN,
    ENCODED_URL_PATTERN,
    MALICIOUS_DATA_URI_SCHEMES
)

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1024)
def check_homograph_attack(text: str | bytes | None) -> bool:
    """
    Check for possible homograph attacks in text.
    
    Args:
        text: Text to analyze for homograph attacks
        
    Returns:
        True if potential homograph attack detected
    """
    if not text or not isinstance(text, (str, bytes)):
        return False

    try:
        cleaned_text = re.sub(r'[<@.,-_> "]', '', str(text))
        scripts: set[str] = {ud.name(char).split(' ')[0] for char in cleaned_text}
        scripts.discard('LATIN')
        return len(scripts) > 1
    except Exception as e:
        logger.error("Error in homograph attack check: %s", str(e))
        return False


def is_suspicious_subject(subject: str) -> bool:
    """
    Check if email subject contains suspicious patterns.
    
    Args:
        subject: Email subject line
        
    Returns:
        True if suspicious patterns detected
    """
    if not subject:
        return False
        
    return any(pattern.lower() in subject.lower() for pattern in SUSPICIOUS_SUBJECT_PATTERNS)


def is_suspicious_attachment(filename: str) -> bool:
    """
    Check if attachment filename is suspicious.
    
    Args:
        filename: Attachment filename
        
    Returns:
        True if filename appears suspicious
    """
    if not filename:
        return False
        
    file_ext = filename.split('.')[-1].lower() if '.' in filename else ''
    return file_ext in SUSPICIOUS_ATTACHMENT_EXTENSIONS


def has_extension_spoofing(filename: str) -> bool:
    """
    Check for potential extension spoofing (multiple extensions).
    
    Args:
        filename: Attachment filename
        
    Returns:
        True if multiple extensions detected
    """
    return filename.count('.') > 1 if filename else False


def is_suspicious_mailer(x_mailer: str | None) -> bool:
    """
    Check if X-Mailer header indicates suspicious software.
    
    Args:
        x_mailer: X-Mailer header value
        
    Returns:
        True if mailer appears suspicious
    """
    if not x_mailer:
        return False
        
    return any(mailer in x_mailer.lower() for mailer in SUSPICIOUS_MAILER_PATTERNS)


def check_url_redirection(html_content: str) -> bool:
    """
    Check for potential URL redirection in HTML content.
    
    Args:
        html_content: HTML content to analyze
        
    Returns:
        True if potential URL redirection detected
    """
    if not html_content:
        return False
        
    return bool(re.search(HTML_REDIRECTION_PATTERN, html_content, re.I))


def check_ip_address_urls(html_content: str) -> bool:
    """
    Check for URLs with raw IP addresses.
    
    Args:
        html_content: HTML content to analyze
        
    Returns:
        True if IP address URLs detected
    """
    if not html_content:
        return False
        
    return bool(re.search(IP_ADDRESS_URL_PATTERN, html_content, re.I))


def check_data_uri_schemes(html_content: str) -> bool:
    """
    Check for potentially malicious data URI schemes.
    
    Args:
        html_content: HTML content to analyze
        
    Returns:
        True if suspicious data URI schemes detected
    """
    if not html_content:
        return False
        
    return any(scheme in html_content for scheme in MALICIOUS_DATA_URI_SCHEMES)


def check_encoded_urls(html_content: str) -> bool:
    """
    Check for URL-encoded links which may be suspicious.
    
    Args:
        html_content: HTML content to analyze
        
    Returns:
        True if encoded URLs detected
    """
    if not html_content:
        return False
        
    return bool(re.search(ENCODED_URL_PATTERN, html_content, re.I))


def parse_authentication_results(auth_results: list[str]) -> dict[str, bool]:
    """
    Parse authentication results for SPF, DKIM, and DMARC.
    
    Args:
        auth_results: List of authentication result headers
        
    Returns:
        Dictionary with authentication status
    """
    results = {
        'spf_pass': False,
        'dkim_pass': False,
        'dmarc_pass': False
    }
    
    if not auth_results:
        return results
    
    auth_text = ' '.join(auth_results).lower()
    
    results['spf_pass'] = 'spf=pass' in auth_text
    results['dkim_pass'] = 'dkim=pass' in auth_text
    results['dmarc_pass'] = 'dmarc=pass' in auth_text
    
    return results
