import json
from pathlib import Path

import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.utils.ioc_utils import (
    IOC_TYPES,
    determine_ioc_type,
    normalize_address,
)

# Shared with the frontend's port of this classifier (core/utils/iocTypeDetection.js) via
# testdata/ioc-type-detection-cases.json at the repo root, so the two can't silently diverge.
FIXTURE_PATH = Path(__file__).resolve().parents[4] / "testdata" / "ioc-type-detection-cases.json"
HAPPY_PATH_CASES = [
    (case["value"], case["expectedType"])
    for case in json.loads(FIXTURE_PATH.read_text())
]


@pytest.mark.parametrize("ioc, expected_type", HAPPY_PATH_CASES)
def test_determine_ioc_type_happy_path(ioc, expected_type):
    assert determine_ioc_type(ioc) == expected_type


def test_url_wins_over_domain_when_scheme_present():
    # A bare domain with a URL scheme/path must not be misclassified as a
    # Domain just because the domain pattern also matches its authority part.
    assert determine_ioc_type("https://evil.com/login") == IOC_TYPES["URL"]
    assert determine_ioc_type("evil.com/login") == IOC_TYPES["UNKNOWN"]


def test_email_is_not_misclassified_as_domain():
    # The local part before '@' would not satisfy the domain pattern on its
    # own, but this guards the intended priority (domain checked before email).
    assert determine_ioc_type("first.last@sub.example.co.uk") == IOC_TYPES["EMAIL"]


def test_domain_is_not_misclassified_as_email():
    assert determine_ioc_type("sub.example.co.uk") == IOC_TYPES["DOMAIN"]


def test_hash_like_length_boundaries_do_not_bleed_into_each_other():
    md5 = "a" * 32
    sha1 = "a" * 40
    sha256 = "a" * 64
    assert determine_ioc_type(md5) == IOC_TYPES["MD5"]
    assert determine_ioc_type(sha1) == IOC_TYPES["SHA1"]
    assert determine_ioc_type(sha256) == IOC_TYPES["SHA256"]
    # one character short/long of a valid hash length must not match any hash type
    assert determine_ioc_type("a" * 31) == IOC_TYPES["UNKNOWN"]
    assert determine_ioc_type("a" * 33) == IOC_TYPES["UNKNOWN"]


def test_evm_address_checked_before_hash_patterns():
    # A 0x-prefixed 40-hex-char string is also 42 chars total, which does not
    # collide with any hash length, but confirms EVM is tried before generic
    # hex-hash patterns rather than falling through to UNKNOWN.
    evm = "0x" + "a" * 40
    assert determine_ioc_type(evm) == IOC_TYPES["EVM_ADDRESS"]


def test_whitespace_is_stripped_before_classification():
    assert determine_ioc_type("  8.8.8.8  ") == IOC_TYPES["IPV4"]


def test_ipv4_out_of_range_octet_is_not_misclassified_as_ipv4():
    assert determine_ioc_type("999.999.999.999") != IOC_TYPES["IPV4"]


def test_normalize_address_lowercases_evm_only():
    mixed_case_evm = "0x5aAeb6053f3e94c9b9a09f33669435E7ef1BeAed"
    assert normalize_address(mixed_case_evm) == mixed_case_evm.lower()

    btc = "1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa"
    assert normalize_address(btc) == btc


def test_normalize_address_strips_whitespace():
    assert normalize_address("  0x5aAeb6053f3e94c9b9a09f33669435E7ef1BeAed  ") == (
        "0x5aaeb6053f3e94c9b9a09f33669435e7ef1beaed"
    )
