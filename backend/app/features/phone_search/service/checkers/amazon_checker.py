"""Checks whether a phone number is registered to an Amazon account by driving
its sign-in identifier form: submitting a known account's phone/email takes you
to a password prompt, while an unknown one takes you to an account-creation
confirmation page.

The exact form-field names and the "new account" text marker below are this
feature's best-effort read of Amazon's current sign-in page - unlike
microsoft_checker's GetCredentialType.srf, this isn't a documented API and
Amazon can change its markup at any time without notice. Treat a wrong result
here as a signal to re-check `_NEW_ACCOUNT_MARKER`/the form selectors against
the live page, not a bug in the surrounding scan machinery.
"""

import httpx
from bs4 import BeautifulSoup

PROVIDER_NAME = "Amazon"

_SIGNIN_URL = (
    "https://www.amazon.com/ap/signin"
    "?openid.pape.max_auth_age=0"
    "&openid.return_to=https%3A%2F%2Fwww.amazon.com%2F%3Fref_%3Dnav_signin"
    "&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
    "&openid.assoc_handle=usflex"
    "&openid.mode=checkid_setup"
    "&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select"
    "&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0"
)

# Text Amazon's response shows when the submitted identifier has no existing account.
_NEW_ACCOUNT_MARKER = "new to amazon"


async def check(phone_number: str, client: httpx.AsyncClient, timeout: float) -> bool:
    """Return True if `phone_number` is registered to an Amazon account"""
    page = await client.get(_SIGNIN_URL, timeout=timeout)
    page.raise_for_status()

    soup = BeautifulSoup(page.text, "lxml")
    form = soup.find("form", {"name": "signIn"}) or soup.find("form")
    if form is None:
        raise ValueError("Amazon sign-in form not found - page layout likely changed")

    action = str(form.get("action") or page.url)
    payload = {
        str(input_tag["name"]): str(input_tag.get("value") or "")
        for input_tag in form.find_all("input")
        if input_tag.get("name")
    }
    payload["email"] = phone_number

    result = await client.post(action, data=payload, timeout=timeout)
    result.raise_for_status()
    return _NEW_ACCOUNT_MARKER not in result.text.lower()
