"""Scrubs API keys/tokens out of log records before they're written.

Several IOC-lookup providers (Hunter.io, Pulsedive, Shodan, Google Safe
Browsing, IPQualityScore) pass their API key in the request URL rather than a
header. An `httpx.HTTPStatusError`'s str() embeds the full request URL, so a
broad `except Exception as e: logger.error(..., str(e))` (e.g. in
bulk_ioc_lookup_service.py) can leak the key into data/logs/*.log if such an
exception ever escapes the normal response-handling path.

Matches by pattern rather than looking up live key values, so newly added
providers/keys are covered without touching this file.
"""
import logging
import re

_QUERY_PARAM_SECRET_RE = re.compile(
    r"(?i)([?&](?:api[_-]?key|apikey|key|token|secret|password|passwd|pwd|access[_-]?token|auth)=)[^&\s\"']+"
)
_BEARER_RE = re.compile(r"(?i)(Bearer\s+)[A-Za-z0-9\-_.~+/]+=*")
# IPQualityScore embeds the key as a URL path segment instead of a query param:
# https://www.ipqualityscore.com/api/json/ip/<KEY>/<ioc>
_IPQS_PATH_RE = re.compile(r"(ipqualityscore\.com/api/json/[a-z]+/)[A-Za-z0-9]+(/)")


class SecretRedactionFilter(logging.Filter):
    """Logging filter that redacts secret-looking substrings from every record."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        redacted = _QUERY_PARAM_SECRET_RE.sub(r"\1***REDACTED***", message)
        redacted = _BEARER_RE.sub(r"\1***REDACTED***", redacted)
        redacted = _IPQS_PATH_RE.sub(r"\1***REDACTED***\2", redacted)
        if redacted != message:
            record.msg = redacted
            record.args = ()
        return True
