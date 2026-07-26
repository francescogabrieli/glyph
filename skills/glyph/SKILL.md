---
name: glyph
description: Audit, compile, compare, and verify coding-agent instruction files with Glyph. Use for AGENTS.md, CLAUDE.md, Copilot instructions, Cursor rules, README, CONTRIBUTING, or docs when the user wants to reduce instruction tokens, inspect operational semantics, find unmapped directives, generate a separate .glp artifact, check freshness, or review semantic changes.
---

# Glyph

Use Glyph as a conservative, deterministic Instructions-as-Code toolchain. The objective is to make coding-agent guidance measurable and reviewable without silently changing source files or inventing policy.

## Operating rules

Never rewrite, delete, or replace the source instruction file unless the user explicitly requests it. Compile to a separate `.glp` artifact.

Inspect before compiling. Surface unmapped, preserved, ambiguous, high-risk, and conflicting directives instead of hiding them.

Do not claim lossless arbitrary Markdown compression, universal Markdown understanding, or identical model behavior. Treat metrics as evidence for the exact file and command that produced them.

Do not add an LLM interpretation step to Glyph's deterministic workflow.

## Locate the source

Prefer the file named by the user. Otherwise inspect the repository for supported files in this order:

1. `AGENTS.md`
2. `CLAUDE.md`
3. `.github/copilot-instructions.md`
4. `.cursorrules`
5. `.cursor/rules/*.mdc`
6. relevant `README.md`, `CONTRIBUTING.md`, or Markdown below `docs/`

When several files are relevant, explain the proposed scope before compiling them.

## Resolve the executable

Use `glyph` when it is already available.

If it is not available, do not install software silently. Explain the available project install command from the repository documentation. Until Glyph is published on PyPI, the immutable release install is:

```bash
python -m pip install "glyph-instructions @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
```

After PyPI publication, prefer the documented `uvx glyph-instructions` or `pipx` workflow.

## Trust-first workflow

For a source such as `AGENTS.md`, follow this sequence.

### 1. Inspect

```bash
glyph inspect AGENTS.md --show-unmapped
```

Summarize what Glyph recognized and call out anything unmapped, preserved, ambiguous, high-risk, or conflicting. Do not present structured coverage as retained coverage.

### 2. Compile separately

Choose an output next to the source unless the user specifies another path:

```bash
glyph compile AGENTS.md -o AGENTS.glp --report glyph-report.md
```

For `CLAUDE.md`, use `CLAUDE.glp`. Never overwrite the Markdown input.

### 3. Measure

```bash
glyph stats AGENTS.md AGENTS.glp
```

Report token reduction, structured coverage, retained coverage, safety retention, preserved directives, and dropped candidates separately when available.

### 4. Verify

```bash
glyph verify AGENTS.md AGENTS.glp
```

A successful verification means the artifact is fresh and consistent with the source under Glyph's supported semantics. It does not prove identical behavior from an agent runtime.

### 5. Review changes

When a previous manifest exists, compare it before accepting a replacement:

```bash
glyph diff previous.AGENTS.glp AGENTS.glp
```

Explain added, removed, and changed semantic units in plain language. Treat removals of safety, approval, testing, or reporting requirements as high attention.

## Strict adoption

Do not begin with strict gates on an unreviewed repository. Establish and audit a baseline first. Only then suggest thresholds such as:

```bash
glyph check AGENTS.md AGENTS.glp \
  --min-structured-coverage 80 \
  --min-retained-coverage 100 \
  --max-high-risk-preserved 0 \
  --min-reduction 20
```

Thresholds are repository policy, not universal defaults.

## Repository-specific meaning

When `glyph inspect --show-unmapped` identifies a stable repository convention, suggest the deterministic custom-rule workflow rather than modifying the shared parser:

```bash
glyph rules suggest AGENTS.md --format yaml
glyph compile AGENTS.md -o AGENTS.glp --rules glyph.rules.yml
```

Require human review of suggested rules before relying on them.

## Final response

State exactly which files were inspected or created, which commands ran, whether verification passed, and what remains unmapped or preserved. Mention skipped checks and their reason. Keep the source and generated artifact clearly distinguished.

Read `references/commands.md` for command selection and `references/trust-model.md` for interpretation boundaries.