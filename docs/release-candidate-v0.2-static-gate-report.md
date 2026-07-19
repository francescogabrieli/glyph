# Glyph `.glp 0.2` Static Gate Report

Date: 2026-07-19

## Outcome

The fixed ten-SHA external static gate is green without lowered thresholds.
This report is metadata-only: no third-party directive text, checkout path, or
repository-local identity was added to the project.

| Criterion | Result |
| --- | ---: |
| Zero crashes | pass |
| Zero nondeterminism | pass |
| Retained coverage | 100.0% |
| Safety retention | 100.0% |
| Dropped candidates | 0 |
| High-risk preserved directives | 0 |
| Agent-instruction coverage | 96.63% (threshold 90%) |
| Structured operational coverage | 82.18% (threshold 80%) |

The corpus contains 10 repositories, 124 supported files, and 18
agent-specific files. Average structured coverage is 78.65%; 316 genuinely
ambiguous or unsupported lower-risk directives remain source-faithfully
preserved. Average token reduction is 55.82%; negative per-file reductions are
reported rather than clamped.

## Implemented boundary

- Risk classification now requires a security-relevant relation for ambiguous
  lexemes such as token, permission, schema, credential availability, and
  production recommendations.
- Generic command prompts, implementation plans, passive product contracts,
  and non-directive conditional descriptions use one authoritative operational
  decision.
- Source-code fence statements cannot inherit policy modality from surrounding
  headings; only explicit directive comments in agent-instruction files are
  eligible, while executable commands remain handled separately.
- Local coreference is limited to an immediately preceding clause with one
  deterministic label, located resource, or grammatical subject.
- `.glp 0.2` adds `allow` and an inseparable `PolicyLink` only because the
  sanitized residual set contains explicit authorization and mixed
  allow/deny clauses.
- Conditions and alternatives use the existing `atomic`, `all`, `any`, and
  `not` expression language. No sequence, implication, NLP, or LLM dependency
  was added.

## Validation

| Check | Result |
| --- | ---: |
| Pytest | 384 passed |
| Ruff | pass |
| mypy | pass (9 configured modules) |
| Package build | sdist and wheel built |
| Fresh-wheel release smoke | pass; disposable environment created for each run |
| Synthetic benchmark | 96.6% structured; 100% retained; 100% safety; 0 high-risk preserved; 0 dropped |
| Fixed external corpus | every static gate criterion passed |
| Determinism | zero failures |
| Semantic conflicts | zero |

## Release boundary

This closes the static expressiveness and classification blocker, including a
fresh-wheel smoke run. Publication still requires the normal human release
decision and final artifact/diff review; tagging and publication were not run.
The separately governed external behavior matrix remains outside this
milestone and was not run.
