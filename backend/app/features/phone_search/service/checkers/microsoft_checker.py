"""Checks whether a phone number is registered to a Microsoft account via
`login.live.com`'s public `GetCredentialType.srf` endpoint - the same technique
used by several published Microsoft-account-enumeration tools (e.g. o365spray).
Of this feature's three checkers, this one rests on the most stable/well-documented
API surface, since `GetCredentialType.srf` is also used by legitimate first-party
sign-in flows and its response shape has stayed consistent.
"""

import re

import httpx

PROVIDER_NAME = "Microsoft"

_LOGIN_PAGE_URL = (
    "https://login.live.com/oauth20_authorize.srf"
    "?client_id=00000000480C7F8B"
    "&scope=service%3A%3Aaccount.live.com%3A%3AMBI_SSL"
    "&response_type=code"
    "&redirect_uri=https%3A%2F%2Faccount.live.com%2F"
)
_CREDENTIAL_TYPE_URL = "https://login.live.com/GetCredentialType.srf"
_CANARY_RE = re.compile(r'"apiCanary":"(?P<value>[^"]+)"')

# IfExistsResult == 0 means a Microsoft account exists for the given identifier.
_ACCOUNT_EXISTS_RESULT = 0


async def check(phone_number: str, client: httpx.AsyncClient, timeout: float) -> bool:
    """Return True if `phone_number` is registered to a Microsoft account"""
    login_page = await client.get(_LOGIN_PAGE_URL, timeout=timeout)
    login_page.raise_for_status()

    match = _CANARY_RE.search(login_page.text)
    headers = {"Content-Type": "application/json; charset=UTF-8"}
    if match:
        headers["canary"] = match.group("value")

    response = await client.post(
        _CREDENTIAL_TYPE_URL,
        json={"username": phone_number, "isOtherIdpSupported": False},
        headers=headers,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json().get("IfExistsResult") == _ACCOUNT_EXISTS_RESULT
