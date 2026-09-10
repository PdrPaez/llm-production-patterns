# Specification validation

This audit compares `llm-production-patterns-master-spec.md` with the executable repository state. The specification is treated as project guidance; system and user instructions remain authoritative.

## Requirement matrix

| Specification area | Evidence in this repository | Status |
| --- | --- | --- |
| Offline-first startup and no mandatory API key | `README.md`, `backend/app/config.py`, mock providers, `backend/tests/test_patterns.py` | Verified |
| FastAPI service and typed playground contract | `backend/app/main.py`, `backend/app/schemas.py`, API integration tests | Verified |
| Provider protocol and deterministic mocks | `backend/app/providers/base.py`, `backend/app/providers/mock.py` | Verified |
| Model routing and fixed-route override | `backend/app/patterns/routing.py`, gateway trace metadata, tests | Verified |
| Bounded retries with exponential backoff | `backend/app/patterns/retries.py`, retry/fallback tests | Verified |
| Ordered provider fallback | `backend/app/patterns/fallback.py`, gateway tests | Verified |
| Structured validation and one correction | `backend/app/patterns/structured_output.py`, gateway tests | Verified |
| Priority-aware token budgeting and overflow | `backend/app/patterns/token_budget.py`, budget tests | Verified |
| SQLite cache and TTL | `backend/app/patterns/caching.py`, cache tests and API | Verified |
| Token-bucket rate limiting | `backend/app/patterns/rate_limiting.py`, 429 API test | Verified |
| Prompt security and operation allowlist | `backend/app/patterns/prompt_security.py`, security tests | Verified |
| Persisted tracing and trace retrieval | `backend/app/patterns/tracing.py`, `/api/traces/{trace_id}`, tests | Verified |
| Deterministic evaluation | `backend/app/evaluation/dataset.json`, `backend/app/evaluation/run.py`, 10/10 run | Verified |
| Provider discovery and safe metadata | `/api/providers`, `Gateway.descriptors()`, frontend API client | Verified |
| Optional real LLM transport, tier-aware model selection, and safe HTTP error classification | `backend/app/providers/openai_compatible.py`, `backend/app/config.py`, `.env.example`, transport tests | Verified |
| React/XYFlow execution visualization | `frontend/src/main.tsx`, `frontend/src/flow/execution/mapExecution.ts` | Verified |
| Retry, fallback, cache, security and correction visual states | `mapExecution.ts`, `mapExecution.test.ts`, browser smoke scenarios | Verified |
| Timeline, inspector and replay | `frontend/src/main.tsx`, `frontend/src/timeline.css`, browser smoke scenarios | Verified |
| Architecture, lifecycle, pattern and release documentation | `README.md`, `docs/`, `ROADMAP.md`, CI workflow | Verified |
| Clean Git/release policy | `git log`, `CONTRIBUTING.md`, `origin/dev`, `origin/main` | Verified |

## Validation commands

```text
cd backend
python -m ruff check .
python -m pytest -q
python -m app.evaluation.run

cd ../frontend
npm ci
npm run test
npm run lint
npm run build
```

The default path remains offline. The real provider path is opt-in and never exposes the API key through `/api/providers` or playground responses.

## Real provider setup

Copy `.env.example` to `.env`, set `LLM_PROVIDER_MODE=openai_compatible`, provide `OPENAI_API_KEY`, and optionally change `OPENAI_BASE_URL` for another OpenAI-compatible service. Set `OPENAI_MODEL` or the tier-specific model variables for deployment-specific routing. Start the backend and choose one of the discovered OpenAI-compatible Fast/Quality providers in a fixed flow, or use automatic routing while the provider mode is enabled.
