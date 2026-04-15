"""Hash calculation utilities for email analyzer."""

import hashlib
import logging
from typing import Callable

from ..config.email_config import SUPPORTED_HASH_ALGORITHMS

logger = logging.getLogger(__name__)


def get_hash_function(hash_type: str) -> Callable:
    """
    Get hash function for specified algorithm.
    
    Args:
        hash_type: Hash algorithm name
        
    Returns:
        Hash function
        
    Raises:
        ValueError: If hash_type is not supported
    """
    hash_functions: dict[str, Callable] = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256
    }
    
    if hash_type not in hash_functions:
        raise ValueError(f"Unsupported hash type: {hash_type}")
        
    return hash_functions[hash_type]


def calculate_hash(data: bytes, hash_type: str = 'sha256') -> str:
    """
    Calculate hash of given data using specified algorithm.
    
    Args:
        data: Binary data to hash
        hash_type: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        ValueError: If hash_type is not supported
    """
    hash_function = get_hash_function(hash_type)
    return hash_function(data).hexdigest()


def calculate_multiple_hashes(data: bytes) -> dict[str, str]:
    """
    Calculate multiple hash values for data.
    
    Args:
        data: Binary data to hash
        
    Returns:
        Dictionary with hash algorithm as key and hash as value
    """
    hashes = {}
    
    for algorithm in SUPPORTED_HASH_ALGORITHMS:
        try:
            hashes[algorithm] = calculate_hash(data, algorithm)
        except Exception as e:
            logger.error("Error calculating %s hash: %s", algorithm, str(e))
            hashes[algorithm] = ""
    
    return hashes
