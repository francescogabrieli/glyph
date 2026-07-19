# Agent Instructions

Generated from a Glyph `.glp` manifest. This preserves encoded operational semantics, not original prose.

## Agent

- fullstack

## Stack

- `fastapi`
- `postgres`
- `pytest`
- `python`
- `react`
- `typescript`

## Workflow

1. read
2. plan
3. minimal change
4. lint
5. typecheck
6. test
7. report

## Commands

- `dev`: `npm run start`
- `lint`: `npm test -- --runInBand`
- `test`: `pytest`
- `typecheck`: `uv run mypy src`

## Required

- Follow existing repository style and conventions.
- Create a short plan before non-trivial edits.
- Read the relevant files before editing.
- Report what changed.
- Report what was verified.
- Run the test suite before considering the task complete.

## Forbidden

- Do not perform large unrequested refactors.
- Do not add unrequested features.
- Never commit secrets, tokens, API keys, or credentials.

## Ask First

- Ask for confirmation before destructive operations.
- Ask before schema changes.
