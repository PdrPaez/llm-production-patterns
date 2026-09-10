import asyncio
import json

import httpx

from app.config import get_settings
from app.gateway import Gateway
from app.providers.base import TransientProviderError
from app.providers.openai_compatible import OpenAICompatibleProvider
from app.schemas import ProviderRequest


def run(coro):
    return asyncio.run(coro)


def test_openai_compatible_provider_sends_context_and_structured_contract():
    captured = {}

    def handler(request: httpx.Request):
        captured.update(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"ok": true}'}}]})

    provider = OpenAICompatibleProvider(base_url="https://llm.test/v1", api_key="secret", model="test-model", transport=httpx.MockTransport(handler))
    response = run(provider.generate(ProviderRequest(user_content="Classify this", system_instructions="Be precise", retained_context_blocks=["Prior context"], structured_output=True)))

    assert response.provider == "openai_compatible"
    assert response.model == "test-model"
    assert captured["model"] == "test-model"
    assert captured["messages"][-1]["content"] == "Classify this"
    assert captured["response_format"] == {"type": "json_object"}


def test_openai_compatible_provider_maps_transient_http_errors():
    transport = httpx.MockTransport(lambda request: httpx.Response(429, json={"error": "busy"}))
    provider = OpenAICompatibleProvider(base_url="https://llm.test/v1", api_key="secret", transport=transport)

    try:
        run(provider.generate(ProviderRequest(user_content="retry me")))
    except TransientProviderError as error:
        assert "429" in str(error)
    else:
        raise AssertionError("expected transient provider error")


def test_gateway_discovers_real_tier_providers_without_exposing_credentials(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER_MODE", "openai_compatible")
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    get_settings.cache_clear()
    try:
        descriptors = Gateway().descriptors()
        external = {item["id"]: item for item in descriptors if item["type"] == "external"}
        assert external["openai_fast"]["available"] is True
        assert external["openai_quality"]["available"] is True
        assert all("key" not in item and "secret" not in item for item in descriptors)
    finally:
        get_settings.cache_clear()
