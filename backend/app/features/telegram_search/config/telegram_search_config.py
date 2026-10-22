"""Telegram channel analytics: keyless reads of Telegram's public web pages (`t.me/<name>` and the
`t.me/s/<name>` message preview). See docs/adr/0029-telegram-channel-analytics-web-preview.md."""

TME_BASE_URL = "https://t.me"

# Posts sampled from the `t.me/s/` preview. The preview serves ~20 posts per page, so the
# default is ~5 requests and the cap ~25.
MAX_POSTS_DEFAULT = 100
MAX_POSTS_CAP = 500

# Pause between preview pages - a polite crawl rate for a host we don't control.
PAGE_DELAY_SECONDS = 0.5
REQUEST_TIMEOUT_SECONDS = 20.0
# Telegram sometimes answers 429 with no Retry-After; this is the wait we report then.
DEFAULT_RETRY_AFTER_SECONDS = 60

# Telegram serves a reduced page (no message preview) to clients it doesn't recognize as a
# browser.
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/130.0 Safari/537.36"
)

TOP_FORWARD_SOURCES_N = 10
TOP_MENTIONS_N = 20
TOP_POSTS_N = 5
# Text kept per sampled post in the stored result - enough to recognize it, not an archive.
POST_TEXT_MAX_CHARS = 500
# Indicator lists stored per run; a long-running channel can link thousands of URLs.
MAX_INDICATORS_PER_TYPE = 200

# Domains that are Telegram's own: links to them are channel mentions/navigation, not indicators.
TELEGRAM_DOMAINS = frozenset({"t.me", "telegram.me", "telegram.org", "telegram.dog", "telesco.pe"})
