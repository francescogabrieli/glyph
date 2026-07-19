# Compatibility

Glyph is designed for progressive adoption.

Repositories can keep `.glp` as a source-controlled semantic source of truth and emit Markdown fallbacks for tools that do not yet support `.glp` natively.

Supported targets:

```txt
agents-md
claude-md
copilot
cursor
generic-md
```

Example:

```bash
glyph emit AGENTS.glp --target agents-md -o AGENTS.md
glyph emit AGENTS.glp --target cursor -o .cursor/rules/glyph.mdc
```

Generated Markdown preserves encoded operational semantics, not the original prose.

Glyph continues to parse and render `glyph/0.1` deterministically. A 0.1
manifest can be upgraded to the shared 0.2 semantic view without rewriting its
legacy fields. Structured expressions, `allow`, and linked policies are
0.2-only and cannot be rendered as 0.1 when doing so would lose meaning.

Markdown emitters render linked policies as one inseparable directive so an
allow/deny pair cannot appear to be two unrelated recommendations.

When custom rules are used with `--rules`, render and emit commands can use the custom rendered sentence for custom semantic IDs.
