# Native Agent Support

Glyph is positioned as a compact, deterministic, machine-readable instruction format for coding agents, with Markdown compatibility.

That matters because native support is not required for Glyph to be useful now, but native support is the long-term adoption target.

## Adoption Path

```txt
Today:
  Markdown instructions -> Glyph compile -> .glp -> render/emit/select/check -> Markdown-compatible agent output

Near future:
  Agents call Glyph through CLI or MCP to inspect/select task-relevant instructions

Long term:
  Coding agents support .glp natively or through lightweight adapters
```

## Integration Levels

### Level 1: Compatibility mode

Agents continue reading Markdown.

Glyph emits:

- `AGENTS.md`
- `CLAUDE.md`
- `.github/copilot-instructions.md`
- Cursor rules

This is the lowest-risk adoption path because teams can use `.glp` as source of truth without waiting for runtime changes.

### Level 2: Tool-assisted mode

Agents call Glyph through CLI or MCP to inspect, select, lint, diff, or render instructions on demand.

Examples:

- compile repository instructions into `.glp`
- select task-relevant instructions before a task starts
- check instruction drift in CI
- inspect unresolved operational candidates

This mode keeps the runtime unchanged while giving the agent structured access to instruction semantics.

### Level 3: Native `.glp` mode

Agents read `.glp` directly and interpret:

- `flow[]`
- `must[]`
- `deny[]`
- `ask[]`
- `cmd.*`
- `stack[]`
- `scope[]`

Expected behavior in native mode:

- `flow[]` influences execution order
- `must[]` are required behaviors
- `deny[]` are prohibited behaviors
- `ask[]` require confirmation before proceeding
- `cmd.*` exposes recommended repository commands
- safety-critical rules should always be loaded
- task selection may reduce context but must preserve safety rules
- unknown semantics should fail closed or be ignored with warning depending on severity

## Minimal Pseudo-Interface

```txt
load_glp(path) -> InstructionManifest
select_for_task(manifest, task) -> InstructionManifest
render_for_model(manifest) -> MarkdownInstructionBlock
```

This is intentionally small. A runtime can start with parse, select, and render behavior before adding any deeper enforcement.

## Native Mode Notes

Native `.glp` support does not require a hosted service.

A runtime can implement support by:

- parsing the file directly
- embedding a lightweight adapter
- shelling out to the Glyph CLI
- calling a local MCP server

The right path depends on the agent architecture and trust boundary.

## Safety Expectations

Native or tool-assisted consumers should treat the following as durable safety semantics:

- secrets and credential handling
- production configuration restrictions
- destructive-operation approval
- schema or migration approval
- deployment approval

Safety-critical rules should not be dropped just because a task-focused selector narrows context.

## Why Agent Maintainers Might Care

- lower instruction-token cost
- machine-readable safety semantics
- deterministic task-aware selection
- CI-checkable instruction drift
- easier instruction diffing
- compatible Markdown fallback

## Non-Claims

Glyph does not claim that any current coding agent supports `.glp` natively today unless that support is explicitly documented by the agent maintainer.

At the time of writing, Glyph should be treated as a compatibility-first format with a credible path toward native support, not as a format already adopted by major runtimes.
