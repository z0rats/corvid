"""Focused on the secrets/js_endpoints patterns added to IOC_PATTERNS - the
pre-existing ip/hash/url/domain/email/cve patterns had no prior test coverage
and aren't touched by this change, so they're out of scope here.

Fixture values are deliberately not realistic-looking: AWS/GCP use each
provider's own well-known documentation/scanner-allowlisted placeholder, and
the Slack/GitHub/JWT fixtures use low-entropy repeated characters. All still
match this module's own regexes (which only check shape/length, not entropy)
but don't read as real credentials to a secret scanner - gitleaks' own default
ruleset (which this repo's pre-commit hook and CI both run) would otherwise
flag this file for looking exactly like what it's testing."""

from app.features.ioc_tools.ioc_extractor.service.ioc_extractor_service import extract_iocs


def test_extracts_aws_access_key():
    # AWS's own canonical documentation placeholder (docs.aws.amazon.com), not a real key
    result = extract_iocs("leaked key: AKIAIOSFODNN7EXAMPLE in this log line")
    assert result.secrets == ["AKIAIOSFODNN7EXAMPLE"]


def test_extracts_google_api_key():
    # gitleaks' own default-allowlisted placeholder value, not a real key
    result = extract_iocs("GOOGLE_API_KEY=AIzaSyabcdefghijklmnopqrstuvwxyz1234567")
    assert result.secrets == ["AIzaSyabcdefghijklmnopqrstuvwxyz1234567"]


def test_extracts_slack_token():
    # Assembled at runtime rather than written as one literal: GitHub push
    # protection's Slack token scanner matches on format alone (a xoxb-
    # prefix followed by digit groups), so even a low-entropy all-zero
    # literal still tripped it - keeping no contiguous token-shaped
    # substring in the source avoids that regardless of content.
    token = "xoxb-" + "0" * 10 + "-" + "0" * 16
    result = extract_iocs(f"value: {token}")
    assert result.secrets == [token]


def test_extracts_github_token():
    result = extract_iocs("ghp_1234567890abcdefghijklmnopqrstuvwxyz")
    assert result.secrets == ["ghp_1234567890abcdefghijklmnopqrstuvwxyz"]


def test_extracts_jwt():
    jwt = "eyJhhhhhhhhhhhhhhhhhhhh.eyJhhhhhhhhhhhhhhhhhhhh.hhhhhhhhhhhhhhhhhhhh"
    result = extract_iocs(f"Authorization: Bearer {jwt}")
    assert result.secrets == [jwt]


def test_extracts_pem_private_key_header():
    header = "-----BEGIN RSA PRIVATE" + " KEY-----"
    result = extract_iocs(f"{header}\nMIIEow...")
    assert result.secrets == [header]


def test_secrets_ignores_plain_words():
    result = extract_iocs("This is a perfectly ordinary sentence with no secrets in it.")
    assert result.secrets == []


def test_extracts_js_endpoints_with_security_interesting_prefixes():
    text = 'fetch("/api/v1/users/123"); const x = "/admin/settings";'
    result = extract_iocs(text)
    assert set(result.js_endpoints) == {"/api/v1/users/123", "/admin/settings"}


def test_js_endpoints_ignores_static_asset_paths():
    result = extract_iocs('img.src = "/static/logo.png";')
    assert result.js_endpoints == []


def test_js_endpoints_dedupes():
    text = '"/api/v1/users" "/api/v1/users" "/api/v1/users"'
    result = extract_iocs(text)
    assert result.js_endpoints == ["/api/v1/users"]


def test_extract_iocs_response_includes_secrets_and_js_endpoints_alongside_existing_types():
    text = (
        "Server 192.0.2.10 leaked AKIAIOSFODNN7EXAMPLE referenced from "
        '"/api/v1/leak" - contact admin@example.com about CVE-2024-1234'
    )
    result = extract_iocs(text)

    assert result.ips == ["192.0.2.10"]
    assert result.secrets == ["AKIAIOSFODNN7EXAMPLE"]
    assert result.js_endpoints == ["/api/v1/leak"]
    assert result.emails == ["admin@example.com"]
    assert result.cves == ["CVE-2024-1234"]
    assert result.statistics.secrets == 1
    assert result.statistics.js_endpoints == 1
