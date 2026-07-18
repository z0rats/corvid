import asyncio

import pytest

from app.core.exceptions import AppHTTPException
from app.features.ioc_tools.domain_finder.schemas.domain_schemas import WhoisLookupRequest
from app.features.ioc_tools.domain_finder.service import whois_lookup_service
from app.features.ioc_tools.domain_finder.service.whois_lookup_service import (
    _extract_entities,
    _extract_events,
    _extract_registrar,
    _parse_rdap_date,
    _parse_vcard,
    perform_whois_lookup,
)

RDAP_SAMPLE = {
    "objectClassName": "domain",
    "ldhName": "GOOGLE.COM",
    "status": ["client transfer prohibited", "server delete prohibited"],
    "entities": [
        {
            "objectClassName": "entity",
            "roles": ["registrar"],
            "publicIds": [{"type": "IANA Registrar ID", "identifier": "292"}],
            "vcardArray": ["vcard", [["version", {}, "text", "4.0"], ["fn", {}, "text", "MarkMonitor Inc."]]],
            "entities": [
                {
                    "objectClassName": "entity",
                    "roles": ["abuse"],
                    "vcardArray": ["vcard", [
                        ["version", {}, "text", "4.0"],
                        ["email", {}, "text", "abusecomplaints@markmonitor.com"],
                    ]],
                }
            ],
        }
    ],
    "events": [
        {"eventAction": "registration", "eventDate": "1997-09-15T04:00:00Z"},
        {"eventAction": "expiration", "eventDate": "2028-09-14T04:00:00Z"},
        {"eventAction": "last changed", "eventDate": "2019-09-09T15:39:04Z"},
    ],
    "nameservers": [
        {"objectClassName": "nameserver", "ldhName": "NS1.GOOGLE.COM"},
        {"objectClassName": "nameserver", "ldhName": "NS2.GOOGLE.COM"},
    ],
}


def test_parse_vcard_extracts_name_org_email():
    vcard = _parse_vcard(["vcard", [
        ["version", {}, "text", "4.0"],
        ["fn", {}, "text", "Jane Doe"],
        ["org", {}, "text", ["Example Org"]],
        ["email", {}, "text", "jane@example.com"],
    ]])

    assert vcard == {"name": "Jane Doe", "organization": "Example Org", "email": "jane@example.com"}


def test_parse_vcard_handles_missing_or_malformed_array():
    assert _parse_vcard(None) == {}
    assert _parse_vcard(["vcard"]) == {}
    assert _parse_vcard(["vcard", [["fn"]]]) == {}


def test_extract_registrar_returns_name_and_iana_id():
    name, iana_id = _extract_registrar(RDAP_SAMPLE)

    assert name == "MarkMonitor Inc."
    assert iana_id == "292"


def test_extract_registrar_returns_none_when_absent():
    name, iana_id = _extract_registrar({"entities": []})

    assert name is None
    assert iana_id is None


def test_extract_events_maps_action_to_date():
    events = _extract_events(RDAP_SAMPLE)

    assert events["registration"] == "1997-09-15T04:00:00Z"
    assert events["expiration"] == "2028-09-14T04:00:00Z"
    assert events["last changed"] == "2019-09-09T15:39:04Z"


def test_extract_entities_includes_nested_entities():
    entities = _extract_entities(RDAP_SAMPLE)
    roles = {e.role for e in entities}

    assert "registrar" in roles
    assert "abuse" in roles
    abuse_entity = next(e for e in entities if e.role == "abuse")
    assert abuse_entity.email == "abusecomplaints@markmonitor.com"


def test_parse_rdap_date_parses_z_suffixed_iso8601():
    parsed = _parse_rdap_date("2019-09-09T15:39:04Z")

    assert parsed is not None
    assert parsed.year == 2019 and parsed.month == 9 and parsed.day == 9


def test_parse_rdap_date_returns_none_for_missing_or_invalid():
    assert _parse_rdap_date(None) is None
    assert _parse_rdap_date("not-a-date") is None


def test_perform_whois_lookup_parses_full_response(monkeypatch):
    async def fake_fetch(domain):
        return RDAP_SAMPLE, "rdap.verisign.com"

    monkeypatch.setattr(whois_lookup_service, "fetch_rdap_domain_data", fake_fetch)

    result = asyncio.run(perform_whois_lookup(WhoisLookupRequest(domain="google.com")))

    assert result.domain == "google.com"
    assert result.rdap_server == "rdap.verisign.com"
    assert result.registrar == "MarkMonitor Inc."
    assert result.registrar_iana_id == "292"
    assert result.creation_date.year == 1997
    assert result.expiration_date.year == 2028
    assert result.updated_date.year == 2019
    assert result.nameservers == ["NS1.GOOGLE.COM", "NS2.GOOGLE.COM"]
    assert result.statuses == RDAP_SAMPLE["status"]
    assert result.raw == RDAP_SAMPLE


def test_perform_whois_lookup_registrant_org_none_when_redacted(monkeypatch):
    async def fake_fetch(domain):
        return RDAP_SAMPLE, "rdap.verisign.com"

    monkeypatch.setattr(whois_lookup_service, "fetch_rdap_domain_data", fake_fetch)

    result = asyncio.run(perform_whois_lookup(WhoisLookupRequest(domain="google.com")))

    assert result.registrant_organization is None


def test_perform_whois_lookup_propagates_fetch_errors(monkeypatch):
    async def fake_fetch(domain):
        raise AppHTTPException(status_code=404, detail="not found", error_code="RDAP_NOT_FOUND")

    monkeypatch.setattr(whois_lookup_service, "fetch_rdap_domain_data", fake_fetch)

    with pytest.raises(AppHTTPException) as exc_info:
        asyncio.run(perform_whois_lookup(WhoisLookupRequest(domain="doesnotexist.example")))

    assert exc_info.value.status_code == 404


def test_whois_lookup_request_rejects_wildcard_patterns():
    with pytest.raises(ValueError):
        WhoisLookupRequest(domain="google-*")


def test_whois_lookup_request_normalizes_protocol_and_path():
    req = WhoisLookupRequest(domain="HTTPS://Example.COM/path")

    assert req.domain == "example.com"
