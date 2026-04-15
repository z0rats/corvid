"""
URLScan.io API service for domain lookup operations
"""
import logging
from typing import Any
import httpx
from fastapi import HTTPException

from app.features.ioc_tools.domain_finder.config.api_config import (
    URLSCAN_BASE_URL,
    URLSCAN_SEARCH_ENDPOINT,
    URLSCAN_TIMEOUT,
    DEFAULT_HEADERS,
    MAX_RETRIES,
    RETRY_DELAY
)

logger = logging.getLogger(__name__)


async def fetch_domain_scan_results(domain: str) -> list[dict[str, Any]]:
    """
    Fetch scan results from URLScan.io API for a specific domain
    
    Args:
        domain: Domain name to search for
        
    Returns:
        List of scan result dictionaries from URLScan.io API
        
    Raises:
        HTTPException: For API request failures or HTTP errors
    """
    url = f"{URLSCAN_BASE_URL}{URLSCAN_SEARCH_ENDPOINT}?q=domain:{domain}"
    logger.debug("Fetching URLScan data from: %s", url)
    
    try:
        async with httpx.AsyncClient(timeout=URLSCAN_TIMEOUT, headers=DEFAULT_HEADERS) as client:
            logger.debug("Making HTTP request to URLScan.io for domain: %s", domain)
            response = await client.get(url)
            
            logger.debug("URLScan.io response - Status: %s, Domain: %s", response.status_code, domain)
            response.raise_for_status()
            
            data = response.json()
            logger.debug("Successfully parsed URLScan.io JSON response for domain: %s", domain)
            
            if 'results' not in data:
                logger.warning("No 'results' key in URLScan.io response for domain: %s", domain)
                return []
            
            raw_results = data['results']
            logger.info("Retrieved %s raw results from URLScan.io for domain: %s", len(raw_results), domain)
            
            return raw_results
            
    except httpx.TimeoutException as e:
        logger.error("Timeout while fetching URLScan.io data for domain %s: %s", domain, e)
        raise HTTPException(
            status_code=504,
            detail=f"Request timeout while connecting to URLScan.io service"
        )
    except httpx.RequestError as e:
        logger.error("Request error while fetching URLScan.io data for domain %s: %s", domain, e)
        raise HTTPException(
            status_code=503,
            detail=f"Failed to connect to URLScan.io service: {str(e)}"
        )
    except httpx.HTTPStatusError as e:
        logger.error("HTTP status error from URLScan.io for domain %s: Status %s", domain, e.response.status_code)
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"URLScan.io API returned error: {e.response.status_code}"
        )
    except Exception as e:
        logger.error("Unexpected error while fetching URLScan.io data for domain %s: %s", domain, e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while fetching scan data"
        )


def process_scan_result_for_response(raw_result: dict[str, Any]) -> dict[str, Any]:
    """
    Process a single raw scan result from URLScan.io API for response formatting
    
    Args:
        raw_result: Raw scan result dictionary from URLScan.io API
        
    Returns:
        Processed scan result with UI compatibility fields added
    """
    try:
        processed_result = {**raw_result, 'expanded': False}
        return processed_result
    except Exception as e:
        logger.warning("Failed to process scan result: %s", e)
        # Return minimal structure if processing fails
        return {'expanded': False, 'error': 'Failed to process result'}


def validate_scan_results_response(raw_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Validate and process scan results from URLScan.io API response
    
    Args:
        raw_results: List of raw scan result dictionaries
        
    Returns:
        List of validated and processed scan results
    """
    processed_results = []
    
    for i, raw_result in enumerate(raw_results):
        try:
            processed_result = process_scan_result_for_response(raw_result)
            processed_results.append(processed_result)
            logger.debug("Successfully processed result %s/%s", i+1, len(raw_results))
        except Exception as e:
            logger.warning("Failed to process result %s/%s: %s", i+1, len(raw_results), e)
            continue
    
    if len(processed_results) != len(raw_results):
        logger.warning("Some results were skipped during processing - Raw: %s, Processed: %s", len(raw_results), len(processed_results))
    
    return processed_results
