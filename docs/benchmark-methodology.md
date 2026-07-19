# Benchmark Methodology

`glyph benchmark benchmarks/` runs each benchmark case containing `AGENTS.md` and `expected.json`.

For each case, Glyph:

- compiles Markdown to `.glp`
- counts Markdown tokens
- counts `.glp` tokens
- computes token reduction
- verifies expected semantic units, commands, and stack values
- computes structured coverage, retained coverage, and safety retention
- counts preserved directives, high-risk preserved directives, and dropped candidates
- counts conflicts
- writes `benchmark-report.json`
- writes `benchmark-report.md`

Token reduction:

```txt
1 - glp_tokens / markdown_tokens
```

Semantic coverage:

```txt
encoded_expected_items / expected_items
```

Structured coverage:

```txt
(canonical + policy candidates) / all operational candidates
```

Retained coverage includes preserved source-faithful directives; safety retention applies the same retained measure to high-risk candidates. Benchmark tables use these post-hardening metrics as release-review fields. Legacy semantic coverage and high-risk-unmapped counts remain in JSON and tables only as compatibility diagnostics.

Benchmarks are deterministic and do not use network or LLM calls.
