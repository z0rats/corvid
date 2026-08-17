import asyncio
import types

import httpx
import pytest

from app.utils import llm_service


def _run(coro):
    return asyncio.run(coro)


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=None, response=self)

    def json(self):
        return self._json_data


class _FakeAsyncClient:
    """Stands in for httpx.AsyncClient as an async context manager, since the
    repo has no respx/pytest-httpx dependency to fake the transport with."""

    def __init__(self, response=None, exc=None):
        self._response = response
        self._exc = exc

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def get(self, url):
        if self._exc:
            raise self._exc
        return self._response


def _patch_discovery_client(monkeypatch, **client_kwargs):
    """Rebinds the `httpx` name *inside llm_service's own namespace* to a fake with
    just an AsyncClient factory - patching the real httpx module directly would also
    swap AsyncClient out from under pydantic-ai/openai's own internals (OpenAIProvider
    builds its own httpx.AsyncClient when none is passed in), breaking unrelated code."""
    fake_httpx = types.SimpleNamespace(
        AsyncClient=lambda **kwargs: _FakeAsyncClient(**client_kwargs)
    )
    monkeypatch.setattr(llm_service, "httpx", fake_httpx)


class TestDiscoverOllamaModels:
    def test_returns_empty_dict_when_ollama_unreachable(self, monkeypatch):
        _patch_discovery_client(monkeypatch, exc=httpx.ConnectError("connection refused"))

        result = _run(llm_service._discover_ollama_models())

        assert result == {}

    def test_registers_each_discovered_model_under_the_ollama_prefix(self, monkeypatch):
        response = _FakeResponse({"data": [{"id": "qwen2.5vl:7b"}, {"id": "llava:latest"}]})
        _patch_discovery_client(monkeypatch, response=response)

        result = _run(llm_service._discover_ollama_models())

        assert set(result.keys()) == {"ollama:qwen2.5vl:7b", "ollama:llava:latest"}

    def test_skips_entries_without_an_id_field(self, monkeypatch):
        response = _FakeResponse({"data": [{"id": "llava:latest"}, {"name": "no id field"}]})
        _patch_discovery_client(monkeypatch, response=response)

        result = _run(llm_service._discover_ollama_models())

        assert list(result.keys()) == ["ollama:llava:latest"]

    def test_returns_empty_dict_on_a_non_2xx_response(self, monkeypatch):
        response = _FakeResponse({}, status_code=500)
        _patch_discovery_client(monkeypatch, response=response)

        result = _run(llm_service._discover_ollama_models())

        assert result == {}


class TestGetAvailableModels:
    @pytest.fixture(autouse=True)
    def stub_registry(self, monkeypatch):
        async def fake_build_model_registry(db):
            return {
                "gpt-4o": object(),
                "ollama:llava:latest": object(),
            }

        monkeypatch.setattr(llm_service, "build_model_registry", fake_build_model_registry)

    def test_derives_name_and_provider_for_ollama_models_from_the_id(self):
        available = _run(llm_service.get_available_models(db=None))

        ollama_entry = next(m for m in available if m["id"] == "ollama:llava:latest")
        assert ollama_entry["name"] == "llava:latest"
        assert ollama_entry["provider"] == "Ollama (local)"

    def test_still_resolves_cloud_models_from_model_definitions(self):
        available = _run(llm_service.get_available_models(db=None))

        cloud_entry = next(m for m in available if m["id"] == "gpt-4o")
        assert cloud_entry["name"] == "GPT-4o"
        assert cloud_entry["provider"] == "OpenAI"
