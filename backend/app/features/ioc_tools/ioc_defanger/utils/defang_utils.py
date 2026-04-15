import re
from functools import lru_cache


# Defang patterns for converting dangerous IOCs to safe representations
DEFANG_PATTERNS: list[dict[str, any]] = [
    # Protocol defanging
    {'defanged': re.compile(r'hxxp', re.IGNORECASE), 'fanged': 'http'},
    {'defanged': re.compile(r'hxxps', re.IGNORECASE), 'fanged': 'https'},
    {'defanged': re.compile(r'fxp', re.IGNORECASE), 'fanged': 'ftp'},
    
    # Dot defanging
    {'defanged': re.compile(r'\[\.\]'), 'fanged': '.'},
    {'defanged': re.compile(r'\(\.\)'), 'fanged': '.'},
    {'defanged': re.compile(r'\{\.\}'), 'fanged': '.'},
    {'defanged': re.compile(r'\[dot\]', re.IGNORECASE), 'fanged': '.'},
    {'defanged': re.compile(r'\(dot\)', re.IGNORECASE), 'fanged': '.'},
    {'defanged': re.compile(r'\{dot\}', re.IGNORECASE), 'fanged': '.'},
    {'defanged': re.compile(r'\\\\.'), 'fanged': '.'},
    {'defanged': re.compile(r' \. '), 'fanged': '.'},
    {'defanged': re.compile(r' dot ', re.IGNORECASE), 'fanged': '.'},
    
    # Colon defanging
    {'defanged': re.compile(r'\[:\]'), 'fanged': ':'},
    {'defanged': re.compile(r'\(:\)'), 'fanged': ':'},
    {'defanged': re.compile(r'\{:\}'), 'fanged': ':'},
    
    # Protocol separator defanging
    {'defanged': re.compile(r'\[:\/\/\]'), 'fanged': '://'},
    {'defanged': re.compile(r'\(:\/\/\)'), 'fanged': '://'},
    {'defanged': re.compile(r'\{:\/\/\}'), 'fanged': '://'},
    
    # Slash defanging
    {'defanged': re.compile(r'\[\/\]'), 'fanged': '/'},
    {'defanged': re.compile(r'\(\/\)'), 'fanged': '/'},
    {'defanged': re.compile(r'\{\/\}'), 'fanged': '/'},
    
    # At symbol defanging
    {'defanged': re.compile(r'\[@\]'), 'fanged': '@'},
    {'defanged': re.compile(r'\(@\)'), 'fanged': '@'},
    {'defanged': re.compile(r'\{@\}'), 'fanged': '@'},
    {'defanged': re.compile(r'\[at\]', re.IGNORECASE), 'fanged': '@'},
    {'defanged': re.compile(r'\(at\)', re.IGNORECASE), 'fanged': '@'},
    {'defanged': re.compile(r'\{at\}', re.IGNORECASE), 'fanged': '@'},
    {'defanged': re.compile(r' at ', re.IGNORECASE), 'fanged': '@'},
]

# Fang patterns for converting safe IOCs back to dangerous representations
FANG_PATTERNS: list[dict[str, any]] = [
    # Protocol fanging
    {'fanged': re.compile(r'http', re.IGNORECASE), 'defanged': 'hxxp'},
    {'fanged': re.compile(r'https', re.IGNORECASE), 'defanged': 'hxxps'},
    {'fanged': re.compile(r'ftp', re.IGNORECASE), 'defanged': 'fxp'},
    
    # Dot fanging
    {'fanged': re.compile(r'\.'), 'defanged': '[.]'},
    
    # Colon fanging (be careful with this one)
    {'fanged': re.compile(r':(?!\/\/)'), 'defanged': '[:]'},
    
    # Protocol separator fanging
    {'fanged': re.compile(r':\/\/'), 'defanged': '[://]'},
    
    # Slash fanging (only in URLs, be careful)
    {'fanged': re.compile(r'\/(?=\w)'), 'defanged': '[/]'},
    
    # At symbol fanging
    {'fanged': re.compile(r'@'), 'defanged': '[@]'},
]


def apply_defang_patterns(ioc: str) -> str:
    """
    Apply defang patterns to make an IOC safe
    
    Args:
        ioc: The IOC to defang
        
    Returns:
        The defanged IOC
    """
    if not ioc or not isinstance(ioc, str):
        return ioc
    
    defanged = ioc.strip()
    
    for pattern in FANG_PATTERNS:
        defanged = pattern['fanged'].sub(pattern['defanged'], defanged)
    
    return defanged


def apply_fang_patterns(defanged_ioc: str) -> str:
    """
    Apply fang patterns to restore an IOC to its original form
    
    Args:
        defanged_ioc: The defanged IOC to restore
        
    Returns:
        The fanged (original) IOC
    """
    if not defanged_ioc or not isinstance(defanged_ioc, str):
        return defanged_ioc
    
    fanged = defanged_ioc.strip()
    
    for pattern in DEFANG_PATTERNS:
        fanged = pattern['defanged'].sub(pattern['fanged'], fanged)
    
    return fanged


def split_ioc_text(text: str) -> list[str]:
    """
    Split text into individual IOCs using various separators
    
    Args:
        text: Text containing IOCs
        
    Returns:
        List of individual IOC strings
    """
    if not text or not isinstance(text, str):
        return []
    
    # Split by lines first, then by common separators
    lines = text.split('\n')
    iocs = []
    
    for line in lines:
        # Split by commas, semicolons, or multiple spaces
        line_iocs = re.split(r'[,;]\s*|\s{2,}', line)
        line_iocs = [ioc.strip() for ioc in line_iocs if ioc.strip()]
        iocs.extend(line_iocs)
    
    return [ioc for ioc in iocs if ioc]


@lru_cache(maxsize=1024)
def is_ioc_changed(original: str, processed: str) -> bool:
    """
    Check if an IOC was changed during processing
    
    Args:
        original: Original IOC value
        processed: Processed IOC value
        
    Returns:
        True if IOC was changed, False otherwise
    """
    return original != processed


def calculate_processing_stats(results: list[dict[str, any]]) -> dict[str, int]:
    """
    Calculate statistics about IOC processing results
    
    Args:
        results: List of processing results
        
    Returns:
        Dictionary containing processing statistics
    """
    total_processed = len(results)
    total_changed = sum(1 for result in results if result.get('changed', False))
    
    return {
        'total_processed': total_processed,
        'total_changed': total_changed,
        'total_unchanged': total_processed - total_changed
    }
