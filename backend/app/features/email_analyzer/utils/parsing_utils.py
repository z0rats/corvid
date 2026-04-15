"""Email parsing utilities for email analyzer."""

import logging
import re
from email.message import EmailMessage

from ..config.email_config import URL_PATTERN, EMAIL_PATTERN

logger = logging.getLogger(__name__)


def extract_email_addresses(header: str | None) -> list[str]:
    """
    Extract email addresses from header field.
    
    Args:
        header: Email header value
        
    Returns:
        List of extracted email addresses
    """
    if not header or not isinstance(header, str):
        return ['none']
        
    try:
        addresses = re.findall(EMAIL_PATTERN, header)
        return addresses if addresses else ['none']
    except Exception as e:
        logger.error("Error extracting email addresses: %s", str(e))
        return ['none']


def extract_urls_from_text(text: str | list[str]) -> list[str]:
    """
    Extract URLs from text content.
    
    Args:
        text: Text content to search for URLs
        
    Returns:
        List of unique URLs found
    """
    try:
        text_str = str(text) if not isinstance(text, str) else text
        urls = re.findall(URL_PATTERN, text_str)
        cleaned_urls = [re.split(r'>|<|\\|\(', url)[0] for url in urls]
        return list(dict.fromkeys(cleaned_urls))  # Remove duplicates while preserving order
    except Exception as e:
        logger.error("Error extracting URLs: %s", str(e))
        return []


def extract_message_text(msg: EmailMessage) -> list[str] | str:
    """
    Extract text content from email message.
    
    Args:
        msg: Email message object
        
    Returns:
        Text content as string or list of strings
    """
    try:
        if msg.is_multipart():
            full_message = []
            for part in msg.walk():
                if part.is_multipart():
                    continue
                if part.get_content_disposition() == "attachment":
                    continue
                content_type = part.get_content_maintype()
                if content_type != "text":
                    continue
                try:
                    body = part.get_payload(decode=True)
                    if body:
                        full_message.append(body.decode(errors='ignore'))
                except Exception as e:
                    logger.error("Error decoding message part: %s", str(e))
            return full_message
        else:
            body = msg.get_payload(decode=True)
            return body.decode(errors='ignore') if body else ""
    except Exception as e:
        logger.error("Error getting message text: %s", str(e))
        return ""


def parse_hop_components(hop: str) -> tuple[str | None, str | None, str | None]:
    """
    Parse hop components (from, by, with) from received header.
    
    Args:
        hop: Received header value
        
    Returns:
        Tuple of (from_server, by_server, with_protocol)
    """
    from_server = None
    by_server = None
    with_protocol = None

    if "from" in hop:
        from_parts = hop.split("from ", 1)
        if len(from_parts) > 1:
            from_server = from_parts[1].split(None, 1)[0].strip()

    if "by" in hop:
        by_parts = hop.split("by ", 1)
        if len(by_parts) > 1:
            by_server = by_parts[1].split(None, 1)[0].strip()

    if "with" in hop:
        with_parts = hop.split("with ", 1)
        if len(with_parts) > 1:
            with_protocol = with_parts[1].split(None, 1)[0].strip()

    return from_server, by_server, with_protocol


def parse_hop_date(hop: str) -> str | None:
    """
    Parse date from received header.
    
    Args:
        hop: Received header value
        
    Returns:
        Date string or None
    """
    parts = hop.split(";", 1)
    return parts[1].strip() if len(parts) > 1 else None
