# Architecture

FastAPI exposes a typed playground API. `Gateway` composes small, visible modules for rate limiting, prompt security, routing, token budgeting, exact caching, retries, fallback, validation, and tracing. Mock providers satisfy a minimal protocol and make every path work offline. SQLite stores only cache entries, trace records, and trace spans. The React client consumes execution truth and maps spans to XYFlow nodes; it does not reimplement routing.

The optional external provider is intentionally not required. At production scale, SQLite/cache, local limiter, and local spans could evolve toward shared infrastructure, but those systems are explicitly out of scope here.
