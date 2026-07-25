# Glyph examples

Start with one of the complete, inspectable compilation examples:

| Example | Source | Compiled artifact | What it demonstrates |
| --- | --- | --- | --- |
| [Claude Code service](realistic-claude/README.md) | [`CLAUDE.md`](realistic-claude/CLAUDE.md) | [`CLAUDE.glp`](realistic-claude/CLAUDE.glp) | Python service workflow, safety rules, verification, and repository-specific guidance |
| [Full-stack monorepo](realistic-agents/README.md) | [`AGENTS.md`](realistic-agents/AGENTS.md) | [`AGENTS.glp`](realistic-agents/AGENTS.glp) | Python and Node tooling, package boundaries, generated files, migrations, and approvals |

Each complete example includes the original instruction file, the committed deterministic `.glp` output, reproducible commands, and an audit checklist. Glyph writes a separate artifact and does not rewrite the source file.

Other directories demonstrate narrower features such as custom semantic rules, MCP configuration, and small backend workflows.

These are maintained realistic fixtures for inspection and reproducibility. They do not imply universal Markdown support, lossless arbitrary compression, or identical coding-agent behavior.