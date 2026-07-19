# Development Guide

## Local environment

Glyph uses a modern Python `src/` layout.

```bash
pip install -e ".[dev]"
pytest
glyph benchmark benchmarks/
```

The optional MCP surface is separate:

```bash
pip install -e ".[dev,mcp]"
glyph mcp --help
```

## Repository map

```text
src/glyph/
  core/           domain models and shared value objects
  source/         adapters, Markdown AST, document IR, candidates, tokenizer
  semantics/      rules, classification, clause parsing, policy resolution
  formats/        .glp parser and renderer
  pipeline/       compilation, provenance, conflicts, verification
  governance/     diff, lock, check, select, emit, lint, score, benchmarks
  interfaces/     CLI, services, configuration, diagnostics, optional MCP
tests/            synthetic and integration tests
benchmarks/      license-safe benchmark fixtures and generated reports
corpus/          pinned metadata-only external-corpus manifest and reports
docs/            product, engineering, and validation documentation
spec/            v0.1 format specification and conformance fixtures
evals/           separately governed evaluation harnesses
scripts/         repeatable release validation scripts
```

## Working on a change

1. Read the relevant owning package (`core`, `source`, `semantics`, `formats`,
   `pipeline`, `governance`, or `interfaces`) and its consumer modules first.
2. Write a short implementation plan for any non-trivial change.
3. Make the narrowest deterministic change that preserves format and metric
   invariants.
4. Add positive, negative, ambiguity, and compatibility tests as appropriate.
5. Update the closest product document and any affected command reference.
6. Run the validation proportional to the area changed.

## Documentation ownership

| Change | Required documentation update |
| --- | --- |
| CLI behavior or option | [CLI reference](cli-reference.md) and README if it changes the primary workflow. |
| `.glp` grammar or semantic model | [Specification](glp-spec.md), architecture, compatibility, and conformance fixtures. |
| Metric or strict gate | [No silent semantic loss](no-silent-semantic-loss.md), CI guide, and benchmark methodology. |
| Rule precedence or custom policy | [Custom rules](custom-rules.md). |
| Release validation | [Release process](release-process.md) and the relevant evidence report. |

## Non-negotiable engineering boundaries

- Do not call hosted services or an LLM from Glyph itself.
- Do not commit third-party source text into fixtures, tests, or reports.
- Do not lower thresholds simply to obtain a green result.
- Do not make a v0.2 feature appear as a lossless v0.1 rendering.
- Do not turn ambiguous natural language into opaque target strings.

See [Testing guide](testing.md) and [CONTRIBUTING.md](../CONTRIBUTING.md).
