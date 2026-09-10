"""Small optional OpenAI-compatible transport; never required by the default mock mode."""

import time

from ..config import get_settings
from ..schemas import ProviderRequest, ProviderResponse
from .base import ProviderConfigurationError


class OpenAICompatibleProvider:
    name = "openai_compatible"

    def __init__(self):
        settings = get_settings()
        self.base_url = settings.openai_base_url.rstrip("/")
        self.api_key = settings.openai_api_key
        self.model = settings.openai_model or "configured-model"

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        if not self.base_url or not self.api_key:
            raise ProviderConfigurationError("OpenAI-compatible provider is not configured")
        try:
            import httpx
        except ImportError as exc:
            raise ProviderConfigurationError("Install the optional HTTP client to use this provider") from exc
        started = time.perf_counter()
        payload = {"model": self.model, "messages": [{"role": "user", "content": request.user_content}], "temperature": request.temperature, "max_tokens": request.max_output_tokens}
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {self.api_key}"}, json=payload)
            response.raise_for_status()
            text = response.json()["choices"][0]["message"]["content"]
        return ProviderResponse(text=text, provider=self.name, model=self.model, input_tokens=max(1, len(request.user_content) // 4), output_tokens=max(1, len(text) // 4), latency_ms=(time.perf_counter() - started) * 1000)
