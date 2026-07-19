# Getting Started

This guide takes a repository from Markdown instructions to a checked-in,
deterministic Glyph manifest. Glyph works alongside existing `AGENTS.md`,
`CLAUDE.md`, Copilot, Cursor, README, and CONTRIBUTING files; it does not
require native `.glp` support from those tools.

## Install

Glyph 0.2.0 is currently distributed from its immutable GitHub tag. PyPI
distribution is planned.

```bash
pip install "glyph-instructions @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
glyph doctor
```

For local development, install the repository with its development tools:

```bash
pip install -e ".[dev]"
```

The optional local MCP server is installed separately:

```bash
pip install "glyph-instructions[mcp] @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
```

## Compile the first manifest

Start with one existing instruction file:

```bash
glyph inspect AGENTS.md --show-unmapped
glyph compile AGENTS.md -o AGENTS.glp --report glyph-report.md
glyph stats AGENTS.md AGENTS.glp
```

`inspect` shows what Glyph recognized, structurally represented, preserved, or
classified as non-operational. Review this before treating the manifest as a
source of truth.

## Keep Markdown compatibility

Most agent runtimes still consume Markdown. Generate a compatible file from a
reviewed manifest when needed:

```bash
glyph emit AGENTS.glp --target agents-md -o AGENTS.generated.md
glyph emit AGENTS.glp --target claude-md -o CLAUDE.md
glyph emit AGENTS.glp --target copilot -o .github/copilot-instructions.md
glyph emit AGENTS.glp --target cursor -o .cursor/rules/glyph.mdc
```

Generated Markdown preserves encoded semantics, not the original prose or
layout. Keep the original file until your team deliberately changes ownership.

## Add a safe CI gate

Create a semantic lock and make retention explicit:

```bash
glyph lock AGENTS.md -o glyph.lock.json
glyph compile AGENTS.md -o AGENTS.glp \
  --strict \
  --min-structured-coverage 80 \
  --min-retained-coverage 100 \
  --max-high-risk-preserved 0
glyph check AGENTS.md AGENTS.glp \
  --min-structured-coverage 80 \
  --min-retained-coverage 100 \
  --max-high-risk-preserved 0 \
  --min-reduction 20
glyph check --lock glyph.lock.json
```

Choose thresholds from your own files and tighten them only after reviewing
preserved directives. A strict gate is a policy decision, not a universal
default. See [CI and lockfiles](ci-cd.md).

## Add repository-specific meaning

If an important repeated instruction is not in Glyph's registry, add a custom
semantic rule. If it needs 0.2 predicate structure, add an exact custom policy
instead. Both are local, versioned files and have deterministic precedence.

```bash
glyph rules suggest AGENTS.md --format yaml
```

Review suggestions before committing them; ambiguous input should remain
preserved. See [Custom rules](custom-rules.md).

## Next steps

- Read [Adoption guide](adoption-guide.md) for a phased rollout.
- Read [No silent semantic loss](no-silent-semantic-loss.md) before enabling
  strict CI.
- Read [`.glp` specification](glp-spec.md) before editing manifests manually.
