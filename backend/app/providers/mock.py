import asyncio
import time

from ..schemas import ProviderRequest, ProviderResponse
from .base import ProviderUnavailableError, TransientProviderError


def _tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _ticket_json(prompt: str, rich: bool, invalid: bool) -> str:
    if invalid:
        return '{"category":"unknown","priority":"urgent"}'
    lower = prompt.lower()
    category = "billing" if any(x in lower for x in ("charged", "payment", "billing")) else "account" if any(x in lower for x in ("login", "password", "account")) else "technical" if any(x in lower for x in ("error", "crash", "bug")) else "other"
    priority = "high" if any(x in lower for x in ("urgent", "blocking", "twice")) else "medium" if len(prompt) > 40 else "low"
    human = priority == "high" or category in {"billing", "account"}
    summary = f"Classified as {category} with {priority} priority."
    if rich:
        summary += " The request should be reviewed using the explicit structured contract."
    return f'{{"category":"{category}","priority":"{priority}","summary":"{summary}","requires_human":{str(human).lower()}}}'


class MockFastProvider:
    name = "mock_fast"
    model = "mock-fast-v1"

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        started = time.perf_counter()
        await asyncio.sleep(0.008)
        if request.failure_mode == "unavailable":
            raise ProviderUnavailableError("mock_fast unavailable")
        if request.failure_mode == "transient_once" and request.failure_attempts == 0:
            request.failure_attempts += 1
            raise TransientProviderError("temporary mock_fast overload")
        text = _ticket_json(request.user_content, False, request.simulate_invalid_output and not request.correction) if request.structured_output else f"Fast answer: {request.user_content[:240]}"
        return ProviderResponse(text=text, provider=self.name, model=self.model, input_tokens=_tokens(request.user_content), output_tokens=_tokens(text), latency_ms=(time.perf_counter() - started) * 1000)


class MockQualityProvider:
    name = "mock_quality"
    model = "mock-quality-v1"

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        started = time.perf_counter()
        await asyncio.sleep(0.02)
        text = _ticket_json(request.user_content, True, request.simulate_invalid_output and not request.correction) if request.structured_output else f"Quality answer: {request.user_content[:240]}\n\nProduction consideration: keep behavior explicit, bounded, and observable."
        return ProviderResponse(text=text, provider=self.name, model=self.model, input_tokens=_tokens(request.user_content), output_tokens=_tokens(text), latency_ms=(time.perf_counter() - started) * 1000)


class MockFailingProvider:
    name = "mock_failing"
    model = "mock-failing-v1"

    async def generate(self, request: ProviderRequest) -> ProviderResponse:
        started = time.perf_counter()
        await asyncio.sleep(0.008)
        if request.failure_mode in {"transient_once", "exhaust_primary", "unavailable"}:
            if request.failure_mode == "unavailable":
                raise ProviderUnavailableError("mock_failing unavailable")
            raise TransientProviderError("deterministic simulated provider failure")
        text = f"Failing provider answer: {request.user_content[:240]}"
        return ProviderResponse(text=text, provider=self.name, model=self.model, input_tokens=_tokens(request.user_content), output_tokens=_tokens(text), latency_ms=(time.perf_counter() - started) * 1000)
