import time

from pydantic import ValidationError

from .config import get_settings
from .database import get_session, init_db
from .patterns.caching import cache_key, cache_stats, clear_cache, get_cached, put_cached
from .patterns.fallback import ordered_plan
from .patterns.prompt_security import inspect_prompt
from .patterns.rate_limiting import TokenBucketLimiter
from .patterns.retries import with_retries
from .patterns.routing import ModelRouter
from .patterns.structured_output import parse_ticket, validation_errors
from .patterns.token_budget import apply_budget
from .patterns.tracing import Trace
from .providers.base import (
    ProviderConfigurationError,
    ProviderUnavailableError,
    TransientProviderError,
)
from .providers.mock import MockFailingProvider, MockFastProvider, MockQualityProvider
from .providers.openai_compatible import OpenAICompatibleProvider
from .schemas import PlaygroundRequest, PlaygroundResponse, ProviderRequest


class Gateway:
    def __init__(self):
        init_db()
        self.settings = get_settings()
        self.router = ModelRouter()
        self.limiter = TokenBucketLimiter(self.settings.rate_limit_capacity, self.settings.rate_limit_refill_per_second)
        self.providers = {p.name: p for p in (MockFastProvider(), MockQualityProvider(), MockFailingProvider())}
        if self.settings.llm_provider_mode == "openai_compatible" and self.settings.openai_api_key:
            self.providers["openai_fast"] = OpenAICompatibleProvider(provider_name="openai_fast", model=self.settings.openai_fast_model or self.settings.openai_model)
            self.providers["openai_quality"] = OpenAICompatibleProvider(provider_name="openai_quality", model=self.settings.openai_quality_model or self.settings.openai_model)

    def descriptors(self):
        external = bool(self.settings.llm_provider_mode == "openai_compatible" and self.settings.openai_api_key)
        return [{"id": "mock_fast", "label": "Mock Fast", "tier": "fast", "type": "mock", "available": True}, {"id": "mock_quality", "label": "Mock Quality", "tier": "quality", "type": "mock", "available": True}, {"id": "mock_failing", "label": "Mock Failing", "tier": "failure", "type": "mock", "available": True}, {"id": "openai_fast", "label": "OpenAI-Compatible Fast", "tier": "fast", "type": "external", "available": external}, {"id": "openai_quality", "label": "OpenAI-Compatible Quality", "tier": "quality", "type": "external", "available": external}]

    async def run(self, req: PlaygroundRequest) -> PlaygroundResponse:
        started = time.perf_counter(); trace = Trace(); session = get_session()
        route = self.router.choose(prompt=req.prompt, complexity=req.complexity, structured_output=req.structured_output)
        if req.routing_mode == "fixed" and req.provider:
            selected = req.provider
        elif self.settings.llm_provider_mode == "openai_compatible":
            selected = "openai_quality" if route.provider == "mock_quality" else "openai_fast"
        else:
            selected = route.provider
        reason = "routing_overridden" if req.routing_mode == "fixed" else route.reason
        trace.span("request", "succeeded")
        rate = self.limiter.consume(req.client_id) if req.enable_rate_limit else {"allowed": True, "remaining": None, "retry_after": 0}
        trace.span("rate_limit", "succeeded" if rate["allowed"] else "blocked", rate)
        if not rate["allowed"]:
            response = PlaygroundResponse(trace_id=trace.trace_id, rate_limit=rate, execution={"status": "rate_limited", "route": ["rate_limit"]})
            trace.persist(session, response.model_dump()); return response
        security = inspect_prompt(req.prompt, req.requested_operation) if req.enable_security_check else type("S", (), {"allowed": True, "risk": "disabled", "findings": []})()
        trace.span("security", "succeeded" if security.allowed else "blocked", {"risk": security.risk, "findings": security.findings})
        if not security.allowed:
            response = PlaygroundResponse(trace_id=trace.trace_id, security=security.as_dict() if hasattr(security, "as_dict") else {"allowed": False, "risk_level": security.risk, "reasons": security.findings, "flagged_patterns": security.findings}, routing_reason=reason, selected_provider=selected, execution={"status": "blocked", "route": ["rate_limit", "security"], "skipped_stages": ["routing", "provider", "validation"]})
            trace.persist(session, response.model_dump()); return response
        trace.span("routing", "succeeded", {"selected_provider": selected, "reason": reason, "signals": route.signals})
        budget = apply_budget("", req.prompt, req.context_blocks, req.max_context_tokens, req.reserved_output_tokens)
        budget_json = budget.as_dict(req.max_context_tokens)
        trace.span("token_budget", "succeeded", budget_json)
        provider_request = ProviderRequest(user_content=req.prompt, retained_context_blocks=budget.retained_context, structured_output=req.structured_output, max_output_tokens=req.reserved_output_tokens, temperature=req.temperature, failure_mode=req.failure_mode, simulate_invalid_output=req.simulate_invalid_output, request_id=trace.trace_id)
        key = cache_key({"prompt": req.prompt, "structured": req.structured_output, "failure": req.failure_mode, "temperature": req.temperature}, selected)
        if req.enable_cache:
            cached = get_cached(session, key, self.settings.cache_ttl_seconds)
            trace.span("cache_lookup", "cache_hit" if cached else "miss", {"key": key})
            if cached:
                cached["trace_id"] = trace.trace_id; cached["cache_hit"] = True; cached["attempts"] = 0; cached["trace"] = [s.model_dump() for s in trace.spans]; trace.persist(session, cached); return PlaygroundResponse.model_validate(cached)
        else: trace.span("cache_lookup", "skipped")
        fallback = req.fallback_provider or ({"mock_fast": "mock_quality", "mock_quality": "mock_fast", "openai_fast": "openai_quality", "openai_quality": "openai_fast"}.get(selected, "mock_fast"))
        primary = "mock_failing" if req.failure_mode == "exhaust_primary" and selected.startswith("mock_") else selected
        plan = ordered_plan(primary, fallback, self.providers)
        attempted, attempts, retries, fallback_used, provider_response, errors = [], 0, 0, False, None, []
        for index, provider_id in enumerate(plan):
            if provider_id not in self.providers: raise ProviderConfigurationError(f"unknown provider: {provider_id}")
            attempted.append(provider_id)
            try:
                provider_response, performed, backoffs = await with_retries(lambda: self.providers[provider_id].generate(provider_request))
                attempts += performed; retries += performed - 1
                if performed > 1:
                    trace.span("retry", "succeeded", {"provider": provider_id, "attempts": performed, "backoffs_ms": backoffs})
                trace.span("provider_call", "succeeded", {"provider": provider_id, "attempts": performed, "backoffs_ms": backoffs})
                break
            except (TransientProviderError, ProviderUnavailableError) as exc:
                attempts += self.settings.provider_max_attempts if isinstance(exc, TransientProviderError) else 1; retries += max(0, attempts - len(attempted))
                errors.append({"provider": provider_id, "error": str(exc), "type": exc.__class__.__name__}); trace.span("provider_call", "failed", {"provider": provider_id, "error": str(exc)})
                if index == len(plan) - 1: raise
                fallback_used = True; trace.span("fallback", "succeeded", {"from": provider_id, "to": plan[index + 1]})
        structured = None
        if req.structured_output:
            try: structured = parse_ticket(provider_response.text); trace.span("validation", "succeeded")
            except ValidationError as first_error:
                trace.span("validation", "failed", {"errors": validation_errors(first_error)}); provider_request.correction = True
                corrected = await self.providers[provider_response.provider].generate(provider_request); attempts += 1
                try: structured = parse_ticket(corrected.text); provider_response = corrected; trace.span("correction", "succeeded"); trace.span("validation", "succeeded")
                except ValidationError as final_error: trace.span("correction", "failed", {"errors": validation_errors(final_error)}); raise ValueError("structured validation exhausted") from final_error
        trace.span("completion", "succeeded", {"provider": provider_response.provider})
        if req.enable_cache:
            trace.span("cache_store", "succeeded", {"key": key})
        result = PlaygroundResponse(response=None if structured else provider_response.text, structured_response=structured, selected_provider=selected, provider=provider_response.provider, routing_reason=reason, attempted_providers=attempted, attempts=attempts, retry_count=retries, fallback_used=fallback_used, security=security.as_dict() if hasattr(security, "as_dict") else {"allowed": True, "risk_level": security.risk, "reasons": security.findings, "flagged_patterns": security.findings}, rate_limit=rate, token_budget=budget_json, trace_id=trace.trace_id, latency_ms=(time.perf_counter()-started)*1000, execution={"status": "succeeded", "route": [s.name for s in trace.spans], "skipped_stages": ["correction"] if not req.structured_output else []}, trace=trace.spans)
        payload = result.model_dump()
        if req.enable_cache:
            put_cached(session, key, payload)
        trace.persist(session, payload); return result

    def stats(self):
        session = get_session(); data = cache_stats(session); session.close(); return data

    def clear(self):
        session = get_session(); count = clear_cache(session); session.close(); return {"cleared": count}
