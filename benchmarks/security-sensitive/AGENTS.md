# Security Sensitive Repository Instructions

This service handles authentication, authorization, credentials, API keys, and production configuration. It uses Python, FastAPI, Postgres, Docker, pytest, Ruff, and MyPy.

Read relevant files before editing. Create a short plan before touching auth, permissions, migrations, or production settings. Keep changes small and reviewable, prefer simple explicit code, and avoid large refactors.

Commands are intentionally concrete:

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src
docker build .
```

Never commit secrets, tokens, API keys, private keys, or credentials. Do not expose credentials in logs, tests, docs, or errors. Ask for confirmation before destructive operations. Ask before schema changes, unsafe migrations, security sensitive changes, or production config writes. Never deploy without approval.

Before completion, tests must pass. Run lint and type checks before done. Report what changed and what was verified. If any verification was skipped, explain unrun tests or checks.

## Security domain context

The service manages authentication sessions, authorization decisions, audit records, credential rotation metadata, and administrative workflows. Security reviews focus on data exposure, privilege boundaries, state transitions, and logging behavior. The repository contains synthetic examples of tokens and keys for parser tests, but those examples are deliberately invalid. Reviewers expect changes to explain whether a path touches authentication, authorization, session lifetime, or audit visibility.

The system separates policy evaluation from request handling so permission decisions can be tested independently. Audit events are structured for downstream monitoring, and failures are designed to be explicit rather than silent. Background documentation describes incident response expectations, support escalation paths, and deployment sequencing. Those notes provide domain context, while the operational instructions above define what a coding agent should compress into `.glp`.

This benchmark is intentionally safety-heavy. It includes repeated references to secrets, credentials, API keys, production configuration, migrations, deployment approval, and verification because real security-sensitive repositories often repeat these concepts in multiple sections.

## Security review workflow

Ask before security-sensitive changes, permission changes, authentication changes, authorization changes, schema changes, destructive operations, unsafe migrations, or production deploys. Do not deploy without approval. Do not modify production config, CI policy checks, or secret scanning configuration without a clear reason and reviewer approval.

Never commit secrets, credentials, tokens, API keys, private keys, real session identifiers, or customer-like security data. Do not expose credentials in logs, fixtures, screenshots, or generated examples. Do not touch `.env` files or secret files unless explicitly requested.

Report security impact for sensitive changes. Explain whether the path touches authentication, authorization, session lifetime, audit visibility, rate limiting, or permission inheritance. Document breaking changes when API behavior, token shape, or policy semantics change.

## Verification

Run tests before opening a PR. Run lint before done and typecheck before done. Verify the build before completion when packaging or deploy artifacts change.

```bash
pytest tests/security
pytest tests/policies
ruff check .
mypy src
```

Use existing shared helpers for policy evaluation, audit logging, and tenant resolution. Avoid raw database connections. Avoid unrelated packages and broad refactors. Preserve public APIs unless the task explicitly asks for migration work.

## Domain context

Security code is reviewed conservatively because small changes can alter access decisions. The project separates request handling, policy evaluation, audit recording, and session management so that tests can exercise each layer independently. This paragraph explains why reviewers care about narrow changes; it is background context, not an extra semantic unit.

Route emergency-access decisions through BreakGlassPolicyEvaluator. This rule is repository-specific and should remain an unmapped candidate unless a custom rule registers it.

## Release safety

Security releases are intentionally conservative. Before merging, reviewers need to know whether the change affects login, logout, password reset, token refresh, role assignment, permission inheritance, audit records, or administrative override behavior. Run the relevant policy and integration tests before opening a PR, and explain any unrun tests.

Do not change dependency versions, cryptographic libraries, token parsing, cookie attributes, CORS behavior, or CI security checks without a clear reason. Avoid large dependency additions. Preserve public APIs unless the task explicitly includes migration work, and document breaking changes.

Generated fixtures may include fake tokens or invalid private keys for parser coverage. Never replace those examples with real values. Do not commit screenshots that expose credentials. Do not commit debug logs from authentication flows. Do not touch secret files, environment files, production config, or deploy manifests unless explicitly requested.

The surrounding documentation explains incident response, escalation paths, and audit terminology. Those sections help humans reason about risk. Glyph should compress registered operational semantics, report high-confidence unmapped operational instructions, and avoid claiming that every background sentence has been preserved.

## Audit and privacy notes

Audit changes should be easy to review. Report whether new events contain identifiers, timestamps, actor information, target resources, permission decisions, or error details. Never include secrets, tokens, private keys, passwords, session values, or real user data in audit fixtures.

Ask before changing retention behavior, administrative override flows, emergency access, permission inheritance, or production monitoring. Preserve public APIs and documented security behavior unless the task explicitly asks for migration work. Update docs when behavior changes and document breaking changes.

The security guide also contains human escalation procedures. Those procedures are important for operations teams, but they are not all coding-agent rules. The compiler should keep explicit safety constraints and expose repository-specific directives that remain unmapped.
