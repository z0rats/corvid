import re
from fastapi import UploadFile


# Supported file extensions for IOC extraction
SUPPORTED_FILE_EXTENSIONS = {'.txt', '.log', '.csv', '.json', '.xml', '.html', '.md'}

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Supported character encodings for file decoding
SUPPORTED_ENCODINGS = ['utf-8', 'latin-1', 'ascii', 'iso-8859-1', 'cp1252']


def validate_file_upload(file: UploadFile) -> tuple[bool, str | None]:
    """
    Validate uploaded file for IOC extraction
    
    Args:
        file: FastAPI UploadFile object
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"
    
    if not file.filename:
        return False, "File must have a filename"
    
    # Check file extension
    file_ext = get_file_extension(file.filename)
    if file_ext not in SUPPORTED_FILE_EXTENSIONS:
        return False, f"Unsupported file type. Supported: {', '.join(SUPPORTED_FILE_EXTENSIONS)}"
    
    # Check file size (if available)
    if hasattr(file, 'size') and file.size and file.size > MAX_FILE_SIZE:
        return False, f"File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    return True, None


def get_file_extension(filename: str) -> str:
    """
    Extract file extension from filename
    
    Args:
        filename: Name of the file
        
    Returns:
        File extension in lowercase (including the dot)
    """
    if not filename or '.' not in filename:
        return ''
    
    return '.' + filename.split('.')[-1].lower()


def validate_text_content(content: str) -> bool:
    """
    Validate if text content is suitable for IOC extraction
    
    Args:
        content: Text content to validate
        
    Returns:
        True if content is valid for extraction, False otherwise
    """
    if not content or not isinstance(content, str):
        return False
    
    content = content.strip()
    if not content:
        return False
    
    # Check minimum content length
    if len(content) < 3:
        return False
    
    # Check if content contains printable characters
    printable_chars = sum(1 for c in content if c.isprintable() or c.isspace())
    if printable_chars / len(content) < 0.8:  # At least 80% printable
        return False
    
    return True


def sanitize_text_content(content: str) -> str:
    """
    Sanitize text content for IOC extraction
    
    Args:
        content: Raw text content
        
    Returns:
        Sanitized text content
    """
    if not content or not isinstance(content, str):
        return ""
    
    # Normalize line endings
    content = re.sub(r'\r\n|\r', '\n', content)
    
    # Remove excessive whitespace
    content = re.sub(r'\n{4,}', '\n\n\n', content)
    content = re.sub(r'[ \t]{3,}', '  ', content)
    
    # Remove non-printable characters except common whitespace
    content = ''.join(c for c in content if c.isprintable() or c in '\n\t ')
    
    return content.strip()


def decode_file_content(file_content: bytes) -> tuple[str, str | None]:
    """
    Decode file content using various character encodings
    
    Args:
        file_content: Raw file content as bytes
        
    Returns:
        Tuple of (decoded_content, encoding_used)
        
    Raises:
        UnicodeDecodeError: If content cannot be decoded with any supported encoding
    """
    for encoding in SUPPORTED_ENCODINGS:
        try:
            decoded_content = file_content.decode(encoding)
            return decoded_content, encoding
        except UnicodeDecodeError:
            continue
    
    raise UnicodeDecodeError(
        "unknown", 
        file_content, 
        0, 
        len(file_content), 
        f"Unable to decode file with any supported encoding: {SUPPORTED_ENCODINGS}"
    )


def validate_extraction_patterns() -> bool:
    """
    Validate that IOC extraction patterns are properly compiled
    
    Returns:
        True if all patterns are valid, False otherwise
    """
    from app.features.ioc_tools.ioc_extractor.service.ioc_extractor_service import COMPILED_PATTERNS
    
    try:
        # Test each compiled pattern
        test_text = "test 192.168.1.1 example.com http://test.com test@example.com"
        
        for pattern_name, pattern in COMPILED_PATTERNS.items():
            if not hasattr(pattern, 'findall'):
                return False
            
            # Try to use the pattern
            pattern.findall(test_text)
        
        return True
        
    except Exception:
        return False


def estimate_processing_time(content_length: int) -> float:
    """
    Estimate processing time based on content length
    
    Args:
        content_length: Length of content to process
        
    Returns:
        Estimated processing time in seconds
    """
    # Rough estimate: ~1000 characters per second
    base_time = content_length / 1000
    
    # Add overhead for pattern matching
    overhead = min(content_length / 10000, 5.0)  # Max 5 seconds overhead
    
    return max(base_time + overhead, 0.1)  # Minimum 0.1 seconds
