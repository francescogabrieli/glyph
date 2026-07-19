# Agent Maintainer Proposal

## Problem

Coding-agent instructions are usually stored as long Markdown files.

That makes them:

- expensive to load repeatedly
- hard to diff semantically
- hard to lint for safety gaps
- hard to select deterministically for a specific task

## Proposal

Support Glyph `.glp` as a compact instruction manifest format, either directly or through a lightweight adapter.

## Why `.glp`

- compact operational semantics
- deterministic parsing and rendering
- explicit `must` / `deny` / `ask` safety structure
- task-aware selection without LLM calls
- CI-checkable drift between Markdown and structured instructions
- Markdown fallback for current workflows

## Integration Levels

### Level 1: Compatibility fallback

Continue consuming Markdown generated from `.glp`.

### Level 2: Tool-assisted support

Call Glyph through CLI or MCP for:

- parse
- inspect
- select
- render
- check

### Level 3: Native support

Read `.glp` directly and treat:

- `flow[]` as execution-order guidance
- `must[]` as required behavior
- `deny[]` as prohibited behavior
- `ask[]` as confirmation-gated behavior
- `cmd.*` as recommended commands

## Minimal Implementation

1. Parse `.glp` v0.1.
2. Preserve safety-critical `deny[]` and `ask[]` rules during task selection.
3. Render an internal instruction block for the model.
4. Warn on unknown custom semantics.

## Security Considerations

- do not silently discard safety-critical rules
- treat destructive and production-affecting rules conservatively
- warn or fail closed on unknown high-severity semantics
- keep a clear distinction between advisory workflow steps and hard prohibitions

## Compatibility Fallback

Native support is not required for adoption.

Projects can keep `.glp` as source of truth and emit:

- `AGENTS.md`
- `CLAUDE.md`
- Copilot instructions
- Cursor rules

## Open Questions

- should native runtimes expose `.glp` parsing directly or through adapters
- how should unknown custom rules be surfaced in UI or logs
- what selection policy should always preserve safety-critical semantics
- how should agents report rule adherence back to users or CI
