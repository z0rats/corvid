"""Structural gate + behaviour of `ProviderSpec.expects`: a keyless `ioc_lookup` provider whose
result lacks the fields the frontend reads is reported as "source changed its response format"
(`LookupStatus.ERROR`), not rendered as an empty card.

Every registered provider either declares `expects` (the top-level fields the UI's summary and
detail components read) or has an `EXEMPT` reason here. A new provider fails
`test_every_provider_declares_expects_or_is_exempt` until it does one of the two."""

import asyncio

import pytest

from app.core.external_sources.contract import SourceDriftError
from app.features.ioc_tools.ioc_lookup.schemas.lookup_schemas import LookupStatus
from app.features.ioc_tools.ioc_lookup.single_lookup.service import (
    external_api_clients,
    service_registry,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service import (
    ioc_lookup_engine as engine,
)
from app.features.ioc_tools.ioc_lookup.single_lookup.service.client_base import ServiceDriftError
from app.features.ioc_tools.ioc_lookup.single_lookup.service.provider_spec import (
    ProviderSpec,
    verify_expected_fields,
)

KEYED = "keyed, see 04-keyed-canaries"
CLIENT_SIDE = "result is built by the client, which validates the raw source itself"

EXEMPT = {
    "blacklist": "local DB, no external source",
    "cisakev": CLIENT_SIDE + " (_get_kev_catalog)",
    "libraryofleaks": CLIENT_SIDE + " (check_libraryofleaks)",
    "openphish": CLIENT_SIDE + " (_get_openphish_feed)",
    "hudsonrock": "shape differs per IOC type (stealers[] for email/ip, data{} for domain)",
}


@pytest.fixture(scope="module")
def providers() -> dict[str, ProviderSpec]:
    service_registry.register_services(external_api_clients)
    return service_registry.get_all_services()


def _exemptions(providers: dict[str, ProviderSpec]) -> dict[str, str]:
    """Reasoned exemptions: the explicit ones plus the blanket one for keyed providers."""
    keyed = {key: KEYED for key, spec in providers.items() if spec.api_key is not None}
    return {**keyed, **EXEMPT}


def test_every_provider_declares_expects_or_is_exempt(providers):
    exempt = _exemptions(providers)
    declared = {key for key, spec in providers.items() if spec.expects}

    missing = set(providers) - declared - set(exempt)
    assert not missing, f"declare `expects` (or add an EXEMPT reason) for: {sorted(missing)}"
    assert not declared & set(EXEMPT), "an EXEMPT provider also declares expects"
    assert set(EXEMPT) <= set(providers), "EXEMPT names a provider that no longer exists"
    assert all(exempt.values()), "an exemption needs a reason"


class TestVerifyExpectedFields:
    spec = ProviderSpec(
        func=None, name="Svc", supported_ioc_types=["ipv4"], expects=("score", "risk")
    )

    def test_a_complete_result_passes_even_with_null_values(self):
        verify_expected_fields(self.spec, {"score": None, "risk": "", "extra": 1})

    def test_a_missing_field_is_drift_naming_it(self):
        with pytest.raises(ServiceDriftError, match="Svc changed its response format.*risk"):
            verify_expected_fields(self.spec, {"score": 1})

    def test_a_non_object_result_is_drift(self):
        with pytest.raises(ServiceDriftError, match="not a JSON object"):
            verify_expected_fields(self.spec, ["score", "risk"])

    def test_without_expects_nothing_is_checked(self):
        verify_expected_fields(
            ProviderSpec(func=None, name="Svc", supported_ioc_types=["ipv4"]), {}
        )


async def _noop(*args, **kwargs):
    return None


class TestEngineReportsDriftAsAnError:
    def _lookup(self, monkeypatch, payload):
        async def func(ioc):
            return payload

        spec = ProviderSpec(func=func, name="Svc", supported_ioc_types=["ipv4"], expects=("score",))

        async def noop(*args, **kwargs):
            return None

        monkeypatch.setattr(engine, "_ensure_registry_initialized", noop)
        monkeypatch.setattr(engine, "apply_rate_limit", noop)
        monkeypatch.setattr(engine, "get_service", lambda name: spec)
        return asyncio.run(engine.lookup_ioc("svc", "1.2.3.4", "ipv4", db=None))

    def test_drifted_result_is_an_error_with_a_readable_message(self, monkeypatch):
        result = self._lookup(monkeypatch, {"renamed_score": 1})

        assert result.status == LookupStatus.ERROR
        assert result.data is None
        assert "changed its response format" in result.error

    def test_a_client_raised_drift_error_gets_the_same_message(self, monkeypatch):
        async def func(ioc):
            raise SourceDriftError("feed has no URL lines")

        spec = ProviderSpec(func=func, name="Svc", supported_ioc_types=["ipv4"])
        monkeypatch.setattr(engine, "get_service", lambda name: spec)
        monkeypatch.setattr(engine, "_ensure_registry_initialized", _noop)
        monkeypatch.setattr(engine, "apply_rate_limit", _noop)

        result = asyncio.run(engine.lookup_ioc("svc", "1.2.3.4", "ipv4", db=None))

        assert result.status == LookupStatus.ERROR
        assert result.error == "Svc changed its response format (feed has no URL lines)"

    def test_complete_result_is_a_success(self, monkeypatch):
        result = self._lookup(monkeypatch, {"score": 0})

        assert result.status == LookupStatus.SUCCESS
        assert result.data == {"score": 0}


# One realistic payload per `expects` provider; dropping any expected field must be drift.
SAMPLES = {
    "ffraud": {"fraud_score": 0, "risk": "none", "ip": "8.8.8.8"},
    "ffraudemail": {
        "is_disposable": False,
        "community_blacklisted": False,
        "valid_format": True,
        "safe_domain": True,
    },
    "firstepss": {"status": "OK", "data": []},
    "urlscanio": {"results": [], "total": 0},
}


def test_every_expects_provider_has_a_sample(providers):
    assert {key for key, spec in providers.items() if spec.expects} == set(SAMPLES)


@pytest.mark.parametrize("key", sorted(SAMPLES))
def test_each_expected_field_is_enforced(providers, key):
    spec = providers[key]
    verify_expected_fields(spec, SAMPLES[key])
    for field in spec.expects:
        dropped = {k: v for k, v in SAMPLES[key].items() if k != field}
        with pytest.raises(ServiceDriftError, match=field):
            verify_expected_fields(spec, dropped)
