# CLI Reference

All commands are local and deterministic. Run `glyph <command> --help` for the
complete option list installed with your version.

## Orient and initialize

| Command | Purpose |
| --- | --- |
| `glyph version [--json]` | Print installed version and capabilities. |
| `glyph doctor [--json]` | Check parsing, rendering, token counting, classification, and writable working directory. |
| `glyph init [--from FILE] [--force]` | Create `.glyph/config.toml`, `AGENTS.glp`, and, with `--from`, a lockfile. |

## Compile, render, and inspect

| Command | Purpose |
| --- | --- |
| `glyph compile INPUT... -o OUTPUT` | Compile one or more Markdown inputs into a `.glp` manifest. |
| `glyph render INPUT.glp -o OUTPUT.md` | Render a manifest as compatibility Markdown. |
| `glyph inspect INPUT [--show-unmapped]` | Show candidates, classifications, commands, policies, preservation, and conflicts. |
| `glyph stats INPUT.md INPUT.glp` | Compare token counts and reduction. |
| `glyph verify INPUT.md INPUT.glp` | Report semantic, structured, retained, and safety coverage. |

Useful `compile` options include:

```bash
glyph compile AGENTS.md -o AGENTS.glp \
  --adapter agents_md \
  --profile compact \
  --rules glyph.rules.yml \
  --report glyph-report.json
```

`--adapter` overrides automatic source detection. Profiles are `readable`,
`compact` (default), and `ultra`.

Strict compilation can enforce `--min-structured-coverage`,
`--min-retained-coverage`, `--min-agent-instruction-coverage`,
`--max-preserved`, `--max-high-risk-preserved`, and `--require-structured`.
`--min-operational-coverage` remains an alias for structured coverage.

## Diagnose and improve instructions

| Command | Purpose |
| --- | --- |
| `glyph lint INPUT.md` | Identify instruction smells with severity and suggested fixes. |
| `glyph score INPUT.md [--badge]` | Produce an explainable instruction-quality score. |
| `glyph diff OLD NEW` | Compare semantic units, policies, commands, and safety regressions. |
| `glyph rules suggest INPUT.md --format yaml` | Generate reviewable semantic-rule suggestions; it does not invent ambiguous 0.2 policy expressions. |

## Enforce and integrate

| Command | Purpose |
| --- | --- |
| `glyph lock INPUT... -o glyph.lock.json` | Create a content-addressed semantic lockfile. |
| `glyph check INPUT.md INPUT.glp ...` | Check coverage, reduction, freshness, preservation, and conflicts. |
| `glyph check --lock glyph.lock.json` | Verify lockfile input hashes and semantic fingerprints. |
| `glyph emit INPUT.glp --target TARGET -o OUTPUT` | Generate a Markdown fallback. |
| `glyph select INPUT.glp --task TEXT --format glp` | Select a deterministic, task-relevant subset. |
| `glyph mcp` | Start the optional local MCP server over stdio. |

Emitter targets are `agents-md`, `claude-md`, `copilot`, `cursor`, and
`generic-md`. Selection formats are `glp` and `markdown`; `--max-tokens` fails
instead of silently omitting mandatory safety instructions.

## Benchmark

```bash
glyph benchmark benchmarks/
glyph benchmark-real .
glyph benchmark-real . --write
```

`benchmark` writes reports under the benchmark root. `benchmark-real` discovers
supported instruction files and is read-only unless `--write` is supplied.
Read [Benchmark methodology](benchmark-methodology.md) before quoting results.
