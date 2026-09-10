# LLM Production Patterns

An offline-first, executable visual lab for ten production-oriented LLM integration patterns. It uses deterministic mock providers, FastAPI, SQLite, React, TypeScript, Vite, and `@xyflow/react`; no API key or external service is required.

## Patterns

| Pattern | Demonstration |
|---|---|
| Model routing | deterministic complexity, structure, and token signals |
| Provider fallback | ordered fallback for recognized provider failures |
| Retries | three total attempts with exponential backoff |
| Structured output | Pydantic validation and one correction cycle |
| Token budgeting | protected prompt plus bounded context |
| Response caching | exact SQLite key with TTL |
| Rate limiting | per-client in-memory token bucket |
| Prompt security | heuristic injection detection and operation allowlist |
| Tracing | persisted spans that drive the UI |
| Deterministic evaluation | fixture assertions without an LLM judge |

## Run locally

Backend (PowerShell):

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

Frontend, in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. The API is available at `http://localhost:8000`; evaluate with `python -m app.evaluation.run` from `backend`.

## Demo walkthrough

Run the Full Production Pipeline, then try high complexity, transient failure, exhausted primary, structured output with invalid first output, the same request twice for a cache hit, and the injection sample. The canvas reflects returned trace spans: skipped providers remain visible, security blocks stop downstream execution, and retry/fallback metadata is inspectable.

## Architecture and trade-offs

The gateway orders rate limit → security → routing → budget → cache → provider/retry/fallback → validation/correction → cache store → response. See [docs/architecture.md](docs/architecture.md), [docs/request-lifecycle.md](docs/request-lifecycle.md), [docs/visual-flow.md](docs/visual-flow.md), and [docs/decisions.md](docs/decisions.md).

SQLite cache and local tracing are not distributed; the limiter is single-process; heuristic security detection is incomplete; token estimates are approximate; mock quality is illustrative; fallback can change cost/quality; and concurrent identical misses can duplicate work. This is not an agent framework, RAG system, workflow builder, or generic LLM gateway product.

## Git workflow

Use `feature/LPP-XXX-description -> dev -> main` and commits in the form `[AREA][LPP-XXX] concise English description`. The repository intentionally contains no automated-authorship metadata.

## License

MIT.
