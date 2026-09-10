# Pattern reference

Each pattern is intentionally visible in one focused module under `backend/app/patterns/` and is composed top-to-bottom by `backend/app/gateway.py`.

| ID | Module | Failure boundary |
| --- | --- | --- |
| `model-routing` | `routing.py` | deterministic decision, no model call |
| `provider-fallback` | `fallback.py` | only recognized provider availability failures |
| `retries` | `retries.py` | transient errors, three total attempts |
| `structured-output` | `structured_output.py` | one correction, then controlled upstream failure |
| `token-budgeting` | `token_budget.py` | protected input overflow is rejected |
| `response-caching` | `caching.py` | exact key, TTL, valid results only |
| `rate-limiting` | `rate_limiting.py` | per-client local token bucket |
| `prompt-injection` | `prompt_security.py` | high-risk input is blocked before cache/provider |
| `tracing` | `tracing.py` | ordered local spans with safe metadata |
| `deterministic-evaluation` | `evaluation/` | ten offline fixture assertions |

The frontend receives pattern descriptions from `/api/patterns` and provider descriptors from `/api/providers`; credentials and prompt contents are never returned by discovery endpoints.
