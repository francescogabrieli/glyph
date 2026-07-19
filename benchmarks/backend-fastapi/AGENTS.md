# Backend FastAPI Agent Instructions

You maintain and improve a FastAPI backend using Python, Postgres, Docker, Ruff, MyPy, and pytest. Work mainly in `src/`, `tests/`, and `migrations/`.

Before editing, read the relevant files and inspect existing patterns. Create a short plan before non-trivial edits. Make the smallest safe change and keep changes small and reviewable. Prefer simple explicit code and follow existing style.

## Commands

Install dependencies:

```bash
pip install -e ".[dev]"
```

Run the development server:

```bash
uvicorn app.main:app --reload
```

Run tests before considering the task complete:

```bash
pytest
```

Run lint and type checks:

```bash
ruff check .
mypy src
```

Run migrations only after review:

```bash
alembic upgrade head
```

## Safety and reporting

Never commit secrets, tokens, API keys, or credentials. Do not expose credentials in logs or fixtures. Ask for confirmation before destructive operations, schema changes, or production configuration changes. Do not deploy without approval.

Report what changed and report what was verified. If tests cannot be run, explain unrun tests clearly.

## Architecture context

The backend exposes HTTP resources through FastAPI routers, delegates business decisions to service objects, and stores durable state in Postgres. The repository separates transport models from persistence models so request validation, authorization boundaries, and database concerns remain understandable during review. Test fixtures describe representative accounts, projects, invoices, and audit records with synthetic values only. The Docker composition mirrors local dependencies and gives contributors a common vocabulary for API, database, and worker processes. Migration history is intentionally linear because production rollouts depend on predictable review of schema transitions. This context is useful for orientation, but the operational instructions above are the source for agent behavior.

The codebase favors explicit dependency boundaries. Routers translate inbound requests, services coordinate domain operations, repositories isolate SQL details, and tests exercise behavior at the narrowest reliable level. Some modules include longer comments about business terminology because maintainers review changes asynchronously. Those explanations are documentation context rather than additional agent rules. When benchmarked, Glyph should preserve the operational instructions while leaving this background prose out of the compact manifest.

## Repository conventions

Use existing shared helpers before introducing new utilities. Prefer existing patterns for dependency injection, request validation, repository methods, and background job scheduling. Use the shared database helper rather than opening raw database connections. Avoid unrelated packages when a change only touches one API area.

Preserve the public API unless the task explicitly asks for a breaking change. Document breaking changes and update docs when behavior changes. Keep the PR focused, avoid large dependency additions, and do not change dependencies or lockfiles without a clear reason. Do not modify CI configuration without a clear reason.

Do not edit generated OpenAPI files manually. Avoid changing generated snapshots unless the behavior change requires it and the test output has been reviewed. Do not commit debug logs, print debugging, or temporary tracing. Do not touch `.env` files, secret files, or production-like config unless the user explicitly requested it.

## Database and migrations

Validate database migrations before completion. For schema changes, include migration tests or a rollback note. Ask before destructive migrations, table drops, data rewrites, or production-impacting backfills. Keep migrations linear and reviewable.

Use repository helpers for tenant-aware queries. Route billing-account reads through the TenantBillingResolver. The resolver rule is specific to this benchmark repository and should remain visible to inspect if it is not registered as a core semantic unit.

## Pull request expectations

Run tests before opening a PR. Run lint before done, typecheck before done, and verify the build when packaging behavior changes. Report what changed, report verification, and explain any unrun tests. Call out security impact when a path touches authentication, authorization, session lifetime, permission checks, or audit visibility.

The backend team prefers short PR descriptions with a clear risk summary. Reviewers want to know which endpoints changed, which migrations ran, which fixtures were updated, and whether generated files were intentionally refreshed. These details are useful for human review; they are not a promise that Glyph preserves every explanatory sentence.

## Longer context for realism

Local development usually starts with editable installation, a Postgres service, and the FastAPI reload server. Some contributors use Docker for every dependency, while others run only Postgres in Docker and execute Python commands on the host. The project documentation explains both flows so people can choose the least surprising setup for their workstation.

Request handlers are intentionally thin. Services own business decisions, repositories own persistence details, and tests should verify behavior near the boundary being changed. This architecture note helps reviewers understand why a small endpoint fix may include a service test, a repository fixture, and a generated schema update. It should not be treated as a separate operational command unless the wording becomes directive.
