# Testing Guide

Glyph's test strategy is layered because a parser can be locally correct while
still failing retention, compatibility, or determinism requirements.

## Test layers

| Layer | What it proves |
| --- | --- |
| Unit and parser tests | Candidate classification, clause parsing, expression construction, and fail-closed ambiguity handling. |
| Format and conformance tests | v0.1/v0.2 parsing, rendering, ordering, IDs, and protected downgrade boundaries. |
| Consumer tests | Verify, diff, lock, selection, emitters, provenance, and custom-rule behavior. |
| Synthetic benchmarks | Token reduction, expected semantics, retention, safety, and preservation under license-safe fixtures. |
| Fixed external corpus | Metadata-only static evidence on pinned repository revisions. |
| Wheel smoke | Package build and CLI behavior outside editable installation. |

## Everyday validation

```bash
pytest
ruff check .
mypy
glyph benchmark benchmarks/
git diff --check
```

For release-candidate changes:

```bash
python -m build
bash scripts/release-smoke.sh
```

The smoke script creates a disposable virtual environment for each run so it
tests the wheel built in that invocation rather than an older editable or cached
installation.

## Parser change checklist

Every new deterministic extraction shape needs:

- a positive synthetic fixture;
- a narrative or code-example non-match;
- an ambiguous alternative that remains preserved;
- risk and safety assertions when relevant;
- parse/render/parse and content-derived-ID coverage when it emits 0.2;
- downstream verification, diff, selection, lock, and emitter coverage if it
  changes representation.

## Evaluation boundary

The fixed external corpus is static evidence: it checks deterministic parsing,
retention, safety, and coverage on pinned files. It does not prove identical
agent behavior. The behavior-evaluation harness is separately governed and must
not be treated as an automatic substitute for static validation.

Read [Benchmark methodology](benchmark-methodology.md),
[External corpus harness](../corpus/README.md), and
[release process](release-process.md).
