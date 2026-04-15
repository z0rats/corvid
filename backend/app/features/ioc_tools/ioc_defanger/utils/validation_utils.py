import re


def validate_defang_operation(operation: str) -> bool:
    """
    Validate if the operation is supported
    
    Args:
        operation: Operation string to validate
        
    Returns:
        True if operation is valid, False otherwise
    """
    return operation.lower() in ['defang', 'fang']


def validate_ioc_text(text: str) -> bool:
    """
    Validate if text contains potential IOCs
    
    Args:
        text: Text to validate
        
    Returns:
        True if text appears to contain IOCs, False otherwise
    """
    if not text or not isinstance(text, str):
        return False
    
    text = text.strip()
    if not text:
        return False
    
    # Basic patterns to detect potential IOCs (both fanged and defanged forms)
    ioc_patterns = [
        r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IP addresses
        r'\b(?:\d{1,3}\[\.\]){3}\d{1,3}\b',  # Defanged IP addresses
        r'\b[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}\b',  # Domains
        r'[a-zA-Z0-9-]+\[\.\][a-zA-Z]{2,}\b',  # Defanged domains
        r'https?://[^\s]+',  # URLs
        r'hxxps?\[?:?\/\/\]?[^\s]+',  # Defanged URLs
        r'\b[a-fA-F0-9]{32}\b',  # MD5 hashes
        r'\b[a-fA-F0-9]{40}\b',  # SHA1 hashes
        r'\b[a-fA-F0-9]{64}\b',  # SHA256 hashes
        r'\b[\w\.-]+@[\w\.-]+\.\w+\b',  # Email addresses
        r'[\w\.-]+\[@\][\w\.-]+',  # Defanged email addresses
    ]
    
    for pattern in ioc_patterns:
        if re.search(pattern, text):
            return True
    
    return False


def sanitize_input_text(text: str) -> str:
    """
    Sanitize input text for processing
    
    Args:
        text: Raw input text
        
    Returns:
        Sanitized text ready for processing
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove excessive whitespace and normalize line endings
    text = re.sub(r'\r\n|\r', '\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]{2,}', ' ', text)
    
    return text.strip()


def validate_ioc_format(ioc: str) -> bool:
    """
    Basic validation to check if a string could be an IOC
    
    Args:
        ioc: String to validate
        
    Returns:
        True if string could be an IOC, False otherwise
    """
    if not ioc or not isinstance(ioc, str):
        return False
    
    ioc = ioc.strip()
    if len(ioc) < 3:  # Minimum reasonable IOC length
        return False
    
    # Check for common IOC characteristics
    has_domain_chars = bool(re.search(r'[a-zA-Z0-9.-]', ioc))
    has_reasonable_length = 3 <= len(ioc) <= 2048
    
    return has_domain_chars and has_reasonable_length
