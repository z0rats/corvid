import logging

from app.features.ioc_tools.ioc_extractor.service.ioc_extractor_service import extract_iocs
from app.features.ioc_tools.ioc_defanger.utils.defang_utils import (
    apply_defang_patterns,
    apply_fang_patterns,
    split_ioc_text,
    is_ioc_changed,
    calculate_processing_stats
)
from app.features.ioc_tools.ioc_defanger.utils.validation_utils import (
    validate_defang_operation,
    validate_ioc_text,
    sanitize_input_text
)
from app.features.ioc_tools.ioc_defanger.schemas.defang_schemas import (
    ProcessedIOC,
    DefangResponse
)

logger = logging.getLogger(__name__)


def defang_single_ioc(ioc: str) -> str:
    """
    Defang a single IOC by replacing dangerous characters with safe alternatives
    
    Args:
        ioc: The IOC to defang
        
    Returns:
        The defanged IOC
    """
    if not ioc or not isinstance(ioc, str):
        logger.warning("Invalid IOC input: %s", type(ioc))
        return ioc
    
    return apply_defang_patterns(ioc)


def fang_single_ioc(defanged_ioc: str) -> str:
    """
    Fang (refang) a single IOC by restoring original dangerous characters
    
    Args:
        defanged_ioc: The defanged IOC to restore
        
    Returns:
        The fanged (original) IOC
    """
    if not defanged_ioc or not isinstance(defanged_ioc, str):
        logger.warning("Invalid defanged IOC input: %s", type(defanged_ioc))
        return defanged_ioc
    
    return apply_fang_patterns(defanged_ioc)


def extract_ioc_types_from_data(extracted_data) -> dict[str, list[str]]:
    """
    Create a mapping of IOC values to their types from extraction data
    
    Args:
        extracted_data: ExtractionResponse object from extract_iocs service
        
    Returns:
        Dictionary mapping IOC values to their detected types
    """
    ioc_type_map = {}
    
    type_mapping = {
        'ips': 'IP Address',
        'md5': 'MD5 Hash',
        'sha1': 'SHA1 Hash',
        'sha256': 'SHA256 Hash',
        'urls': 'URL',
        'domains': 'Domain',
        'emails': 'Email',
        'cves': 'CVE'
    }
    
    # Extract IOCs from the response object
    ioc_data = {
        'ips': extracted_data.ips,
        'md5': extracted_data.md5,
        'sha1': extracted_data.sha1,
        'sha256': extracted_data.sha256,
        'urls': extracted_data.urls,
        'domains': extracted_data.domains,
        'emails': extracted_data.emails,
        'cves': extracted_data.cves
    }
    
    for key, values in ioc_data.items():
        if isinstance(values, list) and key in type_mapping:
            for ioc in values:
                if ioc not in ioc_type_map:
                    ioc_type_map[ioc] = []
                if type_mapping[key] not in ioc_type_map[ioc]:
                    ioc_type_map[ioc].append(type_mapping[key])
    
    return ioc_type_map


def process_iocs_with_type_detection(
    text: str,
    operation: str
) -> list[ProcessedIOC]:
    """
    Process IOCs with automatic type detection using the extractor service
    
    Args:
        text: Input text containing IOCs
        operation: 'defang' or 'fang'
        
    Returns:
        List of ProcessedIOC objects with type information
    """
    logger.info("Processing IOCs with operation: %s", operation)
    
    # Validate and sanitize input
    if not validate_ioc_text(text):
        logger.warning("No valid IOCs detected in input text")
        return []
    
    sanitized_text = sanitize_input_text(text)
    iocs = split_ioc_text(sanitized_text)
    
    if not iocs:
        logger.warning("No IOCs found after text splitting")
        return []
    
    # Select processor function
    processor_func = defang_single_ioc if operation == 'defang' else fang_single_ioc
    
    try:
        # Get type information by fanging all IOCs first
        fanged_iocs = [fang_single_ioc(ioc) for ioc in iocs]
        combined_text = '\n'.join(fanged_iocs)
        extracted_data = extract_iocs(combined_text)
        ioc_type_map = extract_ioc_types_from_data(extracted_data)
        
        # Process each IOC
        results = []
        for original_ioc in iocs:
            processed_ioc = processor_func(original_ioc)
            fanged_ioc = fang_single_ioc(original_ioc)
            detected_types = ioc_type_map.get(fanged_ioc, ['Unknown'])
            
            results.append(ProcessedIOC(
                original=original_ioc,
                processed=processed_ioc,
                types=detected_types,
                changed=is_ioc_changed(original_ioc, processed_ioc)
            ))
        
        logger.info("Successfully processed %s IOCs", len(results))
        return results
        
    except Exception as e:
        logger.error("Error during IOC processing with type detection: %s", str(e))
        # Fallback to basic processing without type detection
        return process_iocs_without_type_detection(iocs, processor_func)


def process_iocs_without_type_detection(
    iocs: list[str],
    processor_func
) -> list[ProcessedIOC]:
    """
    Process IOCs without type detection as fallback
    
    Args:
        iocs: List of IOC strings
        processor_func: Function to apply to each IOC
        
    Returns:
        List of ProcessedIOC objects without type information
    """
    logger.warning("Processing IOCs without type detection (fallback mode)")
    
    results = []
    for original_ioc in iocs:
        processed_ioc = processor_func(original_ioc)
        
        results.append(ProcessedIOC(
            original=original_ioc,
            processed=processed_ioc,
            types=['Unknown'],
            changed=is_ioc_changed(original_ioc, processed_ioc)
        ))
    
    return results


def batch_process_iocs(text: str, operation: str = 'defang') -> DefangResponse:
    """
    Main service function for batch processing IOCs with comprehensive response
    
    Args:
        text: Input text containing IOCs
        operation: 'defang' or 'fang'
        
    Returns:
        DefangResponse with processed results and statistics
        
    Raises:
        ValueError: If operation is invalid
        RuntimeError: If processing fails completely
    """
    logger.info("Starting batch IOC processing with operation: %s", operation)
    
    # Validate operation
    if not validate_defang_operation(operation):
        raise ValueError(f"Invalid operation: {operation}. Must be 'defang' or 'fang'")
    
    try:
        # Process IOCs
        processed_iocs = process_iocs_with_type_detection(text, operation)
        
        # Calculate statistics
        stats = calculate_processing_stats([ioc.model_dump() for ioc in processed_iocs])
        
        response = DefangResponse(
            results=processed_iocs,
            total_processed=stats['total_processed'],
            total_changed=stats['total_changed']
        )
        
        logger.info("Batch processing completed: %s processed, %s changed", stats['total_processed'], stats['total_changed'])
        return response
        
    except Exception as e:
        logger.error("Critical error in batch IOC processing: %s", str(e))
        raise RuntimeError(f"Failed to process IOCs: {str(e)}")
