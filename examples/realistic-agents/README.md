# Complete AGENTS.md compilation example

This directory contains a realistic full-stack monorepo instruction file and its deterministic `.glp` output.

The source is [`AGENTS.md`](AGENTS.md). Glyph produces the separate [`AGENTS.glp`](AGENTS.glp) artifact and leaves the source untouched.

Reproduce the run:

```bash
glyph inspect examples/realistic-agents/AGENTS.md --show-unmapped
glyph compile examples/realistic-agents/AGENTS.md \
  -o /tmp/AGENTS.glp \
  --report /tmp/glyph-report.md
glyph diff examples/realistic-agents/AGENTS.glp /tmp/AGENTS.glp
glyph verify examples/realistic-agents/AGENTS.md /tmp/AGENTS.glp
```

The example covers mixed Python and Node tooling, package boundaries, generated files, database migrations, safety approvals, public API preservation, and repository-specific routing rules.

It is a maintained realistic fixture rather than a claim about arbitrary Markdown or identical coding-agent behavior.