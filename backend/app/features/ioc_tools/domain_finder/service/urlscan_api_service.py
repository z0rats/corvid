"""
URLScan.io API service for domain lookup operations
"""

import logging
from typing import Any

import httpx

from app.features.ioc_tools.domain_finder.config.api_config import (
    URLSCAN_BASE_URL,
    URLSCAN_SEARCH_ENDPOINT,
    URLSCAN_TIMEOUT,
)
from app.features.ioc_tools.domain_finder.service.provider_http import Provider, provider_get

logger = logging.getLogger(__name__)

URLSCAN = Provider(
    name="URLScan.io",
    code="URLSCAN",
    base_url=URLSCAN_BASE_URL,
    timeout=URLSCAN_TIMEOUT,
    accept=None,
)


async def fetch_domain_scan_results(domain: str) -> list[dict[str, Any]]:
    """Raw URLScan.io search results for a domain. Failures raise `AppHTTPException`
    (`provider_http`)."""

    def parse(response: httpx.Response) -> list[dict[str, Any]]:
        data = response.json()
        if "results" not in data:
            logger.warning("No 'results' key in URLScan.io response for domain: %s", domain)
            return []
        raw_results = data["results"]
        logger.info(
            "Retrieved %s raw results from URLScan.io for domain: %s", len(raw_results), domain
        )
        return raw_results

    return await provider_get(
        URLSCAN, f"{URLSCAN_SEARCH_ENDPOINT}?q=domain:{domain}", subject=domain, parse=parse
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
        processed_result = {**raw_result, "expanded": False}
        return processed_result
    except Exception as e:
        logger.warning("Failed to process scan result: %s", e)
        # Return minimal structure if processing fails
        return {"expanded": False, "error": "Failed to process result"}


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
            logger.debug("Successfully processed result %s/%s", i + 1, len(raw_results))
        except Exception as e:
            logger.warning("Failed to process result %s/%s: %s", i + 1, len(raw_results), e)
            continue

    if len(processed_results) != len(raw_results):
        logger.warning(
            "Some results were skipped during processing - Raw: %s, Processed: %s",
            len(raw_results),
            len(processed_results),
        )

    return processed_results
