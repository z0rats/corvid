"""Checks whether a phone number is registered to a Facebook account via the
account-recovery "identify" form (the same entry point as Facebook's own
"forgotten password" flow): submitting a registered phone/email proceeds to a
found-account step, while an unregistered one returns a "no search results"
response.

Same caveat as amazon_checker: `_NOT_FOUND_MARKER`/the form selectors below are
a best-effort read of Facebook's current identify page, not a documented API -
expect to need to adjust them against the live page.
"""

import httpx
from bs4 import BeautifulSoup

PROVIDER_NAME = "Facebook"

_IDENTIFY_URL = "https://www.facebook.com/login/identify/"

# Text Facebook's response shows when no account matches the submitted identifier.
_NOT_FOUND_MARKER = "no search results"


async def check(phone_number: str, client: httpx.AsyncClient, timeout: float) -> bool:
    """Return True if `phone_number` is registered to a Facebook account"""
    page = await client.get(_IDENTIFY_URL, timeout=timeout)
    page.raise_for_status()

    soup = BeautifulSoup(page.text, "lxml")
    form = soup.find("form")
    if form is None:
        raise ValueError("Facebook identify form not found - page layout likely changed")

    action = str(form.get("action") or page.url)
    payload = {
        str(input_tag["name"]): str(input_tag.get("value") or "")
        for input_tag in form.find_all("input")
        if input_tag.get("name")
    }
    email_field = soup.find("input", {"id": "identify_email"})
    field_name = str(email_field.get("name") or "email") if email_field else "email"
    payload[field_name] = phone_number

    result = await client.post(action, data=payload, timeout=timeout)
    result.raise_for_status()
    return _NOT_FOUND_MARKER not in result.text.lower()
