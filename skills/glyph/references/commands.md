# Glyph command selection

Use this reference to choose the smallest command that answers the user's question.

## Audit a source file

```bash
glyph inspect AGENTS.md --show-unmapped
glyph lint AGENTS.md
glyph score AGENTS.md
```

`inspect` is the default starting point. Use `lint` for source quality and conflicts. Use `score` when the user explicitly wants measurable quality or coverage information.

## Compile and report

```bash
glyph compile AGENTS.md -o AGENTS.glp --report glyph-report.md
glyph stats AGENTS.md AGENTS.glp
glyph verify AGENTS.md AGENTS.glp
```

Keep the report and manifest separate from the source. Use source-matching names such as `CLAUDE.glp` for `CLAUDE.md`.

## Compare semantic changes

```bash
glyph diff previous.AGENTS.glp AGENTS.glp
```

Use semantic diff instead of a text-only diff when reviewing instruction policy changes.

## Check an approved baseline

```bash
glyph check AGENTS.md AGENTS.glp \
  --min-structured-coverage 80 \
  --min-retained-coverage 100 \
  --max-high-risk-preserved 0 \
  --min-reduction 20
```

Do not copy these thresholds blindly. Use repository-approved values.

## Create a project baseline

```bash
glyph init --from AGENTS.md
```

Use this only when the user wants configuration and lockfile scaffolding.

## Repository-specific rules

```bash
glyph rules suggest AGENTS.md --format yaml
glyph compile AGENTS.md -o AGENTS.glp --rules glyph.rules.yml
```

Suggestions require review. Do not treat them as automatically approved semantics.

## Emit compatible Markdown

```bash
glyph emit AGENTS.glp --target agents-md -o AGENTS.generated.md
glyph emit AGENTS.glp --target claude-md -o CLAUDE.generated.md
glyph emit AGENTS.glp --target copilot -o copilot.generated.md
glyph emit AGENTS.glp --target cursor -o cursor.generated.mdc
```

Generated Markdown preserves semantics represented by the manifest, not the original prose layout. Do not overwrite existing agent instruction files without explicit user approval.

## Select task-specific guidance

```bash
glyph select AGENTS.glp --task "fix failing tests" --format markdown
glyph select AGENTS.glp --task "add database migration" --max-tokens 300
```

Selection is deterministic and rule-based. Relevant safety and approval instructions normally remain mandatory.