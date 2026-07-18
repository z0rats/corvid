"""
Domain lookup API configuration settings
"""

# URLScan.io API configuration
URLSCAN_BASE_URL = "https://urlscan.io/api/v1"
URLSCAN_SEARCH_ENDPOINT = "/search/"
URLSCAN_TIMEOUT = 30.0

# Request configuration
DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": "Corvid-Domain-Lookup/1.0"
}

# Response limits
MAX_RESULTS_PER_REQUEST = 100
DEFAULT_RESULTS_LIMIT = 50

# Validation settings
MAX_DOMAIN_LENGTH = 255
MIN_DOMAIN_LENGTH = 1

# Retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1.0
