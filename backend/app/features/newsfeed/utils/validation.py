import mimetypes
import xml.sax
import io
from PIL import Image
import logging
from urllib.parse import urlparse
import feedparser
import uuid
from typing import Any, TypedDict
from functools import wraps
import time


logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/gif'}
TARGET_IMAGE_SIZE = (64, 64)

class FeedInfo(TypedDict):
    """Type definition for feed information"""
    title: str
    description: str
    version: str
    entry_count: int

def log_execution_time(func):
    """Decorator to log function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info("%s completed in %.2f seconds", func.__name__, execution_time)
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error("%s failed after %.2f seconds: %s", func.__name__, execution_time, str(e))
            raise
    return wrapper

def generate_icon_filename() -> str:
    """Generate a random filename for the icon.
    
    Returns:
        str: A UUID-based filename with .png extension
    """
    return f"{uuid.uuid4()}.png"

def validate_url_format(url: str) -> tuple[bool, str | None]:
    """Validate URL format
    
    Args:
        url: The URL to validate
        
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
    """
    parsed_url = urlparse(str(url))
    if not all([parsed_url.scheme, parsed_url.netloc]):
        logger.error("Invalid URL format: %s", url)
        return False, "Invalid URL format"
    return True, None

def parse_feed_info(feed: feedparser.FeedParserDict) -> FeedInfo | None:
    """Extract feed information from parsed feed
    
    Args:
        feed: Parsed feed dictionary
        
    Returns:
        FeedInfo | None: Feed information if valid, None otherwise
    """
    if not feed.feed:
        return None
        
    return {
        'title': feed.feed.get('title', ''),
        'description': feed.feed.get('description', ''),
        'version': feed.get('version', ''),
        'entry_count': len(feed.entries)
    }

@log_execution_time
def validate_feed(url: str) -> tuple[bool, str | None, FeedInfo | None]:
    """Validate and parse RSS/Atom feed
    
    Args:
        url: The feed URL to validate
        
    Returns:
        Tuple containing:
        - Success status (bool)
        - Error message if any (str | None)
        - Feed information if successful (FeedInfo | None)
    """
    url = str(url)
    is_valid_url, url_error = validate_url_format(url)
    if not is_valid_url:
        return False, url_error, None
    
    try:
        logger.info("Attempting to parse feed: %s", url)
        
        # Suppress encoding warnings from feedparser
        import warnings
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", message=".*document declared as.*")
            warnings.filterwarnings("ignore", message=".*encoding.*")
            feed = feedparser.parse(str(url), sanitize_html=True)
        
        # Check for parsing errors, but be more lenient with encoding issues
        if feed.get('bozo', 0) == 1:
            exception = feed.get('bozo_exception')
            if exception:
                error_msg = str(exception)
                # Don't fail on encoding warnings, only on serious parsing errors
                if "encoding" in error_msg.lower() or "declared as" in error_msg.lower():
                    logger.warning("Feed encoding warning (continuing): %s", error_msg)
                elif isinstance(exception, xml.sax._exceptions.SAXParseException):
                    logger.error("Feed parsing failed: XML parsing error: %s", error_msg)
                    return False, f"XML parsing error: {error_msg}", None
                else:
                    logger.error("Feed parsing failed: %s", error_msg)
                    return False, error_msg, None
        
        # Validate feed content
        if not feed.entries:
            logger.warning("Feed contains no entries: %s", url)
            return False, "Feed contains no entries", None
        
        feed_info = parse_feed_info(feed)
        if not feed_info:
            logger.error("Invalid feed structure: %s", url)
            return False, "Invalid feed structure: missing feed information", None
        
        logger.info("Successfully validated feed: %s", url)
        return True, None, feed_info
        
    except Exception as e:
        logger.error("Unexpected error validating feed: %s", str(e))
        return False, f"Feed validation error: {str(e)}", None

def validate_image_metadata(
    file_content: bytes,
    original_filename: str
) -> tuple[bool, str | None]:
    """Validate image file metadata
    
    Args:
        file_content: Raw image file content
        original_filename: Original filename of the image
        
    Returns:
        tuple[bool, str | None]: (is_valid, error_message)
    """
    if len(file_content) > MAX_FILE_SIZE:
        return False, f"File size too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)"

    image_type = mimetypes.guess_type(original_filename)[0]
    if image_type not in ALLOWED_IMAGE_TYPES:
        return False, f"Invalid file type. Allowed: {', '.join(t.split('/')[-1].upper() for t in ALLOWED_IMAGE_TYPES)}"
        
    return True, None

def process_image(image: Image.Image) -> Image.Image:
    """Process image according to requirements
    
    Args:
        image: PIL Image object
        
    Returns:
        Image.Image: Processed image
    """
    # Convert image mode if necessary
    if image.mode != 'RGB':
        image = image.convert('RGB')
        logger.info("Converted image mode to RGB")

    # Resize image
    image.thumbnail(TARGET_IMAGE_SIZE, Image.Resampling.LANCZOS)
    return image

@log_execution_time
def validate_and_process_icon(
    file_content: bytes,
    original_filename: str
) -> tuple[bool, str | None, tuple[bytes, str] | None]:
    """Validate and process an icon image
    
    Args:
        file_content: Raw image file content
        original_filename: Original filename of the image
        
    Returns:
        Tuple containing:
        - Success status (bool)
        - Error message if any (str | None)
        - Processed image data and filename if successful (Tuple[bytes, str] | None)
    """
    try:
        # Validate metadata
        is_valid, error_msg = validate_image_metadata(file_content, original_filename)
        if not is_valid:
            logger.warning("Validation error for %s: %s", original_filename, error_msg)
            return False, error_msg, None

        # Process image
        with io.BytesIO(file_content) as input_buffer:
            image = Image.open(input_buffer)
            processed_image = process_image(image)
            
            # Save processed image
            output_buffer = io.BytesIO()
            processed_image.save(output_buffer, format='PNG', optimize=True)
            icon_id = generate_icon_filename()
            
            logger.info(
                f"Successfully processed icon: {original_filename} -> {icon_id} "
                f"(size: {len(output_buffer.getvalue()) // 1024}KB)"
            )
            
            return True, None, (output_buffer.getvalue(), icon_id)

    except Exception as e:
        logger.error("Error processing icon %s: %s", original_filename, str(e))
        return False, f"Invalid image file: {str(e)}", None
