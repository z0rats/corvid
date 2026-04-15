"""Email parsing service for extracting email components."""

import logging
from email.message import EmailMessage
from typing import Any, Union

from ..schemas.email_schemas import EmailBasicInfo, EmailHop, EmailAttachment, EmailHashes
from ..utils.parsing_utils import extract_message_text, parse_hop_components, parse_hop_date
from ..utils.hash_utils import calculate_hash
from ..utils.validation_utils import sanitize_filename

logger = logging.getLogger(__name__)


def extract_basic_info(msg: EmailMessage) -> EmailBasicInfo:
    """
    Extract basic information from email message headers.
    
    Args:
        msg: Email message object
        
    Returns:
        EmailBasicInfo object with header information
    """
    try:
        basic_info = EmailBasicInfo(
            from_address=msg.get('from'),
            to_address=msg.get('to'),
            delivered_to=msg.get('delivered-to'),
            rcpt_to=msg.get('rcpt-to'),
            cc=msg.get('cc'),
            return_path=msg.get('return-path'),
            subject=msg.get('subject'),
            date=msg.get('date'),
            dkim_signature=msg.get('dkim-signature'),
            domainkey_signature=msg.get('domainkey-signature'),
            message_id=msg.get('message-id')
        )
        
        logger.debug("Extracted basic info - From: %s, To: %s", basic_info.from_address, basic_info.to_address)
        return basic_info
        
    except Exception as e:
        logger.error("Error extracting basic info: %s", str(e))
        raise


def extract_all_headers(msg: EmailMessage) -> list[dict[str, str]]:
    """
    Extract all headers from email message as key-value pairs.
    
    Args:
        msg: Email message object
        
    Returns:
        List of header dictionaries
    """
    return [{key: value} for key, value in msg.items()]


def calculate_email_hashes(data: bytes) -> EmailHashes:
    """
    Calculate hash values for email data.
    
    Args:
        data: Email data in bytes
        
    Returns:
        EmailHashes object with hash values
    """
    return EmailHashes(
        md5=calculate_hash(data, 'md5'),
        sha1=calculate_hash(data, 'sha1'),
        sha256=calculate_hash(data, 'sha256')
    )


def extract_attachments(msg: EmailMessage) -> list[EmailAttachment]:
    """
    Extract and analyze attachments from email message.
    
    Args:
        msg: Email message object
        
    Returns:
        List of EmailAttachment objects
    """
    attachments = []
    
    try:
        for attachment in msg.iter_attachments():
            payload = attachment.get_payload(decode=True)
            if payload:
                filename = sanitize_filename(attachment.get_filename() or "unknown")
                logger.debug("Processing attachment: %s (%s bytes)", filename, len(payload))
                
                attachments.append(EmailAttachment(
                    filename=filename,
                    md5=calculate_hash(payload, 'md5'),
                    sha1=calculate_hash(payload, 'sha1'),
                    sha256=calculate_hash(payload, 'sha256')
                ))
        
        logger.info("Extracted %s attachments", len(attachments))
        
    except Exception as e:
        logger.error("Error processing attachments: %s", str(e))
    
    return attachments


def parse_single_hop(hop: str, number: int) -> EmailHop:
    """
    Parse a single email hop with detailed information extraction.
    
    Args:
        hop: Received header value
        number: Hop sequence number
        
    Returns:
        EmailHop object with parsed information
    """
    try:
        from_server, by_server, with_protocol = parse_hop_components(hop)
        date_part = parse_hop_date(hop)

        return EmailHop(
            number=number,
            from_server=from_server,
            by_server=by_server,
            with_protocol=with_protocol,
            date=date_part
        )

    except Exception as e:
        logger.error("Error parsing hop %s: %s", number, str(e))
        return EmailHop(
            number=number,
            from_server=None,
            by_server=None,
            with_protocol=None,
            date=None,
            parse_error=str(e)
        )


def extract_email_hops(msg: EmailMessage) -> list[EmailHop]:
    """
    Extract and parse email hops from message headers.
    
    Args:
        msg: Email message object
        
    Returns:
        List of EmailHop objects in chronological order
    """
    hops = []
    try:
        received_headers = msg.get_all('received') or []
        hop_number = len(received_headers)
        
        for hop in received_headers:
            hop_data = parse_single_hop(hop, hop_number)
            hops.append(hop_data)
            hop_number -= 1
            
        hops.reverse()  # Show in chronological order
        
    except Exception as e:
        logger.error("Error getting hops: %s", str(e))
    
    return hops


def extract_urls(msg: EmailMessage) -> list[str]:
    """
    Extract URLs from email message content.
    
    Args:
        msg: Email message object
        
    Returns:
        List of URLs found in message
    """
    from ..utils.parsing_utils import extract_urls_from_text
    
    text = extract_message_text(msg)
    return extract_urls_from_text(text)
