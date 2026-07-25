# Claude Code Repository Instructions

You are working in a Python service with FastAPI, Postgres, Docker, pytest, Ruff, and MyPy. Read the relevant files before editing, then create a short plan for non-trivial changes. Keep changes small and reviewable. Prefer simple explicit code and follow existing style.

## Workflow

Before opening a PR, make sure the suite is green. Run lint before done and run type checks before done. Do not perform large unrequested refactors. Do not add unrequested features.

```bash
pip install -e ".[dev]"
pytest
ruff check .
mypy src
```

## Safety

Never commit secrets, tokens, API keys, or credentials. Do not expose credentials in logs, tests, fixtures, examples, or docs. Ask for confirmation before destructive operations, schema changes, security-sensitive changes, or production configuration writes. Do not deploy without approval.

## Reporting

Report what changed and report what was verified. If tests are not run, explain unrun tests. Use the shared database helper rather than opening raw connections.

The repository has background architecture notes that are useful but not operational. The API layer delegates persistence to repositories, domain services enforce invariants, and test fixtures mirror production data shapes without containing real customer data.

## Additional context

Claude is expected to work from repository evidence rather than broad assumptions. The project documentation describes service boundaries, package naming, release cadence, observability conventions, and deployment environments. Some sections are intentionally descriptive because new contributors need a narrative path through the codebase. Those paragraphs are useful context, but only concrete operational guidance should become semantic units.

The benchmark includes a custom-rule opportunity about shared database helpers. That sentence is operational and repository-specific, but it is not part of Glyph's default universal semantic registry. `glyph inspect` should surface it as unmapped, and `glyph rules suggest` should produce a deterministic custom rule candidate.
