import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware

from .database import get_session, init_db, trace_by_id
from .gateway import Gateway
from .patterns.token_budget import TokenBudgetExceededError
from .schemas import PlaygroundRequest, ProviderConfigurationRequest


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    yield


app = FastAPI(title="LLM Production Patterns", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
gateway = Gateway()


@app.get("/health")
def health(): return {"status": "ok", "sqlite": "configured", "provider_mode": "openai_compatible" if gateway.external_enabled else gateway.settings.llm_provider_mode}


@app.get("/api/patterns")
def patterns():
    items = [("model-routing", "Model Routing", "Choose an appropriate tier", "Deterministic signals select fast or quality", "patterns/routing.py", "Quality can cost more", "Use capability and cost signals in production"), ("provider-fallback", "Provider Fallback", "Recover from provider failure", "Ordered recognized-error fallback", "gateway.py", "Fallback can change quality/cost", "Keep transitions observable"), ("retries", "Retries with Exponential Backoff", "Handle transient errors", "Bounded 3-attempt retry controller", "patterns/retries.py", "Retries add latency", "Never retry programming errors"), ("structured-output", "Structured Output Validation", "Make model output typed", "Pydantic validation plus one correction", "patterns/structured_output.py", "Correction costs a call", "Reject exhausted upstream output"), ("token-budgeting", "Token Budgeting", "Fit context safely", "Protected input and priority-aware context budget", "patterns/token_budget.py", "Approximation differs from provider count", "Use provider tokenizer when available"), ("response-caching", "Response Caching", "Avoid repeated work", "Exact SQLite cache with TTL", "patterns/caching.py", "Not distributed or semantic", "Include model-affecting settings in key"), ("rate-limiting", "Rate Limiting", "Bound request volume", "In-memory token bucket per client", "patterns/rate_limiting.py", "Single process", "Use distributed limiter at scale"), ("prompt-injection", "Prompt Injection Mitigation", "Reduce unsafe instructions", "Heuristic detection and operation allowlist", "patterns/prompt_security.py", "Heuristics are incomplete", "Layer with stronger controls"), ("tracing", "Tracing", "Explain execution", "Persisted spans power diagnostics", "patterns/tracing.py", "Local, not distributed", "Adopt OpenTelemetry in production"), ("deterministic-evaluation", "Deterministic Evaluation", "Catch regressions offline", "Fixture-driven assertions without LLM judge", "evaluation/run.py", "Does not measure model quality", "Add curated datasets")]
    return [{"id": i, "title": t, "problem": p, "pattern": pat, "implementation": impl, "trade_offs": tr, "production_considerations": pc} for i,t,p,pat,impl,tr,pc in items]


@app.get("/api/providers")
def providers(): return gateway.descriptors()


@app.post("/api/providers/configure")
def configure_provider(request: ProviderConfigurationRequest):
    return gateway.configure_provider(request)


@app.post("/api/playground/run")
async def run_playground(request: PlaygroundRequest, response: Response, x_client_id: str | None = Header(default=None)):
    if x_client_id:
        request.client_id = x_client_id
    if len(request.client_id) > 64 or not request.client_id.strip():
        raise HTTPException(400, "X-Client-ID must contain 1 to 64 characters")
    try: result = await gateway.run(request)
    except TokenBudgetExceededError as exc: raise HTTPException(413, str(exc)) from exc
    except ValueError as exc: raise HTTPException(502, str(exc)) from exc
    if not result.rate_limit.get("allowed", True): response.status_code = 429; response.headers["Retry-After"] = str(result.rate_limit.get("retry_after", 1))
    return result


@app.get("/api/traces/{trace_id}")
def trace(trace_id: str):
    session = get_session(); record = trace_by_id(session, trace_id); session.close()
    if not record: raise HTTPException(404, "trace not found")
    return json.loads(record.response_json)


@app.post("/api/evaluation/run")
async def evaluation():
    from .evaluation.run import run_evaluation
    return await run_evaluation(gateway)


@app.get("/api/cache/stats")
def cache_stats(): return gateway.stats()


@app.delete("/api/cache")
def cache_clear(): return gateway.clear()
