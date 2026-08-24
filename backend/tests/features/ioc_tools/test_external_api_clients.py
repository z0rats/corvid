"""Representative sample across external_api_clients.py's ~24 near-identical
provider functions (chosen per code-review guidance for this coverage push):
check_abuseipdb (the plain GET+apikey-header baseline most providers share),
check_hibp (special-cases 404 instead of treating it as an error),
check_virustotal (ioc_type-dependent URL/encoding + its own 404 special-case),
check_shodan (method-dependent endpoint selection), check_ffraud (keyless),
and check_blacklist (DB-backed, no HTTP at all). Exercises real httpx.Response
objects through the real handle_response, rather than mocking away the parsing
logic being tested.
"""

from base64 import b64encode

import httpx
import pytest

from app.features.ioc_tools.ioc_lookup.single_lookup.models.blacklist_models import (
    BlacklistedAddress,
    BlacklistSource,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service import external_api_clients
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import (
    ServiceAuthError,
    ServiceError,
)
from tests.conftest import run as _run


def _response(status_code: int, json=None) -> httpx.Response:
    request = httpx.Request("GET", "https://service.example/api")
    return httpx.Response(status_code, request=request, json=json if json is not None else {})


class _FakeClient:
    """Records the last call and returns a canned response, standing in for
    the shared httpx.AsyncClient (no respx/pytest-httpx dependency here)."""

    def __init__(self, response: httpx.Response):
        self._response = response
        self.last_call: dict | None = None

    async def get(self, url, **kwargs):
        self.last_call = {"method": "GET", "url": url, **kwargs}
        return self._response

    async def post(self, url, **kwargs):
        self.last_call = {"method": "POST", "url": url, **kwargs}
        return self._response


def _patch_client(monkeypatch, response: httpx.Response) -> _FakeClient:
    fake = _FakeClient(response)
    monkeypatch.setattr(external_api_clients, "get_client", lambda: fake)
    return fake


# --- check_abuseipdb: the plain GET+apikey baseline pattern -------------


class TestCheckAbuseipdb:
    def test_requires_apikey(self):
        with pytest.raises(ServiceAuthError):
            _run(external_api_clients.check_abuseipdb("1.2.3.4", ""))

    def test_returns_parsed_json_on_success(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json={"data": {"abuseConfidenceScore": 10}}))

        result = _run(external_api_clients.check_abuseipdb("1.2.3.4", "key"))

        assert result == {"data": {"abuseConfidenceScore": 10}}

    def test_sends_ioc_and_key_in_request(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200))

        _run(external_api_clients.check_abuseipdb("1.2.3.4", "my-key"))

        assert fake.last_call["params"]["ipAddress"] == "1.2.3.4"
        assert fake.last_call["headers"]["Key"] == "my-key"

    def test_raises_service_error_on_http_error(self, monkeypatch):
        _patch_client(monkeypatch, _response(500, json={"message": "internal error"}))

        with pytest.raises(ServiceError):
            _run(external_api_clients.check_abuseipdb("1.2.3.4", "key"))


# --- check_hibp: 404 means "not found", not an error ---------------------


class TestCheckHibp:
    def test_404_is_treated_as_no_breaches_found(self, monkeypatch):
        _patch_client(monkeypatch, _response(404))

        result = _run(external_api_clients.check_hibp("a@example.com", "key"))

        assert result == {"message": "Not found in any breaches."}

    def test_200_returns_breach_data(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json=[{"Name": "Adobe"}]))

        result = _run(external_api_clients.check_hibp("a@example.com", "key"))

        assert result == [{"Name": "Adobe"}]

    def test_other_error_status_still_raises(self, monkeypatch):
        _patch_client(monkeypatch, _response(429))

        with pytest.raises(ServiceError):
            _run(external_api_clients.check_hibp("a@example.com", "key"))


# --- check_virustotal: ioc_type dispatch + its own 404 special-case ------


class TestCheckVirustotal:
    def test_requires_apikey(self):
        with pytest.raises(ServiceAuthError):
            _run(external_api_clients.check_virustotal("1.2.3.4", "ip", ""))

    def test_ip_type_uses_ip_addresses_endpoint(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200))

        _run(external_api_clients.check_virustotal("1.2.3.4", "ip", "key"))

        assert fake.last_call["url"] == "https://www.virustotal.com/api/v3/ip_addresses/1.2.3.4"

    def test_url_type_base64_encodes_the_indicator(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200))

        _run(external_api_clients.check_virustotal("http://evil.example", "url", "key"))

        expected_encoded = b64encode(b"http://evil.example").decode().strip("=")
        assert fake.last_call["url"] == f"https://www.virustotal.com/api/v3/urls/{expected_encoded}"

    def test_unknown_ioc_type_falls_back_to_ip_addresses(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200))

        _run(external_api_clients.check_virustotal("something", "unknown-type", "key"))

        assert "/ip_addresses/" in fake.last_call["url"]

    def test_404_raises_not_found_service_error(self, monkeypatch):
        _patch_client(monkeypatch, _response(404))

        with pytest.raises(ServiceError) as exc_info:
            _run(external_api_clients.check_virustotal("1.2.3.4", "ip", "key"))

        assert exc_info.value.status_code == 404
        assert "VirusTotal" in exc_info.value.message


# --- check_shodan: method-dependent endpoint selection --------------------


class TestCheckShodan:
    def test_ip_method_uses_host_endpoint(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200))

        _run(external_api_clients.check_shodan("1.2.3.4", "ip", "key"))

        assert "/shodan/host/1.2.3.4" in fake.last_call["url"]

    def test_domain_method_uses_dns_domain_endpoint(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200))

        _run(external_api_clients.check_shodan("example.com", "domain", "key"))

        assert "/shodan/dns/domain/example.com" in fake.last_call["url"]


# --- check_leakix: host lookup, api-key header ----------------------------


class TestCheckLeakix:
    def test_requires_apikey(self):
        with pytest.raises(ServiceAuthError):
            _run(external_api_clients.check_leakix("1.2.3.4", ""))

    def test_returns_parsed_json_on_success(self, monkeypatch):
        _patch_client(
            monkeypatch, _response(200, json={"Services": [{"port": "443"}], "Leaks": []})
        )

        result = _run(external_api_clients.check_leakix("1.2.3.4", "key"))

        assert result == {"Services": [{"port": "443"}], "Leaks": []}

    def test_sends_ioc_in_url_and_key_in_header(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200))

        _run(external_api_clients.check_leakix("1.2.3.4", "my-key"))

        assert fake.last_call["url"] == "https://leakix.net/host/1.2.3.4"
        assert fake.last_call["headers"]["api-key"] == "my-key"
        assert fake.last_call["headers"]["Accept"] == "application/json"

    def test_raises_auth_error_on_invalid_key(self, monkeypatch):
        _patch_client(monkeypatch, _response(401, json="Invalid API key"))

        with pytest.raises(ServiceError):
            _run(external_api_clients.check_leakix("1.2.3.4", "bad-key"))


# --- check_ffraud: keyless -----------------------------------------------


class TestCheckFfraud:
    def test_succeeds_without_an_apikey_argument(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json={"fraud_score": 0}))

        result = _run(external_api_clients.check_ffraud("1.2.3.4"))

        assert result == {"fraud_score": 0}


# --- check_hudsonrock: keyless, ioc_type-dependent endpoint selection -----


class TestCheckHudsonrock:
    def test_email_type_uses_search_by_email_endpoint(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json={"stealers": []}))

        _run(external_api_clients.check_hudsonrock("test@example.com", "email"))

        assert "/osint-tools/search-by-email" in fake.last_call["url"]
        assert fake.last_call["params"] == {"email": "test@example.com"}

    def test_ip_type_uses_search_by_ip_endpoint(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json={"stealers": []}))

        _run(external_api_clients.check_hudsonrock("1.1.1.1", "ip"))

        assert "/osint-tools/search-by-ip" in fake.last_call["url"]
        assert fake.last_call["params"] == {"ip": "1.1.1.1"}

    def test_domain_type_uses_search_by_domain_endpoint(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json={"total": 0}))

        _run(external_api_clients.check_hudsonrock("example.com", "domain"))

        assert "/osint-tools/search-by-domain" in fake.last_call["url"]
        assert fake.last_call["params"] == {"domain": "example.com"}

    def test_no_hit_shape_passes_through_unchanged(self, monkeypatch):
        no_hit = {
            "message": "not associated",
            "stealers": [],
            "total_corporate_services": 0,
            "total_user_services": 0,
        }
        _patch_client(monkeypatch, _response(200, json=no_hit))

        result = _run(external_api_clients.check_hudsonrock("clean@example.com", "email"))

        assert result == no_hit

    def test_succeeds_without_an_apikey_argument(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json={"stealers": []}))

        result = _run(external_api_clients.check_hudsonrock("test@example.com", "email"))

        assert result == {"stealers": []}


# --- check_libraryofleaks: keyless, must never surface raw entity content -


# Shape actually observed from the live API (`docs/library-of-leaks-integration-plan.md`):
# `results` entities carry raw leaked content in `properties` (emails, names, password
# mentions, document titles); `facets.collection_id.values` gives per-collection counts
# without needing to fetch any entity at all.
_LIBRARYOFLEAKS_RAW_RESPONSE = {
    "status": "ok",
    "total": 128,
    "results": [
        {
            "schema": "HyperText",
            "properties": {
                "emailMentioned": ["haytham@puckettfaraj.com"],
                "peopleMentioned": ["Haytham Password"],
                "title": ["Your new password"],
            },
        }
    ],
    "facets": {
        "collection_id": {
            "values": [
                {"id": "1", "label": "BlueLeaks", "category": "leak", "count": 9},
                {"id": "31", "label": "Fuck FBI Friday", "category": "leak", "count": 3},
            ]
        }
    },
}


class TestCheckLibraryOfLeaks:
    def test_succeeds_without_an_apikey_argument(self, monkeypatch):
        _patch_client(monkeypatch, _response(200, json=_LIBRARYOFLEAKS_RAW_RESPONSE))

        result = _run(external_api_clients.check_libraryofleaks("person@example.com"))

        assert result["total_hits"] == 128

    def test_requests_facets_only_never_matching_entities(self, monkeypatch):
        fake = _patch_client(monkeypatch, _response(200, json=_LIBRARYOFLEAKS_RAW_RESPONSE))

        _run(external_api_clients.check_libraryofleaks("person@example.com"))

        params = fake.last_call["params"]
        assert params["q"] == "person@example.com"
        assert params["limit"] == 0
        assert params["facet"] == "collection_id"

    def test_parsed_result_never_contains_raw_entity_content(self, monkeypatch):
        """Regression guard for the plan's core requirement: `properties` (and everything
        under it — emails, names, password mentions from the leaked documents themselves)
        must never leak into the dict that becomes `SingleLookupResult.data`."""
        _patch_client(monkeypatch, _response(200, json=_LIBRARYOFLEAKS_RAW_RESPONSE))

        result = _run(external_api_clients.check_libraryofleaks("person@example.com"))

        assert result == {
            "query": "person@example.com",
            "total_hits": 128,
            "collections": [
                {
                    "label": "BlueLeaks",
                    "category": "leak",
                    "count": 9,
                    "url": "https://search.libraryofleaks.org/datasets/1",
                },
                {
                    "label": "Fuck FBI Friday",
                    "category": "leak",
                    "count": 3,
                    "url": "https://search.libraryofleaks.org/datasets/31",
                },
            ],
            "search_url": "https://search.libraryofleaks.org/search?q=person%40example.com",
        }
        assert "properties" not in str(result)
        assert "password" not in str(result).lower()

    def test_zero_hits(self, monkeypatch):
        no_hit = {
            "status": "ok",
            "total": 0,
            "results": [],
            "facets": {"collection_id": {"values": []}},
        }
        _patch_client(monkeypatch, _response(200, json=no_hit))

        result = _run(external_api_clients.check_libraryofleaks("nomatch@example.com"))

        assert result["total_hits"] == 0
        assert result["collections"] == []


# --- check_blacklist: local DB lookup, no HTTP at all ---------------------


class TestCheckBlacklist:
    @pytest.fixture
    def session_factory(self, make_session_factory):
        return make_session_factory([BlacklistedAddress.__table__])

    def test_returns_no_match_for_unlisted_address(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await external_api_clients.check_blacklist("0xabc123", db)

        result = _run(_scenario())
        assert result["matched"] is False
        assert result["sources"] == []

    def test_matches_active_blacklisted_address(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                db.add(
                    BlacklistedAddress(
                        address="0xabc123",
                        source=BlacklistSource.OFAC.value,
                        is_active=True,
                    )
                )
                await db.commit()
                return await external_api_clients.check_blacklist("0xabc123", db)

        result = _run(_scenario())
        assert result["matched"] is True
        assert result["sources"] == [BlacklistSource.OFAC.value]

    def test_ignores_inactive_blacklist_entries(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                db.add(
                    BlacklistedAddress(
                        address="0xabc123",
                        source=BlacklistSource.OFAC.value,
                        is_active=False,
                    )
                )
                await db.commit()
                return await external_api_clients.check_blacklist("0xabc123", db)

        result = _run(_scenario())
        assert result["matched"] is False

    def test_matches_opensanctions_terror_financing_address(self, session_factory):
        """A crypto address from OpenSanctions' il_mod_crypto source (not OFAC/ScamSniffer)."""

        async def _scenario():
            async with session_factory() as db:
                db.add(
                    BlacklistedAddress(
                        address="TWaertrZdpRJSbLv2G638UL5HCK6sKcZYy",
                        source=BlacklistSource.OPENSANCTIONS.value,
                        chain="USDT",
                        label="crime.terror",
                        entity_name="NOBITEX",
                        details={
                            "dataset": "il_mod_crypto",
                            "profile_url": "https://www.opensanctions.org/entities/il-nbctf-abc123/",
                        },
                        is_active=True,
                    )
                )
                await db.commit()
                return await external_api_clients.check_blacklist(
                    "TWaertrZdpRJSbLv2G638UL5HCK6sKcZYy",
                    db,
                )

        result = _run(_scenario())
        assert result["matched"] is True
        assert result["sources"] == [BlacklistSource.OPENSANCTIONS.value]
        assert result["ofac"] is None
        assert result["opensanctions"] == {
            "chain": "USDT",
            "topics": "crime.terror",
            "holder_name": "NOBITEX",
            "dataset": "il_mod_crypto",
            "profile_url": "https://www.opensanctions.org/entities/il-nbctf-abc123/",
        }

    def test_clean_address_has_no_opensanctions_match(self, session_factory):
        async def _scenario():
            async with session_factory() as db:
                return await external_api_clients.check_blacklist(
                    "TCleanAddressNotListed0000000", db
                )

        result = _run(_scenario())
        assert result["matched"] is False
        assert result["opensanctions"] is None
