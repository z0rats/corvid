"""One vocabulary for "what happened when we asked a third-party source".

`SourceOutcome` separates a source that *answered with nothing* (`EMPTY`) from one that
*answered in a different shape* (`DRIFT`) and from one that *didn't answer us* (`UNREACHABLE`,
`BLOCKED`, `AUTH`). `classify` maps the failures the three source families raise
(`ioc_lookup`'s `ServiceError`s, `domain_finder`'s `AppHTTPException`s, `ru_business_check`'s
Russian `ValueError`s, raw httpx errors) onto it; the live canaries (`tests/canary/policy.py`)
skip on `UNREACHABLE`/`BLOCKED` and fail on the rest.
"""

import enum
import re

import httpx

from app.core.exceptions import AppHTTPException
from app.core.external_sources.contract import SourceDriftError
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError,
    ServiceError,
)


class SourceOutcome(enum.Enum):
    OK = "ok"
    EMPTY = "empty"  # answered in the expected shape: nothing found
    UNREACHABLE = "unreachable"  # network error, timeout, 5xx
    BLOCKED = "blocked"  # anti-bot / geo / rate limit (403, 429, 451, captcha)
    AUTH = "auth"  # 401, or a keyed source without a valid key
    DRIFT = "drift"  # answered, but not in the expected shape


# `ru_business_check` clients report failures as Russian `ValueError` messages; these are the
# "didn't answer us" ones. Everything else from them is DRIFT - notably an unexpected
# empty/partial answer ("Ничего не найдено", "выдача усечена").
RU_NOT_ANSWERING = re.compile(
    r"недоступен|ограничил доступ|капч|лимит запросов|не ответил|Тайм-аут"
    r"|HTTP (?:401|403|429|451|5\d\d)\b"
)

_BLOCKED_STATUSES = frozenset({403, 429, 451})

# domain_finder's `provider_http` error-code suffixes (`<CODE>_<SUFFIX>`).
_UNREACHABLE_SUFFIXES = ("_TIMEOUT", "_CONNECTION_ERROR")
_BLOCKED_SUFFIXES = ("_RATE_LIMITED",)


def _from_status(status: int) -> SourceOutcome:
    if status == 401:
        return SourceOutcome.AUTH
    if status in _BLOCKED_STATUSES:
        return SourceOutcome.BLOCKED
    if status >= 500:
        return SourceOutcome.UNREACHABLE
    return SourceOutcome.DRIFT


def classify(exc: BaseException) -> SourceOutcome:
    """The outcome a live call's exception stands for. Never returns `OK`/`EMPTY` (those
    describe results, not failures); an unrecognised error is `DRIFT` - the source did not
    behave as the parser expects - so a canary fails on it rather than skipping."""
    if isinstance(exc, SourceDriftError):
        return SourceOutcome.DRIFT
    if isinstance(exc, (httpx.TransportError, OSError)):
        return SourceOutcome.UNREACHABLE
    if isinstance(exc, ServiceAuthError):
        return SourceOutcome.AUTH
    if isinstance(exc, ServiceError):
        return _from_status(exc.status_code)
    if isinstance(exc, AppHTTPException):
        code = exc.error_code or ""
        if code.endswith(_UNREACHABLE_SUFFIXES):
            return SourceOutcome.UNREACHABLE
        if code.endswith(_BLOCKED_SUFFIXES):
            return SourceOutcome.BLOCKED
        if code.endswith("_API_ERROR"):
            return _from_status(exc.status_code)
        return SourceOutcome.DRIFT
    if isinstance(exc, httpx.HTTPStatusError):
        return _from_status(exc.response.status_code)
    if isinstance(exc, ValueError) and RU_NOT_ANSWERING.search(str(exc)):
        return SourceOutcome.BLOCKED
    return SourceOutcome.DRIFT
