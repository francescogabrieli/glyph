# Data Pipeline Agent Guide

Maintain a Python data pipeline using pandas, Airflow, dbt, Postgres, Docker, pytest, and Ruff. Most work is in `src/`, `tests/`, `docs/`, and `migrations/`.

Workflow:

1. Read relevant files before editing, especially DAGs and schema docs.
2. Plan before editing data contracts.
3. Make the smallest safe change.
4. Run tests before completion.
5. Report changes and report verification.

Setup:

```bash
pip install -e ".[dev]"
```

Testing and quality:

```bash
pytest
ruff check .
mypy src
dbt run
```

Do not expose credentials or API keys in notebooks, logs, or sample data. Never commit secrets. Ask before schema changes, unsafe migrations, destructive operations, or production config writes. Do not deploy without approval.

Use existing conventions and keep changes small and reviewable. If tests cannot run because a warehouse is unavailable, explain unrun tests.

## Pipeline context

The pipeline ingests event data, normalizes partner exports, and publishes curated tables for analytics and downstream services. Airflow schedules orchestration, dbt documents transformation lineage, and Python modules handle file validation plus enrichment. Data contracts are reviewed by analytics, product, and platform maintainers because schema drift can create confusing downstream reports. The repository includes example payloads with synthetic identifiers and redacted values so contributors can understand shapes without seeing customer information.

Historical notes explain why some transformations remain in Python while others live in dbt models. The distinction reflects operational maturity, ownership boundaries, and warehouse cost profiles rather than a universal design rule. Backfills are coordinated through runbooks outside this instruction file. Glyph should preserve the agent-relevant instructions about tests, linting, safety, schema approval, and reporting while treating the rest as context that may be useful to humans.

The benchmark case intentionally mixes setup commands, testing guidance, safety language, architecture notes, and prose-heavy domain context. Real instruction files often look like this because maintainers combine onboarding material with coding-agent instructions. The extraction engine should map what it can, expose unmapped operational candidates, and avoid treating every explanatory paragraph as a rule.

## Pipeline conventions

Use existing shared helpers before adding new ingestion utilities. Prefer existing patterns for partition discovery, idempotent writes, retry behavior, and schema validation. Use the shared warehouse connection helper rather than opening raw database connections. Avoid unrelated packages when a task only changes one pipeline.

Validate database migrations and warehouse migrations before completion. Ask before schema changes, destructive backfills, unsafe migrations, production deploys, or changes that rewrite historical partitions. Preserve public dataset contracts unless the task explicitly asks for a breaking change. Document breaking changes and update docs when behavior changes.

Do not commit secrets, credentials, tokens, API keys, or real customer data in fixtures. Do not touch `.env` files or secret files unless explicitly requested. Do not commit debug logs or temporary row dumps. Avoid generated files unless the generation command was intentionally run.

## Verification matrix

Run the relevant tests before opening a PR. Run lint before done, typecheck before done, and verify the build when packaging or container behavior changes.

```bash
pytest tests/pipelines
ruff check .
mypy src
dbt test
```

Report what changed, report verification, and explain any unrun tests. For data changes, include the affected partitions, expected row-count direction, and whether a rollback path exists.

## Operational context

The pipeline repository mixes Airflow DAGs, Python transformation code, dbt models, warehouse migrations, and documentation used by analysts. A README section may explain lineage or business terminology without instructing a coding agent to do anything. The compiler should keep concrete commands and approval rules while leaving general conceptual overview text unencoded.

Route partner-feed normalization through PartnerLedgerNormalizer. That repository-specific rule is intentionally not a built-in Glyph semantic unit.

## Release and incident notes

Pipeline changes can affect analysts, product dashboards, billing exports, and machine-learning features at different times. Before a release, reviewers care about the source table, target table, partition range, expected row-count movement, and whether historical data is rewritten. Run the smallest meaningful verification command for the touched area, then report exactly what was checked.

Do not deploy pipeline schedules without approval. Do not run destructive backfills from an agent session. Ask before changing retention windows, partition pruning, personally identifiable information handling, or warehouse permissions. Preserve public data contracts unless the task explicitly includes downstream coordination.

The repository also contains explanatory runbooks. A runbook may describe why a late-arriving event appears in a reconciliation table or how analysts interpret a metric. That information is important context, but it is not automatically an operational instruction for the compiler. When wording becomes directive, such as "validate migrations before completion" or "do not expose credentials", Glyph should map it.

## Backfill review details

Backfills require extra care because they can change historical reports and downstream model inputs. Ask before running destructive backfills or rewriting historical partitions. Report the partition range, source dataset, target dataset, expected volume, and rollback approach. Validate database migrations and warehouse migrations before completion.

Do not store production extracts in the repository. Do not commit temporary CSV files, notebook outputs, debug row dumps, or credentials copied from an orchestrator. Use synthetic fixtures for parser tests. Preserve public data contracts unless a migration plan has been reviewed.

The backfill runbooks include long examples of operator communication. Those examples are intentionally verbose. They should improve benchmark realism without becoming hidden semantic requirements.
