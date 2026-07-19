# Launch Plan Notes

## Core Message

Coding agents waste context on verbose instruction files. Glyph turns those instructions into compact, measurable semantic manifests. It reports what it cannot safely map, instead of silently dropping instructions.

## Demo Commands

```bash
glyph inspect AGENTS.md --show-unmapped
glyph compile AGENTS.md -o AGENTS.glp --strict --min-operational-coverage 80
glyph stats AGENTS.md AGENTS.glp
glyph select AGENTS.glp --task "fix failing tests" --format markdown
glyph benchmark benchmarks/
glyph benchmark-real . --patterns "AGENTS.md,README.md,CONTRIBUTING.md,CLAUDE.md,.github/copilot-instructions.md,.cursor/rules/*.mdc"
```

## Benchmark Claims

Use generated benchmark output only. Claims should mention exact token reduction, semantic coverage, operational coverage, unmapped count, and conflicts for the run being shown.

Do not claim fixed reduction percentages across all repositories.

Do not claim identical LLM behavior.

Do not claim arbitrary Markdown is compressed without loss.

## Honest Limitations

- Glyph preserves measurable operational semantics, not every word.
- Exceptions are reported as unmapped or warnings when the `.glp` model cannot represent them.
- Custom repository policy may need custom rules.
- v0.1 is local, deterministic, and plain-text only.
- v0.1 does not include a VSCode plugin, web app, hosted service, LLM classifier, binary format, or native agent runtime integration.

## Suggested Launch Posts

- Short GitHub release note with commands and benchmark output.
- Hacker News post focused on deterministic agent-instruction compression.
- Reddit posts for `r/programming`, `r/LocalLLaMA`, `r/ChatGPTCoding`, and `r/github`.
- X/Twitter and LinkedIn posts with inspect output and `.glp` before/after.
- Dev.to walkthrough showing CI enforcement.
- AI engineering Discord post with MCP setup.

## Target Communities

- GitHub
- Hacker News
- Reddit `r/programming`
- Reddit `r/LocalLLaMA`
- Reddit `r/ChatGPTCoding`
- Reddit `r/github`
- X/Twitter
- LinkedIn
- Dev.to
- AI engineering Discords
- Open-source agent communities

## Potential Ecosystem Targets

- AGENTS.md ecosystem
- Claude Code workflows
- Codex workflows
- Cursor rules workflows
- Copilot custom instructions workflows
- MCP tool directories
- Agent framework repositories

Do not open ecosystem PRs or issues until the v0.1 release artifacts and benchmark numbers are finalized.
