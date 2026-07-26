# Glyph agent skill

The [`glyph`](glyph/SKILL.md) skill teaches coding agents to audit, compile, compare, and verify instruction files with Glyph using a conservative trust-first workflow.

It supports requests involving `AGENTS.md`, `CLAUDE.md`, Copilot instructions, Cursor rules, `README.md`, `CONTRIBUTING.md`, and instruction-like Markdown below `docs/`.

## What the skill does

The skill instructs the agent to:

- locate the relevant instruction source;
- run `glyph inspect --show-unmapped` before compilation;
- keep the source untouched and generate a separate `.glp` artifact;
- report structured coverage, retained coverage, safety retention, and token reduction separately;
- surface preserved, unmapped, ambiguous, high-risk, conflicting, or dropped directives;
- run `glyph verify` after compilation;
- use semantic diff when reviewing a changed manifest;
- avoid claiming universal Markdown understanding or identical agent behavior.

## Codex

This repository includes [`.codex-plugin/plugin.json`](../.codex-plugin/plugin.json), which exposes the `skills/` directory as a skill-only Codex plugin.

For Codex versions that support direct skill installation, the skill directory can also be installed from:

```text
https://github.com/francescogabrieli/glyph/tree/main/skills/glyph
```

After installation, ask Codex:

```text
Use the Glyph skill to inspect AGENTS.md, explain anything unmapped, compile it to a separate AGENTS.glp file, and verify the result.
```

## Claude Code

Register this repository as a plugin marketplace:

```text
/plugin marketplace add francescogabrieli/glyph
```

Then install the plugin:

```text
/plugin install glyph@glyph-marketplace
```

After installation, ask Claude Code:

```text
Use the Glyph skill to audit CLAUDE.md before compiling it. Keep the source untouched and explain anything preserved or unmapped.
```

## Glyph executable

The skill does not install software silently. Until Glyph is published on PyPI, it points users to the immutable release install:

```bash
python -m pip install "glyph-instructions @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
```

The skill should be updated to prefer `uvx glyph-instructions` after PyPI publication.