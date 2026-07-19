# Contributing

Thanks for contributing. This guide describes the pull request workflow for a full-stack monorepo with Python, React, TypeScript, Postgres, Docker, pytest, Ruff, MyPy, ESLint, and Playwright.

## Before opening a PR

- Read relevant files before editing.
- Create a short plan before cross-package work.
- Keep the PR focused and avoid broad rewrites.
- Do not add unrequested features.
- Follow existing style and repository conventions.
- Make sure the suite is green.
- Run lint before completion.
- Run type checks before completion.
- Report what changed and report what was verified.

## Commands

| check | command |
| --- | --- |
| install | `npm install` |
| backend install | `pip install -e ".[dev]"` |
| backend tests | `pytest` |
| frontend tests | `npm test` |
| backend lint | `ruff check .` |
| frontend lint | `npm run lint` |
| backend typecheck | `mypy src` |
| frontend typecheck | `npm run typecheck` |
| build | `npm run build` |

## Safety

Never commit secrets, credentials, API keys, tokens, or private keys. Do not expose credentials in logs, tests, fixtures, examples, or docs. Ask before destructive operations, schema changes, unsafe migrations, security-sensitive permission changes, or production configuration writes. Do not deploy without approval.

If tests cannot be run locally, explain unrun tests and why they were skipped.

## Review context

Contributors use this document to understand branch hygiene, code review expectations, release notes, and ownership boundaries. Some paragraphs are social process rather than executable instructions. The operational parts matter to coding agents because they define what needs to happen before a pull request is ready for review.

The repository includes generated API clients, shared UI packages, backend service modules, and infrastructure manifests. Changes that cross these boundaries usually require careful review by multiple maintainers. Glyph should preserve rules about focused changes, tests, linting, type checking, safety approvals, and reporting while leaving general contribution etiquette as prose.

## Pull request checklist

Read the relevant files before editing and create a short plan for non-trivial work. Keep the PR focused. Avoid unrelated packages, unrelated workspaces, broad refactors, and unrequested features. Follow existing style and prefer existing patterns.

Run tests before opening a PR. Run lint before done, typecheck before done, and verify the build when packaging or generated clients change. If tests cannot be run, explain why in the PR notes.

Never commit secrets, credentials, tokens, API keys, private keys, or real customer data. Do not touch `.env` files or secret files unless explicitly requested. Ask before destructive operations, schema changes, unsafe migrations, production config writes, security-sensitive changes, or deploys.

Do not edit generated files manually. Do not change dependencies or lockfiles without a clear reason. Do not modify CI configuration without a clear reason. Do not commit debug logs.

Update docs when behavior changes. Document breaking changes. Report what changed and report verification. Call out security impact when a path touches authentication, authorization, permissions, session lifetime, or audit visibility.

## Review guidance

Reviewers look for a clear problem statement, narrow scope, passing checks, and honest notes about risk. They do not need every implementation detail repeated in the PR body, but they do need to understand generated file changes, migrations, dependency updates, and public API changes.

Use ReleaseNoteClassifier for user-visible release notes. That classifier is repository-specific and should remain unmapped unless the repository adds a custom semantic rule.

## Merge readiness

Before requesting review, make sure the relevant tests are green. Run lint and type checks for touched areas. Verify the build when package exports, generated clients, or deployment artifacts change. Explain any check that could not be run.

Do not merge generated file changes unless the generator was intentionally run. Do not change dependencies, lockfiles, CI configuration, or release scripts without a clear reason. Avoid large dependency additions.

Contribution documents often include etiquette, review norms, and historical process notes. Those sections are valuable for humans, but Glyph should only compact operational instructions it can register or confidently surface as unmapped candidates.
