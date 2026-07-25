# Monorepo Fullstack Instructions

This monorepo includes a Python FastAPI backend, React TypeScript frontend, Postgres database, Docker services, Playwright tests, Ruff, MyPy, ESLint, and npm packages. Relevant paths include `backend/`, `frontend/`, `src/`, `tests/`, `docs/`, `infra/`, and `migrations/`.

General workflow:

- Always read relevant files before editing.
- Create a short plan before cross-package changes.
- Make the smallest safe change.
- Follow existing style and repository conventions.
- Keep changes small and reviewable.
- Do not add unrequested features.
- Do not perform large unrequested refactors.

Commands:

| label | command |
| --- | --- |
| install | `npm install` |
| backend install | `pip install -e ".[dev]"` |
| dev | `npm run dev` |
| test | `pytest` |
| frontend test | `npm test` |
| lint | `ruff check .` |
| frontend lint | `npm run lint` |
| typecheck | `mypy src` |
| frontend typecheck | `npm run typecheck` |
| build | `npm run build` |

Before marking work done, run the relevant tests. Run lint before done and typecheck before done for touched packages.

Never commit secrets, tokens, API keys, credentials, or production config. Do not expose credentials. Ask before destructive operations, schema changes, unsafe migrations, security sensitive changes, or deploys. Do not deploy without approval.

Report what changed and report verification. When tests cannot be run, explain unrun tests.

## Monorepo context

The monorepo contains backend services, frontend applications, shared packages, deployment manifests, documentation, and integration tests. Teams own different areas, but pull requests often cross boundaries when API contracts change. The backend exposes typed endpoints, the frontend consumes generated clients, and integration tests verify that the two sides agree on important flows.

Repository documentation explains package ownership, release trains, feature flag conventions, and migration history. Those sections are valuable for human orientation and review, but they are not all operational requirements for a coding agent.

## Package boundaries

Respect package boundaries and ask before crossing ownership boundaries. Avoid unrelated packages and unrelated workspaces. Keep each pull request focused on one product concern or infrastructure concern. Prefer existing patterns before adding a new package-level abstraction.

Preserve public APIs unless the task explicitly asks for a migration. Document breaking changes for exported TypeScript types, backend route contracts, database schemas, package exports, configuration keys, and event payloads. Update docs when behavior changes.

Use shared UI primitives in frontend packages. Use existing shared helpers in backend and platform packages. Use the shared database helper rather than opening raw database connections. Avoid large dependency additions and avoid dependency changes without a clear reason. Do not edit lockfiles unless dependency changes require it.

## Generated files and tooling

Do not edit generated files manually. Generated API clients, OpenAPI schemas, snapshots, typed route maps, and migration artifacts should be changed by their generation command. Avoid changing generated snapshots unless behavior changed and the new output has been reviewed.

Do not modify CI configuration without a clear reason. Do not commit debug logs, print debugging, or temporary browser traces. Do not touch `.env` files, secret files, production config, or deployment credentials unless explicitly requested.

## Verification by area

Run tests before opening a PR. Run lint before done and typecheck before done for every touched package. Verify the build before completion when package exports, generated clients, bundling, deployment manifests, or runtime configuration change.

```bash
pytest tests/api
npm test -- --runInBand
npm run lint
npm run typecheck
npm run build
```

Validate database migrations before completion. Ask before schema changes, destructive operations, unsafe migrations, production deploys, security-sensitive changes, or cross-package changes. Do not deploy without approval.

Report what changed, report verification, and explain unrun tests. Call out security impact when a path touches authentication, authorization, permission inheritance, session lifetime, audit visibility, or production config. Include migration notes when database or generated client behavior changes.

Route enterprise entitlement checks through EnterpriseEntitlementBridge. Route generated client publication through ClientPublishCoordinator. These repository-specific rules remain visible in the compiled policy representation.