"""Small optional OpenAI-compatible transport; never required by the default mock mode."""

import time
from typing import Any

from ..config import get_settings
from ..schemas import ProviderRequest, ProviderResponse
from .base import ProviderConfigurationError, ProviderUnavailableError, TransientProviderError


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self, *, provider_name: str | None = None, base_url: str | None = None, api_key: str | None = None, model: str | None = None, transport: Any = None):
        settings = get_settings()
        self.base_url = (base_url if base_url is not None else settings.openai_base_url).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.model = model or settings.openai_model or "configured-model"
        self.transport = transport
        if provider_name:
            self.name = provider_name

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.base_url or not self.api_key:
            raise ProviderConfigurationError("OpenAI-compatible provider is not configured")
        try:
            import httpx
        except ImportError as exc:
            raise ProviderConfigurationError("Install the optional HTTP client to use this provider") from exc
        started = time.perf_counter()
        messages = []
        if request.system_instructions:
            messages.append({"role": "system", "content": request.system_instructions})
        messages.extend({"role": "user", "content": block} for block in request.retained_context_blocks)
        messages.append({"role": "user", "content": request.user_content})
        payload = {"model": self.model, "messages": messages, "temperature": request.temperature, "max_tokens": request.max_output_tokens}
        if request.structured_output:
            payload["response_format"] = {"type": "json_object"}
        try:
            async with httpx.AsyncClient(timeout=30, transport=self.transport) as client:
                response = await client.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload)
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            raise TransientProviderError(f"OpenAI-compatible transport failed: {exc}") from exc
        if response.status_code in {408, 409, 429} or response.status_code >= 500:
            raise TransientProviderError(f"OpenAI-compatible service returned HTTP {response.status_code}")
        if response.status_code in {401, 403, 404}:
            raise ProviderConfigurationError(f"OpenAI-compatible service returned HTTP {response.status_code}")
        if response.status_code >= 400:
            raise ProviderUnavailableError(f"OpenAI-compatible service returned HTTP {response.status_code}")
        try:
            text = response.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderUnavailableError("OpenAI-compatible response did not contain message content") from exc
        return ProviderResponse(text=text, provider=self.name, model=self.model, input_tokens=max(1, len(request.user_content) // 4), output_tokens=max(1, len(text) // 4), latency_ms=(time.perf_counter() - started) * 1000)
