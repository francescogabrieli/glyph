# Glyph Report

Example generated-style report for a small backend instruction file.

- Source: `examples/backend/AGENTS.md`
- Manifest: `examples/backend/AGENTS.glp`
- Demonstrates: `glyph compile`, `glyph inspect`, `glyph stats`, `glyph check`

Try:

```bash
glyph inspect examples/backend/AGENTS.md --show-unmapped
glyph stats examples/backend/AGENTS.md examples/backend/AGENTS.glp
glyph check examples/backend/AGENTS.md examples/backend/AGENTS.glp --min-coverage 90 --min-operational-coverage 80 --min-reduction 20
```
