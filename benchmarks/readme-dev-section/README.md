# Example Service

This README contains user-facing context plus development instructions. The service is a Python FastAPI app backed by Postgres and Docker. Most implementation work lives in `src/` and tests live in `tests/`.

## Local development

Install dependencies and start the API:

```bash
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Testing

Before opening a PR, make sure the suite is green.

```bash
pytest
ruff check .
mypy src
```

Read the relevant files before editing. Plan before editing migrations. Make the smallest safe change and keep the PR focused. Follow existing style.

## Security

Never commit secrets or API keys. Do not expose credentials in logs or fixtures. Ask before schema changes, destructive operations, unsafe migrations, production config writes, or deploys.

## Notes

The product supports multiple tenants. Background details here are intentionally prose-heavy and not all of them are operational instructions.

## Architecture overview

The service is organized around tenants, projects, memberships, and audit events. The README explains local setup because many contributors begin here before discovering the dedicated agent instruction file. It also contains human-oriented details about request routing, persistence boundaries, logging, and support workflows. Glyph should extract setup, testing, safety, and workflow instructions from this mixed-purpose document while reporting repository-specific operational candidates it cannot map.

This benchmark reflects a common adoption path: a project may not have an `AGENTS.md` file yet, but useful operational instructions already exist in README development sections. Glyph should support progressive adoption by compiling those sections into a `.glp` manifest and later emitting compatibility Markdown for existing tools.

## Contributor workflow

Use existing shared helpers before adding new utilities. Prefer existing patterns for routers, services, repositories, and test fixtures. Use the shared database helper rather than opening raw database connections. Keep changes small and reviewable.

Run tests before opening a PR. Run lint before done and typecheck before done. Verify the build before completion when packaging, Docker images, or generated clients change.

```bash
pytest
ruff check .
mypy src
docker build .
```

Never commit secrets, credentials, API keys, tokens, or real customer data. Do not expose credentials in logs or fixtures. Do not touch `.env` files or secret files unless explicitly requested. Ask before destructive operations, unsafe migrations, schema changes, production config writes, security-sensitive changes, or deploys.

Do not edit generated files manually. Do not change dependencies or lockfiles without a clear reason. Do not modify CI configuration without a clear reason. Do not commit debug logs.

Update docs when behavior changes. Document breaking changes for public APIs, configuration keys, database schema, or emitted events. Report what changed, report verification, and explain unrun tests.

## More architecture background

The service has a small domain model, but real teams still need setup notes, troubleshooting sections, and review expectations in the README. A reader may learn how tenants, projects, audit events, and workers fit together before finding the concrete commands. Glyph should distinguish these explanatory paragraphs from operational instructions.

Route support-ticket assignment through SupportQueueRouter. That instruction is specific to this repository and should be reported as unmapped unless a custom rule maps it.

## Operational notes for contributors

The README doubles as onboarding material, so it contains more prose than a dedicated agent instruction file. A new contributor may read about local services, tenant concepts, worker queues, and support workflows before reaching the concrete development commands. Glyph should not treat every explanatory paragraph as a rule.

For code changes, read the relevant files before editing and prefer existing patterns. Use existing shared helpers for tenant lookup, audit logging, database access, and background job scheduling. Avoid unrelated packages and broad refactors. Preserve public APIs unless the task explicitly asks for migration work.

For database changes, validate migrations before completion and ask before schema changes, unsafe migrations, or destructive operations. Include migration notes when a field is renamed, a table is backfilled, or generated clients need to be refreshed.

For review, keep the PR focused and report what changed. Report verification using the exact commands that ran. If a check was skipped because Docker, Postgres, or a browser dependency was unavailable, explain the limitation. Update docs when behavior changes and document breaking changes for API responses, configuration, events, or setup commands.

This README also includes troubleshooting examples that mention old errors and historical command output. Those examples help humans diagnose local setup failures. They should not become semantic rules unless they contain directive language such as "run pytest before opening a PR" or "never commit secrets."

## Troubleshooting and review

If local setup fails, check that Docker is running, Postgres accepts connections, and the editable Python install completed. These notes are troubleshooting context. They are not required commands for every change.

For pull requests, keep the scope narrow. Avoid unrelated packages, broad refactors, unrequested features, dependency changes without a reason, lockfile churn, and manual generated-file edits. Verify the build when Docker images, package exports, generated clients, or runtime configuration change.

Ask before deploys, production config changes, security-sensitive changes, destructive operations, schema changes, or unsafe migrations. Do not deploy without approval. Do not modify CI configuration without a clear reason.

The README is intentionally mixed-purpose. It explains the product, gives setup commands, and documents contribution expectations in one place. Glyph should produce a compact manifest from the registered operational instructions while reports make unmapped operational candidates auditable.
