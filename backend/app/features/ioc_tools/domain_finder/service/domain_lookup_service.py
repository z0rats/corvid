"""
Domain lookup business logic service
"""

import logging

from fastapi import HTTPException

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import (
    DomainLookupRequest,
    DomainLookupResponse,
    UrlScanResult,
)
from app.features.ioc_tools.domain_finder.service.urlscan_api_service import (
    fetch_domain_scan_results,
    validate_scan_results_response,
)
from app.features.ioc_tools.domain_finder.utils.validation_utils import (
    validate_and_format_domain_for_api,
)

logger = logging.getLogger(__name__)


async def perform_domain_lookup(domain_request: DomainLookupRequest) -> DomainLookupResponse:
    """
    Perform comprehensive domain lookup using URLScan.io API

    Args:
        domain_request: Validated domain lookup request containing domain to search

    Returns:
        DomainLookupResponse containing scan results and metadata

    Raises:
        HTTPException: When domain validation fails or API request encounters errors
    """
    domain = domain_request.domain
    logger.info("Starting domain lookup for: %s", domain)

    try:
        # Validate and format domain for API request
        formatted_domain = validate_and_format_domain_for_api(domain)
        logger.debug("Domain formatted for API: '%s' -> '%s'", domain, formatted_domain)

        # Fetch raw scan results from URLScan.io API
        raw_scan_results = await fetch_domain_scan_results(formatted_domain)

        # Process and validate scan results
        processed_results = validate_scan_results_response(raw_scan_results)

        # Collapse repeat scans of the same page URL down to the latest one
        deduplicated_results = deduplicate_scan_results(processed_results)

        # Convert to UrlScanResult objects
        scan_results = convert_to_urlscan_results(deduplicated_results)

        response = DomainLookupResponse(
            domain=domain, results=scan_results, total_results=len(scan_results)
        )

        logger.info("Domain lookup completed - Domain: %s, Results: %s", domain, len(scan_results))
        return response

    except ValueError as e:
        logger.error("Domain validation failed for '%s': %s", domain, str(e))
        raise AppHTTPException(
            status_code=400,
            detail=f"Invalid domain format: {str(e)}",
            error_code="DOMAIN_INVALID_FORMAT",
        ) from e
    except HTTPException:
        # Re-raise HTTPExceptions from API service
        raise
    except Exception as e:
        logger.error("Unexpected error during domain lookup for '%s': %s", domain, e, exc_info=True)
        raise AppHTTPException(
            status_code=500,
            detail="An unexpected error occurred during domain lookup",
            error_code="DOMAIN_LOOKUP_ERROR",
        ) from e


def deduplicate_scan_results(processed_results: list[dict]) -> list[dict]:
    """
    Collapse repeat scans of the same page URL down to the most recent one.

    URLScan.io's search API returns one row per individual scan submission, so a
    frequently-scanned page (e.g. a domain's homepage) can appear dozens of times
    with different scan UUIDs/timestamps. Results arrive newest-first, so keeping
    the first occurrence of each URL keeps the latest scan.

    Args:
        processed_results: List of processed scan result dictionaries

    Returns:
        List of scan result dictionaries with duplicate page URLs removed
    """
    deduplicated_results = []
    seen_urls: set[str] = set()

    for result in processed_results:
        page_url = (result.get("page") or {}).get("url")
        if page_url is None or page_url not in seen_urls:
            deduplicated_results.append(result)
            if page_url is not None:
                seen_urls.add(page_url)

    if len(deduplicated_results) != len(processed_results):
        logger.debug(
            "Deduplicated scan results by page URL - Before: %s, After: %s",
            len(processed_results),
            len(deduplicated_results),
        )

    return deduplicated_results


def convert_to_urlscan_results(processed_results: list[dict]) -> list[UrlScanResult]:
    """
    Convert processed scan result dictionaries to UrlScanResult objects

    Args:
        processed_results: List of processed scan result dictionaries

    Returns:
        List of UrlScanResult objects for API response
    """
    scan_results = []

    for i, result_data in enumerate(processed_results):
        try:
            scan_result = UrlScanResult(**result_data)
            scan_results.append(scan_result)
            logger.debug("Converted result %s/%s to UrlScanResult", i + 1, len(processed_results))
        except Exception as e:
            logger.warning(
                "Failed to convert result %s/%s to UrlScanResult: %s",
                i + 1,
                len(processed_results),
                e,
            )
            continue

    if len(scan_results) != len(processed_results):
        logger.warning(
            "Some results failed conversion - Processed: %s, Converted: %s",
            len(processed_results),
            len(scan_results),
        )

    return scan_results
