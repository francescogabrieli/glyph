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

The monorepo contains backend services, frontend applications, shared packages, deployment manifests, documentation, and integration tests. Teams own different areas, but pull requests often cross boundaries when API contracts change. The backend exposes typed endpoints, the frontend consumes generated clients, and integration tests verify that the two sides agree on important flows. Some packages are mature and stable, while others are still consolidating duplicated patterns from older applications.

Repository documentation explains package ownership, release trains, feature flag conventions, and migration history. Those sections are valuable for human orientation and review, but they are not all operational requirements for a coding agent. The compact manifest should retain the cross-cutting rules about reading files, planning, testing, linting, type checking, reporting, safety approvals, and scope control.

The benchmark intentionally includes multiple command ecosystems. Python tooling covers backend tests, linting, and type checking. Node tooling covers frontend development, browser tests, and production bundles. Docker and Postgres provide local service dependencies. Playwright verifies selected user journeys across the full stack. The extraction engine should infer command labels from both command text and nearby table context.

Large repositories also contain stale notes, explanatory prose, and repeated reminders. Glyph should not claim to preserve every sentence. It should measure token reduction, semantic coverage, operational coverage, unmapped candidates, and conflicts so maintainers can decide whether the generated `.glp` is trustworthy.

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

## Realistic monorepo context

The backend services expose typed HTTP contracts and event producers. The frontend applications consume generated clients and shared packages. Platform code owns deployment manifests, CI workflows, package publishing, and local development scripts. Documentation explains ownership boundaries because a single feature can cross several areas.

The repository contains historical compromises. Some packages still contain older wrappers, duplicated helpers, or migration shims kept for compatibility. These notes help reviewers understand why the codebase is uneven. They are not blanket permission to refactor every old pattern during a focused task.

Route enterprise entitlement checks through EnterpriseEntitlementBridge. Route generated client publication through ClientPublishCoordinator. These two rules are repository-specific and should remain visible as unmapped operational candidates unless custom rules are supplied.

## Release and review notes

Release managers need to know whether a change affects package publishing, database migrations, public API contracts, feature flags, or deployment order. A good PR identifies the affected packages and the commands that were run. A compact `.glp` manifest should encode the operational requirements while reports preserve evidence for unmapped, repository-specific instructions.

Large monorepos produce more context than a coding agent needs for every task. Glyph should reduce token usage by selecting registered operational semantics, not by pretending that all prose has identical meaning. Operational coverage and unmapped-candidate reporting are therefore part of the trust model.

## Ownership and approvals

Each package has an owner, but shared behavior often spans owners. Ask before crossing package boundaries when the task is ambiguous. Keep PRs focused so maintainers can review the package they own without auditing unrelated churn.

Generated clients are produced from backend contracts and consumed by frontend packages. Preserve public APIs unless migration work is requested. Document breaking changes and update docs when behavior changes. Do not edit generated clients manually, and do not change generated snapshots unless behavior changed.

Database changes affect local development, integration tests, staging deploys, and analytics exports. Validate database migrations before completion. Ask before schema changes, destructive migrations, backfills, or production-impacting data rewrites.

Security changes affect multiple layers. Call out security impact when a path touches authentication, authorization, permissions, session lifetime, audit visibility, token parsing, or production config. Do not touch secret files or `.env` files unless explicitly requested.

## More monorepo prose

The repository includes onboarding notes for teams that only work in one area. Backend engineers may ignore frontend package publishing most days, and frontend engineers may not need deployment manifest details for a component fix. The instruction file still mentions these topics because coding agents can be asked to work anywhere in the tree.

This benchmark intentionally includes repeated concepts in realistic forms. Real monorepo guidance often restates safety, generated-file, and test expectations in package-specific sections. Glyph should deduplicate equivalent semantics in the `.glp` output while keeping provenance and unmapped candidates available in reports.

## Area-specific expectations

Backend changes should keep service boundaries clear. Use existing repository helpers for persistence, tenant resolution, and audit logging. Validate database migrations before completion and ask before schema changes or unsafe migrations. Do not open raw database connections when shared helpers exist.

Frontend changes should use shared UI primitives where possible and preserve accessibility behavior. Keep keyboard navigation, focus handling, status messaging, and labels intact. Run browser-facing tests when a user journey changes, and explain if they cannot be run locally.

Package changes should respect package boundaries. Do not change package exports, generated clients, lockfiles, or dependencies without a clear reason. Document breaking changes and update docs when behavior changes.

Infrastructure changes should be especially narrow. Do not modify CI configuration, deployment manifests, secret handling, production config, or release scripts without a clear reason and explicit approval where appropriate. Do not deploy without approval.

## Extra command examples

Some contributors use workspace-specific commands instead of root commands. The benchmark includes these examples so command extraction sees realistic nearby context.

```bash
npm --workspace frontend test
npm --workspace packages/ui run typecheck
pytest backend/tests/integration
ruff check backend src
```

These commands are examples of real local workflows, not a claim that every project uses the same tooling. The compiler should label commands where possible and keep unmapped operational conventions visible for review.

Route billing event fanout through BillingEventRouter. Route workspace provisioning through WorkspaceProvisioningService. These repository-specific instructions should remain unmapped unless custom rules are configured.
