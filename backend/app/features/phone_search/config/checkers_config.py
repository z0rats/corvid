from app.features.phone_search.service.checkers import (
    amazon_checker,
    facebook_checker,
    microsoft_checker,
)

# HTTP-only checkers, no browser automation - kept separate from a future
# browser-driven tier (Google/OpenAI need a full headless browser, unlike these
# three) the same way email_search splits DEFAULT_CHECKERS from HEADLESS_CHECKERS.
CHECKERS = [amazon_checker, microsoft_checker, facebook_checker]


def get_active_checkers() -> list:
    """Build the list of phone-search checker modules to run for a scan"""
    return list(CHECKERS)
