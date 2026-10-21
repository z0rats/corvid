"""`validate_and_format_domain_for_api` normalizes the user's domain before it
is interpolated into third-party API queries (urlscan's search syntax), so it
must strip URL decoration and reject anything outside the hostname/wildcard
alphabet."""

import pytest

from app.features.ioc_tools.domain_finder.utils.validation_utils import (
    sanitize_domain_input,
    validate_and_format_domain_for_api,
    validate_domain_format,
    validate_ip_address_format,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("Example.COM", "example.com"),
        ("  example.com  ", "example.com"),
        ("https://www.example.com/path?q=1#frag", "www.example.com"),
        ("http://example.com:8080/x", "example.com"),
        ("example.com:443", "example.com"),
        # userinfo must be dropped, not mistaken for the host
        ("https://user:pass@example.com/", "example.com"),
        ("https://admin@internal.example:8443/", "internal.example"),
        ("example.com/login", "example.com"),
        ("8.8.8.8", "8.8.8.8"),
        ("*.example.com", "*.example.com"),
        ("EXAMP?E.com", "examp?e.com"),
        ("sub_domain.example.com", None),
    ],
)
def test_validate_and_format_normalizes(raw, expected):
    if expected is None:
        with pytest.raises(ValueError):
            validate_and_format_domain_for_api(raw)
    else:
        assert validate_and_format_domain_for_api(raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "example.com AND page.ip:10.0.0.1",
        'example.com" OR "x',
        "exa mple.com",
        "-bad.example.com",
        "bad-.example.com",
        "a" * 64 + ".com",
        "*.example.com OR x",
        "*.exa(mple).com",
        "user@example.com",
        "example..com",
    ],
)
def test_injection_and_malformed_inputs_rejected(raw):
    with pytest.raises(ValueError):
        validate_and_format_domain_for_api(raw)


def test_ipv6_is_not_port_stripped():
    assert sanitize_domain_input("::1") == "::1"
    assert sanitize_domain_input("2001:db8::1") == "2001:db8::1"
    assert sanitize_domain_input("") == ""


def test_overlong_domain_rejected():
    long = ".".join(["a" * 60] * 5)
    assert len(long) > 255
    assert validate_domain_format(long) is False


@pytest.mark.parametrize(
    ("value", "ok"),
    [
        ("192.168.0.1", True),
        ("255.255.255.255", True),
        ("256.1.1.1", False),
        ("1.2.3", False),
        ("2001:0db8:0000:0000:0000:ff00:0042:8329", True),
        ("::1", True),
        ("example.com", False),
    ],
)
def test_validate_ip_address_format(value, ok):
    assert validate_ip_address_format(value) is ok
