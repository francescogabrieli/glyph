# Complete Claude Code compilation example

This directory shows a complete, inspectable Glyph run using a realistic `CLAUDE.md` file.

The source file is [`CLAUDE.md`](CLAUDE.md). Glyph compiles it into the separate [`CLAUDE.glp`](CLAUDE.glp) artifact. The source is not rewritten or deleted.

Run the example locally:

```bash
glyph inspect examples/realistic-claude/CLAUDE.md --show-unmapped
glyph compile examples/realistic-claude/CLAUDE.md \
  -o /tmp/CLAUDE.glp \
  --report /tmp/glyph-report.md
glyph diff examples/realistic-claude/CLAUDE.glp /tmp/CLAUDE.glp
glyph verify examples/realistic-claude/CLAUDE.md /tmp/CLAUDE.glp
```

The committed `.glp` file is the expected deterministic output for the committed source. Recompiling should produce the same semantic manifest.

## What to audit

Review the canonical commands, workflow requirements, safety denials, approval requirements, and the final preserved structured policy. Then run `glyph inspect --show-unmapped` to see repository-specific instructions that Glyph does not silently generalize.

This example is deliberately longer than the minimal examples elsewhere in the repository. It mixes repeated rules, commands, safety constraints, repository-specific guidance, and explanatory prose, which is closer to how real coding-agent instruction files evolve.

It is still a maintained project fixture, not evidence that Glyph preserves arbitrary Markdown or guarantees identical agent behavior. The purpose is to make the compilation result directly reviewable before installation or adoption.
