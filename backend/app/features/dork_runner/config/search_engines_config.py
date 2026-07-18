"""Per-engine request configuration for the dork runner.

DuckDuckGo's HTML endpoint is the default/recommended engine - unlike Google
and Bing it doesn't require JS execution and is far less aggressive about
blocking scripted queries, without needing a paid API key for either. Google
and Bing are still offered as selectable engines but are best-effort: they
CAPTCHA/block scraped queries quickly, so failures there are expected and
handled gracefully rather than treated as errors.
"""

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

REQUEST_TIMEOUT = 15.0
MAX_RETRIES = 2
RETRY_DELAY = 1.5

# Politeness delay awaited between each sequential dork query within a run,
# to reduce rate-limit/CAPTCHA risk - queries are never fired in parallel.
REQUEST_DELAY_SECONDS = 2.0

# Hard cap on templates/queries per run, regardless of how many are requested,
# since each query is a real outbound request paced by REQUEST_DELAY_SECONDS.
MAX_QUERIES_PER_RUN = 12

DUCKDUCKGO_URL = "https://html.duckduckgo.com/html/"
GOOGLE_URL = "https://www.google.com/search"
BING_URL = "https://www.bing.com/search"

MAX_RESULTS_PER_QUERY = 15
