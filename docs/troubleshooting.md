# Troubleshooting

## `glyph` is not found

Install the package into the active Python environment, then check it:

```bash
pip install "glyph-instructions @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
glyph version
glyph doctor
```

For a clone of this repository, use `pip install -e ".[dev]"`.

## Compilation preserves more than expected

This is normally intentional. Inspect the candidates first:

```bash
glyph inspect AGENTS.md --show-unmapped
```

Check whether the wording is ambiguous, narrative, repository-specific, or
depends on an unresolved condition or pronoun. Clarify the source instruction
or add a reviewed custom rule only when the meaning is truly stable.

## Strict mode fails

Read the exact failing metric. Do not immediately lower it.

- Low structured coverage: inspect preservation and identify safe generic or
  repository-owned mappings.
- High-risk preserved: clarify source wording or add an exact custom policy.
- Conflict: resolve incompatible source directives or categories.
- Reduction: use a threshold appropriate to the file size and profile.

## `glyph check` says the manifest is stale

Regenerate the manifest from its source, review the semantic diff, then update
the lockfile if the change is intended:

```bash
glyph compile AGENTS.md -o AGENTS.glp
glyph diff previous.AGENTS.glp AGENTS.glp
glyph lock AGENTS.md -o glyph.lock.json
```

## A custom rule does not match

Confirm the `--rules` path or project configuration, then use `inspect` to see
the candidate text and section. Exact policies are case- and punctuation-
sensitive after only NFC, outer-trim, and whitespace normalization.

## A v0.2 manifest will not render as v0.1

That failure protects meaning. A structured expression, different subject,
condition, exception, `allow`, or inseparable link cannot be flattened without
semantic loss. Keep it as v0.2 or emit Markdown compatibility output instead.

## MCP is unavailable

Install the optional extra in the same environment that runs `glyph`:

```bash
pip install "glyph-instructions[mcp] @ git+https://github.com/francescogabrieli/glyph.git@v0.2.0"
glyph mcp --help
```

See [MCP server](mcp.md) for local configuration.
