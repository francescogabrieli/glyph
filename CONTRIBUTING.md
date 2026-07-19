# Contributing to Glyph

Thank you for helping make agent instructions measurable, portable, and safer
to evolve.

## Before opening a change

1. Read [the development guide](docs/development.md) and
   [the testing guide](docs/testing.md).
2. Check existing issues or discussions for overlapping work.
3. Keep the change focused: parser behavior, documentation, rules, and tests
   should all describe the same intended semantics.
4. Do not add third-party instruction text or repository-specific identities to
   committed fixtures, tests, or reports.

## Local setup

```bash
pip install -e ".[dev]"
pytest
glyph benchmark benchmarks/
```

## Contribution principles

- Preserve measurable operational semantics; do not compress arbitrary prose.
- Prefer deterministic rules and small, reviewable changes.
- Keep ambiguous language preserved rather than guessing a policy.
- Add synthetic positive and negative fixtures for parser behavior.
- Do not lower gates to make a benchmark or corpus pass.
- Do not add network calls, remote dependencies, or LLM calls to the library or
  benchmark pipeline.

## Pull request expectations

Describe the user-facing outcome, the semantic boundary, and the validation
performed. Include relevant command output or generated report deltas, but do
not commit external source text.

Changes to format, parser, custom-rule handling, or metrics should include
round-trip, determinism, and regression tests in addition to unit tests.

## Reporting issues

Use a minimal synthetic example whenever possible. Include:

- input format and adapter;
- expected safe behavior;
- actual result and command used;
- whether the candidate is operational, ambiguous, or repository-specific;
- Glyph version and platform.

For security-sensitive reports, use [SECURITY.md](SECURITY.md) rather than a
public issue.
