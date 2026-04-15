import regex as re
from collections import OrderedDict
from typing import Any
import logging
from functools import lru_cache
from app.features.ioc_tools.ioc_extractor.utils.validation_utils import (
    validate_text_content,
    sanitize_text_content
)
from app.features.ioc_tools.ioc_extractor.schemas.extractor_schemas import (
    ExtractionResponse,
    IOCStatistics
)

logger = logging.getLogger(__name__)

# IOC extraction patterns
IOC_PATTERNS = {
    'ips': r'\b(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])(?:\.(?:25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])){3}\b',
    'md5': r'(?i)(?<![a-z0-9])[a-f0-9]{32}(?![a-z0-9])',
    'sha1': r'(?i)(?<![a-z0-9])[a-f0-9]{40}(?![a-z0-9])',
    'sha256': r'(?i)(?<![a-z0-9])[a-f0-9]{64}(?![a-z0-9])',
    'urls': r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b(?:[-a-zA-Z0-9@:%_\+.~#?&//=]*)',
    'domains': r'\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+(?:[a-zA-Z]{2,63})\b',
    'emails': r'(?<![\w\.-])[\w\.-]+@[\w\.-]+\.\w{2,}',
    'cves': r'CVE-\d{4}-\d{4,7}'
}

# Pre-compiled patterns for performance
COMPILED_PATTERNS = {
    name: re.compile(pattern) for name, pattern in IOC_PATTERNS.items()
}

# Pattern for IP address validation
IP_ADDRESS_PATTERN = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$')


def extract_pattern_matches_from_line(line: str, pattern: re.Pattern) -> list[str]:
    """
    Extract matches for a specific pattern from a line of text
    
    Args:
        line: Text line to search
        pattern: Compiled regex pattern
        
    Returns:
        List of matches found in the line
    """
    try:
        return pattern.findall(line)
    except Exception as e:
        logger.error("Error extracting pattern %s: %s", pattern.pattern, str(e))
        return []


def remove_duplicate_items(items: list[str]) -> tuple[list[str], int]:
    """
    Remove duplicates while preserving order
    
    Args:
        items: List of items that may contain duplicates
        
    Returns:
        Tuple of (unique_items, removed_count)
    """
    unique_items = list(OrderedDict.fromkeys(items))
    removed_count = len(items) - len(unique_items)
    return unique_items, removed_count


@lru_cache(maxsize=1024)
def is_valid_ip_address(domain: str) -> bool:
    """
    Check if a domain string is actually an IP address
    
    Args:
        domain: Domain string to check
        
    Returns:
        True if string is an IP address, False otherwise
    """
    return bool(IP_ADDRESS_PATTERN.match(domain))


def filter_domains_from_ips(domains: list[str]) -> list[str]:
    """
    Filter out domains that are actually IP addresses
    
    Args:
        domains: List of potential domain names
        
    Returns:
        List of actual domain names (IP addresses removed)
    """
    return [domain for domain in domains if not is_valid_ip_address(domain)]


def extract_iocs_from_single_line(line: str) -> dict[str, list[str]]:
    """
    Extract all types of IOCs from a single line of text
    
    Args:
        line: Single line of text to process
        
    Returns:
        Dictionary mapping IOC types to lists of found IOCs
    """
    return {
        ioc_type: extract_pattern_matches_from_line(line, pattern)
        for ioc_type, pattern in COMPILED_PATTERNS.items()
    }


def calculate_extraction_statistics(
    extracted_iocs: dict[str, list[str]],
    unique_iocs: dict[str, list[str]],
    filtered_domains: list[str]
) -> IOCStatistics:
    """
    Calculate comprehensive statistics about the extraction process
    
    Args:
        extracted_iocs: Raw extracted IOCs (with duplicates)
        unique_iocs: Deduplicated IOCs
        filtered_domains: Domains after IP filtering
        
    Returns:
        IOCStatistics object with detailed statistics
    """
    stats_data = {}
    
    for ioc_type in IOC_PATTERNS.keys():
        original_count = len(extracted_iocs.get(ioc_type, []))
        unique_count = len(unique_iocs.get(ioc_type, []))
        
        if ioc_type == 'domains':
            final_count = len(filtered_domains)
        else:
            final_count = unique_count
            
        stats_data[ioc_type] = final_count
        stats_data[f'{ioc_type}_removed_duplicates'] = original_count - unique_count
    
    # Calculate total unique IOCs
    total_unique = sum(
        len(iocs) for ioc_type, iocs in unique_iocs.items()
        if ioc_type != 'domains'
    ) + len(filtered_domains)
    
    stats_data['total_unique_iocs'] = total_unique
    
    return IOCStatistics(**stats_data)


def process_content_for_iocs(content: str) -> dict[str, list[str]]:
    """
    Process content line by line to extract IOCs
    
    Args:
        content: Text content to process
        
    Returns:
        Dictionary of extracted IOCs by type
    """
    extracted_iocs: dict[str, list[str]] = {
        ioc_type: [] for ioc_type in IOC_PATTERNS.keys()
    }
    
    for line in content.splitlines():
        if not line.strip():  # Skip empty lines
            continue
            
        line_iocs = extract_iocs_from_single_line(line)
        for ioc_type, iocs in line_iocs.items():
            extracted_iocs[ioc_type].extend(iocs)
    
    return extracted_iocs


def deduplicate_extracted_iocs(extracted_iocs: dict[str, list[str]]) -> dict[str, list[str]]:
    """
    Remove duplicates from extracted IOCs
    
    Args:
        extracted_iocs: Raw extracted IOCs with potential duplicates
        
    Returns:
        Dictionary of deduplicated IOCs
    """
    unique_iocs = {}
    for ioc_type, iocs in extracted_iocs.items():
        unique_iocs[ioc_type], _ = remove_duplicate_items(iocs)
    
    return unique_iocs


def extract_iocs(content: str) -> ExtractionResponse:
    """
    Main function to extract Indicators of Compromise from text content
    
    Args:
        content: String containing potential IOCs
        
    Returns:
        ExtractionResponse with extracted IOCs and statistics
        
    Raises:
        ValueError: If content is invalid
        RuntimeError: If extraction fails
    """
    logger.info("Starting IOC extraction process")
    
    # Validate input content
    if not validate_text_content(content):
        raise ValueError("Invalid or empty content provided for IOC extraction")
    
    # Sanitize content
    sanitized_content = sanitize_text_content(content)
    
    try:
        # Extract IOCs from content
        extracted_iocs = process_content_for_iocs(sanitized_content)
        
        # Remove duplicates
        unique_iocs = deduplicate_extracted_iocs(extracted_iocs)
        
        # Filter domains (remove IP addresses)
        filtered_domains = filter_domains_from_ips(unique_iocs['domains'])
        
        # Calculate statistics
        statistics = calculate_extraction_statistics(
            extracted_iocs, 
            unique_iocs, 
            filtered_domains
        )
        
        # Build response
        response = ExtractionResponse(
            ips=unique_iocs['ips'],
            md5=unique_iocs['md5'],
            sha1=unique_iocs['sha1'],
            sha256=unique_iocs['sha256'],
            urls=unique_iocs['urls'],
            domains=filtered_domains,
            emails=unique_iocs['emails'],
            cves=unique_iocs['cves'],
            statistics=statistics
        )
        
        logger.info("IOC extraction completed successfully. Found %s unique IOCs", statistics.total_unique_iocs)
        return response
        
    except Exception as e:
        logger.error("Critical error during IOC extraction: %s", str(e), exc_info=True)
        raise RuntimeError(f"Failed to extract IOCs: {str(e)}")


def extract_iocs_from_file_content(
    file_content: str, 
    filename: str | None = None
) -> ExtractionResponse:
    """
    Extract IOCs from file content with additional file-specific processing
    
    Args:
        file_content: Decoded file content
        filename: Optional filename for context
        
    Returns:
        ExtractionResponse with extracted IOCs and statistics
        
    Raises:
        ValueError: If file content is invalid
        RuntimeError: If extraction fails
    """
    logger.info("Starting IOC extraction from file: %s", filename or 'unknown')
    
    try:
        # Use the main extraction function
        result = extract_iocs(file_content)
        
        logger.info("File IOC extraction completed for: %s", filename or 'unknown')
        return result
        
    except Exception as e:
        logger.error("Error extracting IOCs from file %s: %s", filename, str(e))
        raise
