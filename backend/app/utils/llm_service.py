import logging
import time as _time
from typing import TypeVar

import httpx
from pydantic import BaseModel
from pydantic_ai import Agent, BinaryContent
from pydantic_ai.settings import ModelSettings
from pydantic_ai.models.openai import OpenAIChatModel, OpenAIResponsesModel, OpenAIResponsesModelSettings
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.providers.anthropic import AnthropicProvider
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config.settings import settings as app_settings
from app.core.settings.api_keys.crud.api_keys_settings_crud import get_apikey

logger = logging.getLogger(__name__)


MODEL_DEFINITIONS: dict[str, tuple[str, str, str]] = {
    "gpt-5": ("openai", "gpt-5", "GPT-5"),
    "gpt-4o": ("openai", "gpt-4o", "GPT-4o"),
    "claude-opus-4-6": ("anthropic", "claude-opus-4-6", "Claude Opus 4.6"),
    "claude-sonnet-4-6": ("anthropic", "claude-sonnet-4-6", "Claude Sonnet 4.6"),
    "claude-sonnet-4-5": ("anthropic", "claude-sonnet-4-5-20250514", "Claude Sonnet 4.5"),
    "claude-haiku-4-5": ("anthropic", "claude-haiku-4-5-20251001", "Claude Haiku 4.5"),
}

PROVIDER_DISPLAY_NAMES: dict[str, str] = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "google": "Google",
}

_PROVIDER_KEY_NAMES: dict[str, str] = {
    "openai": "openai",
    "anthropic": "anthropic",
    "google": "gemini",
}

_REASONING_MODEL_PREFIXES = ("o1", "o3", "o4", "gpt-5")

OLLAMA_MODEL_ID_PREFIX = "ollama:"
OLLAMA_PROVIDER_DISPLAY_NAME = "Ollama (local)"
_OLLAMA_DISCOVERY_TIMEOUT_SECONDS = 1.5


def _is_reasoning_model(model_id: str) -> bool:
    """Check if a model is a reasoning model that doesn't support temperature"""
    return any(model_id.startswith(p) for p in _REASONING_MODEL_PREFIXES)


def _create_model(provider: str, model_name: str, api_key: str):
    """Create a PydanticAI model instance for the given provider"""
    if provider == "openai":
        openai_provider = OpenAIProvider(api_key=api_key)
        if _is_reasoning_model(model_name):
            return OpenAIResponsesModel(model_name, provider=openai_provider)
        return OpenAIChatModel(model_name, provider=openai_provider)
    if provider == "anthropic":
        return AnthropicModel(model_name, provider=AnthropicProvider(api_key=api_key))
    if provider == "google":
        return GoogleModel(model_name, provider=GoogleProvider(api_key=api_key))
    raise ValueError(f"Unknown provider: {provider}")


async def _discover_ollama_models() -> dict:
    """Auto-discover models pulled into a local Ollama server, via its OpenAI-compatible
    /v1/models endpoint. No API key needed - Ollama ignores it, the client just requires
    a non-empty string. Returns {} (rather than raising) if Ollama isn't reachable, so a
    user without it running still gets the cloud-provider models unaffected.
    """
    base_url = app_settings.llm.ollama_base_url
    try:
        async with httpx.AsyncClient(timeout=_OLLAMA_DISCOVERY_TIMEOUT_SECONDS) as client:
            response = await client.get(f"{base_url}/models")
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.debug("Ollama not reachable at %s, skipping local models: %s", base_url, e)
        return {}

    provider = OpenAIProvider(base_url=base_url, api_key="ollama")
    models: dict = {}
    for entry in data.get("data", []):
        model_name = entry.get("id")
        if not model_name:
            continue
        models[f"{OLLAMA_MODEL_ID_PREFIX}{model_name}"] = OpenAIChatModel(model_name, provider=provider)

    logger.info("Discovered %d local Ollama model(s) at %s", len(models), base_url)
    return models


async def _build_model_registry(db: AsyncSession) -> dict:
    """Build a registry of available LLM models from database API keys, plus any
    locally-available Ollama models (no key required for those)."""
    models: dict = {}

    api_keys: dict[str, str | None] = {}
    for provider, key_name in _PROVIDER_KEY_NAMES.items():
        key_obj = await get_apikey(name=key_name, db=db)
        api_keys[provider] = key_obj.key if key_obj else None
        logger.info("%s API key available: %s", provider.capitalize(), bool(api_keys[provider]))

    for display_id, (provider, model_name, _) in MODEL_DEFINITIONS.items():
        api_key = api_keys.get(provider)
        if api_key:
            models[display_id] = _create_model(provider, model_name, api_key)

    models.update(await _discover_ollama_models())

    return models


def _build_model_settings(
    model,
    model_id: str,
    temperature: float | None,
    max_tokens: int | None,
) -> ModelSettings | None:
    """Build appropriate model settings based on model type"""
    if isinstance(model, OpenAIResponsesModel):
        kwargs: dict = {}
        if _is_reasoning_model(model_id):
            kwargs["openai_reasoning_effort"] = "low"
        else:
            if max_tokens is not None:
                kwargs["max_tokens"] = max_tokens
            if temperature is not None:
                kwargs["temperature"] = temperature
        return OpenAIResponsesModelSettings(**kwargs) if kwargs else None

    kwargs = {}
    if temperature is not None and not _is_reasoning_model(model_id):
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    return ModelSettings(**kwargs) if kwargs else None


async def execute_prompt(
    models: dict,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """Execute a prompt using the specified model from the registry"""
    if model_id not in models:
        raise ValueError(f"Model '{model_id}' not registered")

    model = models[model_id]
    settings = _build_model_settings(model, model_id, temperature, max_tokens)
    agent = Agent(model, instructions=system_prompt)

    try:
        result = await agent.run(user_prompt, model_settings=settings)

        content = result.output
        if not content:
            raise ValueError(f"[execute_prompt] Model '{model_id}' returned an empty response")

        return content
    except ValueError:
        raise
    except Exception as e:
        logger.error("Error executing prompt with model '%s': %s", model_id, e)
        raise ValueError(f"Failed to execute prompt with model '{model_id}': {e}")


T = TypeVar("T", bound=BaseModel)


async def execute_structured_prompt(
    models: dict,
    model_id: str,
    system_prompt: str,
    user_prompt: str,
    output_type: type[T],
    temperature: float | None = None,
    max_tokens: int | None = None,
    image_data: bytes | None = None,
    image_media_type: str = "image/jpeg",
) -> T:
    """Execute a prompt and return a validated Pydantic model instance.

    Uses pydantic-ai's output_type to get structured output with automatic
    validation and retry on validation failures. Pass image_data for a
    multimodal (vision) request - not every model/provider supports it.
    """
    if model_id not in models:
        raise ValueError(f"Model '{model_id}' not registered")

    model = models[model_id]
    settings = _build_model_settings(model, model_id, temperature, max_tokens)
    agent = Agent(model, instructions=system_prompt, output_type=output_type)

    user_input = user_prompt
    if image_data is not None:
        user_input = [user_prompt, BinaryContent(data=image_data, media_type=image_media_type)]

    try:
        result = await agent.run(user_input, model_settings=settings)
        return result.output
    except Exception as e:
        logger.error("Error executing structured prompt with model '%s': %s (type: %s)", model_id, e, type(e).__name__)
        raise ValueError(f"Failed to execute structured prompt with model '{model_id}': {e}")


_registry_cache: dict | None = None
_registry_cache_timestamp: float = 0.0
_REGISTRY_CACHE_TTL: float = 300.0


async def build_model_registry(db: AsyncSession) -> dict:
    """Build a registry of available LLM models, cached for 5 minutes"""
    global _registry_cache, _registry_cache_timestamp

    now = _time.monotonic()
    if _registry_cache is not None and (now - _registry_cache_timestamp) < _REGISTRY_CACHE_TTL:
        return _registry_cache

    registry = await _build_model_registry(db)
    _registry_cache = registry
    _registry_cache_timestamp = now
    return registry


def invalidate_model_registry_cache() -> None:
    """Clear the model registry cache (call when API keys change)"""
    global _registry_cache, _registry_cache_timestamp
    _registry_cache = None
    _registry_cache_timestamp = 0.0


async def get_available_models(db: AsyncSession) -> list[dict[str, str]]:
    """Get list of available models with display info, filtered by configured API keys
    (plus any locally-discovered Ollama models, which aren't in MODEL_DEFINITIONS - their
    display name/provider are derived from the model id itself)."""
    registry = await build_model_registry(db)
    available = []
    for model_id in registry:
        if model_id.startswith(OLLAMA_MODEL_ID_PREFIX):
            available.append({
                "id": model_id,
                "name": model_id.removeprefix(OLLAMA_MODEL_ID_PREFIX),
                "provider": OLLAMA_PROVIDER_DISPLAY_NAME,
            })
            continue
        provider, _, display_name = MODEL_DEFINITIONS[model_id]
        available.append({
            "id": model_id,
            "name": display_name,
            "provider": PROVIDER_DISPLAY_NAMES.get(provider, provider),
        })
    return available


async def get_default_model_id(db: AsyncSession, module_key: str | None = None) -> str:
    """Resolve the default model ID for a given module.

    Resolution order: per-module override > global default > first available model.
    """
    from app.core.settings.ai_settings.crud.ai_settings_crud import get_ai_settings

    registry = await build_model_registry(db)
    if not registry:
        raise ValueError("No LLM models available (no API keys configured)")

    ai_settings = await get_ai_settings(db)

    if ai_settings and module_key:
        module_field = f"{module_key}_model"
        module_model = getattr(ai_settings, module_field, None)
        if module_model and module_model in registry:
            return module_model

    if ai_settings and ai_settings.default_model and ai_settings.default_model in registry:
        return ai_settings.default_model

    return next(iter(registry))
