# LLM Production Patterns roadmap

The integration branch is `dev`; releases move to `main` only after the full validation matrix passes. Each meaningful change uses one sequential LPP card and a named branch.

## Foundation and backend

- [x] LPP-001 Initialize repository structure
- [x] LPP-002 Configure FastAPI application
- [x] LPP-003 Configure React application
- [x] LPP-004 Add local SQLite persistence
- [x] LPP-005 Implement provider protocol and deterministic mocks
- [x] LPP-006 Add deterministic model routing
- [x] LPP-007 Add bounded provider retries
- [x] LPP-008 Add ordered provider fallback
- [x] LPP-009 Add persistent request tracing
- [x] LPP-010 Validate structured provider output
- [x] LPP-011 Implement token budgeting
- [x] LPP-012 Add SQLite response caching
- [x] LPP-013 Add local token-bucket rate limiting
- [x] LPP-014 Add prompt security controls
- [x] LPP-015 Compose the production-pattern gateway
- [x] LPP-016 Add deterministic evaluation dataset and CLI
- [x] LPP-017 Expose the playground API
- [x] LPP-018 Expose provider discovery and optional external transport

## Visual execution product

- [x] LPP-019 Add typed flow templates
- [x] LPP-020 Build the interactive XYFlow canvas
- [x] LPP-021 Visualize provider routing and fixed selection
- [x] LPP-022 Visualize retries and fallback states
- [x] LPP-023 Visualize cache and security short-circuits
- [x] LPP-024 Visualize structured correction
- [x] LPP-025 Add trace timeline and node inspector
- [x] LPP-026 Add frontend execution replay
- [x] LPP-027 Add pattern explorer and configuration controls
- [x] LPP-028 Add evaluation interface

## Quality and release

- [x] LPP-029 Add focused backend pattern tests
- [x] LPP-030 Add gateway/API integration tests
- [x] LPP-031 Add dedicated frontend execution-mapping tests
- [x] LPP-032 Add continuous integration
- [x] LPP-033 Document architecture and visual execution
- [x] LPP-034 Complete final reliability, accessibility, and UI hardening

All roadmap cards are complete and have dedicated implementation, validation, and release evidence in the repository history.
